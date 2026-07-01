"""
Motor de decision de ILTONIF, extraido de dashboard_v3.py (version elegida
como definitiva) para que sea testable sin necesidad de levantar Streamlit.

Version de la regla EXCESO: esta es la variante "v3" — el stock solo se
marca EXCESO si ademas la demanda no esta subiendo (media_7d <= media_30d).
Si la cobertura es alta pero la demanda de la ultima semana ya supera la
media del mes, no se marca EXCESO porque es probable que el stock se
consuma pronto. Esta fue una decision de negocio explicita (v3 sobre
dashboard.py simple), no un cambio de estilo.

Como integrarlo:
1. Guarda este archivo como `decision_engine.py` en la raiz del repo
   (junto al dashboard.py final, promovido desde dashboard_v3.py).
2. Sustituye el cuerpo de `generar_recomendaciones()` por una llamada a
   `evaluar_sku()` por cada fila, y usa `clasificar_cobertura()` en el
   Tab 4 en vez de repetir los umbrales a mano.

Aviso importante sobre el Tab 4 de dashboard_v3.py: hoy el coloreado de
las barras de stock en ese tab usa la regla simple (cobertura > 45 sin
mirar media_30d), mientras que generar_recomendaciones() ya usaba la
regla con media_30d. Es decir, la inconsistencia que buscabamos evitar
ya existia dentro del propio v3, entre dos sitios distintos del mismo
archivo. Usar clasificar_cobertura() en los dos sitios la resuelve.
"""

from __future__ import annotations


UMBRAL_CRITICO = 7
UMBRAL_REPOSICION = 15
UMBRAL_EXCESO = 45

MARGEN_MINIMO = 0.20          # coste / (1 - margen_minimo) = precio piso
UMBRAL_PRECIO_ALTO_PCT = 0.10  # % por encima del competidor minimo
UMBRAL_PRECIO_BAJO_RATIO = 0.92  # ratio precio propio / precio medio competencia


def clasificar_cobertura(cobertura_dias: float, media_7d: float | None = None,
                          media_30d: float | None = None) -> str:
    """Traduce dias de cobertura (+ tendencia de demanda) a una senal.

    `media_7d` y `media_30d` son opcionales para poder seguir llamando a
    esta funcion con solo la cobertura en sitios donde no se tenga la
    media_30d a mano — en ese caso, EXCESO se marca solo por cobertura
    (comportamiento mas conservador, nunca deja pasar un exceso real,
    como mucho lo marca de mas). Cuando esten disponibles ambas medias,
    se aplica la regla completa de v3.
    """
    if cobertura_dias < UMBRAL_CRITICO:
        return "CRITICO"
    if cobertura_dias < UMBRAL_REPOSICION:
        return "REPOSICION"
    if cobertura_dias > UMBRAL_EXCESO:
        if media_7d is not None and media_30d is not None:
            return "EXCESO" if media_7d <= media_30d else "OK"
        return "EXCESO"
    return "OK"


def evaluar_sku(row: dict) -> dict:
    """Aplica el motor de decision de pricing + stock a una fila (un SKU).

    `row` debe tener las claves: precio_venta, coste_unitario,
    precio_comp_min, precio_comp_avg, stock_disponible, ventas_media_7d,
    ventas_media_30d, y opcionalmente alerta_bajada_competidor (0/1).

    Si `ventas_media_30d` no viene en `row`, se asume igual a
    `ventas_media_7d` (equivale a "demanda estable"), lo que activa
    EXCESO igual que la regla simple — es el fallback mas seguro cuando
    falta el dato, en vez de lanzar un error.

    Devuelve un dict con senal_stock, accion_stock, impacto_stock,
    senal_pricing, accion_pricing, precio_rec, impacto_pricing —
    exactamente las mismas claves que generar_recomendaciones() en
    dashboard_v3.py, para que el reemplazo sea directo.
    """
    pvp = row["precio_venta"]
    coste = row["coste_unitario"]
    comp_min = row["precio_comp_min"]
    comp_avg = row["precio_comp_avg"]
    stock = row["stock_disponible"]
    media_7d = max(row["ventas_media_7d"], 0.1)
    media_30d = max(row.get("ventas_media_30d", media_7d), 0.1)
    cobertura = stock / media_7d

    senal_stock = clasificar_cobertura(cobertura, media_7d, media_30d)
    if senal_stock == "CRITICO":
        accion_stock = f"Repón {int(media_7d*30)} uds — rotura en {int(cobertura)} días"
        impacto_stock = round(media_7d * pvp * max(0, UMBRAL_CRITICO - cobertura), 0)
    elif senal_stock == "REPOSICION":
        accion_stock = f"Repón {int(media_7d*30)} uds esta semana"
        impacto_stock = round(media_7d * pvp * 3, 0)
    elif senal_stock == "EXCESO":
        accion_stock = f"{int(cobertura)} días cobertura — considera promoción"
        impacto_stock = 0
    else:
        accion_stock = "Niveles óptimos"
        impacto_stock = 0

    dif = pvp - comp_min
    precio_min_viable = coste / (1 - MARGEN_MINIMO)
    ratio = pvp / comp_avg if comp_avg else 1

    if dif > comp_min * UMBRAL_PRECIO_ALTO_PCT:
        bajada = min((dif / pvp) * 0.6, 0.20)
        precio_rec = max(round(pvp * (1 - bajada), 2), precio_min_viable)
        senal_pricing = "PRECIO ALTO"
        accion_pricing = f"Bajar {bajada*100:.1f}% → {precio_rec:.2f}€"
        impacto_pricing = round(media_7d * bajada * 1.5 * (precio_rec - coste), 0)
    elif ratio < UMBRAL_PRECIO_BAJO_RATIO:
        subida = 0.06
        precio_rec = round(pvp * (1 + subida), 2)
        senal_pricing = "SUBIR PRECIO"
        accion_pricing = f"Subir {subida*100:.0f}% → {precio_rec:.2f}€"
        impacto_pricing = round(media_7d * subida * pvp, 0)
    elif row.get("alerta_bajada_competidor", 0) == 1:
        senal_pricing = "ALERTA COMP."
        accion_pricing = "Competidor bajó >5% esta semana"
        precio_rec = pvp
        impacto_pricing = 0
    else:
        senal_pricing = "OK"
        accion_pricing = "Precio competitivo"
        precio_rec = pvp
        impacto_pricing = 0

    return {
        "senal_stock": senal_stock,
        "accion_stock": accion_stock,
        "impacto_stock": impacto_stock,
        "senal_pricing": senal_pricing,
        "accion_pricing": accion_pricing,
        "precio_rec": precio_rec,
        "impacto_pricing": impacto_pricing,
        "cobertura_dias": round(cobertura, 1),
        "impacto_total": impacto_stock + impacto_pricing,
    }
