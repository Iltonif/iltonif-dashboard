
"""
Tests del motor de decision. Guardar como test_decision_engine.py junto a
decision_engine.py y correr con: pytest test_decision_engine.py -v
 
Por que estos casos: cada uno corresponde a una frontera de umbral que,
si alguien cambia un numero por error (7 -> 8, 0.10 -> 0.01, etc.), debe
hacer fallar un test. Es la proteccion mas barata contra bugs de negocio
silenciosos que existe para este proyecto.
"""
 
import pytest
from decision_engine import evaluar_sku, clasificar_cobertura
 
 
def fila_base(**overrides):
    base = dict(
        precio_venta=100.0,
        coste_unitario=60.0,
        precio_comp_min=100.0,
        precio_comp_avg=100.0,
        stock_disponible=100,
        ventas_media_7d=10.0,
        ventas_media_30d=10.0,
        alerta_bajada_competidor=0,
    )
    base.update(overrides)
    return base
 
 
# ── Fronteras de cobertura de stock (sin tendencia de demanda) ──
 
def test_cobertura_justo_debajo_de_critico():
    assert clasificar_cobertura(6.9) == "CRITICO"
 
def test_cobertura_justo_en_critico_no_cuenta_como_critico():
    # cobertura == 7 no es "< 7", así que cae en REPOSICION
    assert clasificar_cobertura(7.0) == "REPOSICION"
 
def test_cobertura_justo_debajo_de_reposicion():
    assert clasificar_cobertura(14.9) == "REPOSICION"
 
def test_cobertura_en_15_es_ok():
    assert clasificar_cobertura(15.0) == "OK"
 
def test_cobertura_en_45_es_ok():
    assert clasificar_cobertura(45.0) == "OK"
 
def test_cobertura_justo_encima_de_exceso_sin_medias_es_exceso():
    # sin media_7d/media_30d, se usa la regla simple (mas conservadora)
    assert clasificar_cobertura(45.1) == "EXCESO"
 
 
# ── Regla v3: EXCESO depende también de la tendencia de demanda ──
 
def test_exceso_confirmado_cuando_demanda_no_sube():
    # cobertura alta y la media semanal no supera la mensual -> EXCESO
    assert clasificar_cobertura(50, media_7d=8, media_30d=10) == "EXCESO"
 
def test_no_es_exceso_si_demanda_semanal_ya_supera_la_mensual():
    # cobertura alta pero la demanda de la última semana está repuntando
    # -> no se marca EXCESO, porque probablemente se consuma pronto
    assert clasificar_cobertura(50, media_7d=12, media_30d=10) == "OK"
 
def test_exceso_con_medias_iguales_cuenta_como_exceso():
    assert clasificar_cobertura(50, media_7d=10, media_30d=10) == "EXCESO"
 
def test_evaluar_sku_sin_media_30d_usa_fallback_conservador():
    # si el dataset no trae ventas_media_30d, se asume demanda estable
    # y por tanto EXCESO se activa igual que en la regla simple
    row = fila_base(stock_disponible=500, ventas_media_7d=10)
    del row["ventas_media_30d"]
    r = evaluar_sku(row)
    assert r["senal_stock"] == "EXCESO"
 
def test_evaluar_sku_no_marca_exceso_si_demanda_semanal_sube():
    row = fila_base(stock_disponible=500, ventas_media_7d=15, ventas_media_30d=10)
    r = evaluar_sku(row)
    assert r["senal_stock"] == "OK"
 
 
# ── evaluar_sku: stock ───────────────────────────────────────
 
def test_sku_critico_genera_impacto_stock_positivo():
    row = fila_base(stock_disponible=20, ventas_media_7d=10)  # cobertura=2
    r = evaluar_sku(row)
    assert r["senal_stock"] == "CRITICO"
    assert r["impacto_stock"] > 0
 
def test_sku_stock_ok_no_genera_impacto():
    row = fila_base(stock_disponible=250, ventas_media_7d=10)  # cobertura=25
    r = evaluar_sku(row)
    assert r["senal_stock"] == "OK"
    assert r["impacto_stock"] == 0
 
def test_ventas_media_7d_cero_no_rompe_division():
    row = fila_base(stock_disponible=50, ventas_media_7d=0)
    r = evaluar_sku(row)  # no debe lanzar ZeroDivisionError
    assert r["cobertura_dias"] > 0
 
 
# ── evaluar_sku: pricing ──────────────────────────────────────
 
def test_precio_alto_respeta_margen_minimo():
    # precio muy por encima del competidor, coste alto -> el precio
    # recomendado no debe caer por debajo de coste/(1-0.20)
    row = fila_base(precio_venta=200, coste_unitario=150,
                     precio_comp_min=100, precio_comp_avg=110)
    r = evaluar_sku(row)
    assert r["senal_pricing"] == "PRECIO ALTO"
    precio_min_viable = 150 / 0.80
    assert r["precio_rec"] >= round(precio_min_viable, 2) - 0.01
 
def test_precio_bajo_vs_competencia_sugiere_subir():
    row = fila_base(precio_venta=80, precio_comp_min=95, precio_comp_avg=100)
    r = evaluar_sku(row)
    assert r["senal_pricing"] == "SUBIR PRECIO"
    assert r["precio_rec"] > 80
 
def test_alerta_bajada_competidor_sin_otras_condiciones():
    row = fila_base(precio_venta=100, precio_comp_min=100, precio_comp_avg=100,
                     alerta_bajada_competidor=1)
    r = evaluar_sku(row)
    assert r["senal_pricing"] == "ALERTA COMP."
 
def test_precio_competitivo_sin_alertas():
    row = fila_base()
    r = evaluar_sku(row)
    assert r["senal_pricing"] == "OK"
    assert r["impacto_pricing"] == 0
 
 
# ── impacto total ──────────────────────────────────────────
 
def test_impacto_total_es_suma_de_stock_y_pricing():
    row = fila_base(stock_disponible=20, ventas_media_7d=10,
                     precio_venta=200, coste_unitario=150,
                     precio_comp_min=100, precio_comp_avg=110)
    r = evaluar_sku(row)
    assert r["impacto_total"] == r["impacto_stock"] + r["impacto_pricing"]
