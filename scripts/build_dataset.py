"""
Pipeline de generación del dataset modelable de ILTONIF.

Cada ejecución añade UN día nuevo por SKU al histórico
(data/iltonif_dataset_modelable_v3.csv), calculando las 47 columnas
(features de calendario, lags, medias móviles y alertas) a partir de:

  1. Shopify Admin API  → ventas de ayer, stock y precios propios.
     Requiere variables de entorno SHOPIFY_STORE (xxx.myshopify.com)
     y SHOPIFY_TOKEN (Admin API access token).
  2. Precios de competencia → data/competitor_prices.csv si existe
     (columnas: sku_id, precio_decathlon, precio_trailzone,
     precio_outdoorpro). Si no, se arrastran los últimos conocidos.
     Aquí se enchufará en el futuro una API de precios de Amazon
     (Keepa, Rainforest o SP-API).

Modo demo (sin credenciales de Shopify): --demo simula el día nuevo a
partir del histórico (demanda ~ media 7d, stock decrementado), para
poder probar el pipeline de punta a punta antes de conectar la tienda.

Uso:  python scripts/build_dataset.py [--demo] [--fecha YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
CSV = REPO / "data" / "iltonif_dataset_modelable_v3.csv"
COMPETITORS_CSV = REPO / "data" / "competitor_prices.csv"

FESTIVOS_ES = {  # festivos nacionales fijos (aprox.)
    (1, 1), (1, 6), (5, 1), (8, 15), (10, 12), (11, 1), (12, 6), (12, 8), (12, 25),
}


# ── Fuentes ────────────────────────────────────────────────────

def snapshot_shopify(fecha: date) -> pd.DataFrame:
    """Ventas de `fecha`, stock y precios actuales desde Shopify.

    Devuelve DataFrame con: sku_id, unidades_vendidas, precio_venta,
    pvp_base, coste_unitario, stock_disponible, promocion_activa,
    descuento_pct. Un SKU por fila.
    """
    import requests

    store = os.environ["SHOPIFY_STORE"]
    token = os.environ["SHOPIFY_TOKEN"]
    base = f"https://{store}/admin/api/2024-10"
    hdr = {"X-Shopify-Access-Token": token}

    # Productos y variantes (precio, compare_at_price, sku, inventario)
    productos = []
    url = f"{base}/products.json?limit=250"
    while url:
        r = requests.get(url, headers=hdr, timeout=30)
        r.raise_for_status()
        productos += r.json()["products"]
        url = r.links.get("next", {}).get("url")

    filas = {}
    inv_item_ids = {}
    for p in productos:
        for v in p["variants"]:
            sku = v.get("sku") or f"shopify-{v['id']}"
            pvp_base = float(v.get("compare_at_price") or v["price"])
            precio = float(v["price"])
            filas[sku] = {
                "sku_id": sku,
                "precio_venta": precio,
                "pvp_base": pvp_base,
                "stock_disponible": int(v.get("inventory_quantity") or 0),
                "promocion_activa": int(precio < pvp_base),
                "descuento_pct": round(1 - precio / pvp_base, 4) if pvp_base else 0.0,
                "coste_unitario": np.nan,  # se rellena con inventory_items
                "unidades_vendidas": 0,
            }
            inv_item_ids[v["inventory_item_id"]] = sku

    # Coste unitario (inventory items, en lotes de 100)
    import itertools
    ids = list(inv_item_ids)
    for lote in (ids[i:i + 100] for i in range(0, len(ids), 100)):
        r = requests.get(f"{base}/inventory_items.json",
                         params={"ids": ",".join(map(str, lote)), "limit": 100},
                         headers=hdr, timeout=30)
        r.raise_for_status()
        for item in r.json()["inventory_items"]:
            sku = inv_item_ids[item["id"]]
            filas[sku]["coste_unitario"] = float(item.get("cost") or 0)

    # Ventas del día `fecha` (pedidos pagados)
    ini = f"{fecha}T00:00:00Z"
    fin = f"{fecha + timedelta(days=1)}T00:00:00Z"
    url = (f"{base}/orders.json?status=any&financial_status=paid"
           f"&created_at_min={ini}&created_at_max={fin}&limit=250")
    while url:
        r = requests.get(url, headers=hdr, timeout=30)
        r.raise_for_status()
        for o in r.json()["orders"]:
            for li in o["line_items"]:
                sku = li.get("sku")
                if sku in filas:
                    filas[sku]["unidades_vendidas"] += li["quantity"]
        url = r.links.get("next", {}).get("url")

    return pd.DataFrame(filas.values())


def snapshot_demo(hist: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Simula el día nuevo a partir del último estado del histórico."""
    ultimo = hist.sort_values("fecha").groupby("sku_id").last().reset_index()
    n = len(ultimo)
    demanda = rng.poisson(np.maximum(ultimo["ventas_media_7d"], 0.1))
    return pd.DataFrame({
        "sku_id": ultimo["sku_id"],
        "unidades_vendidas": demanda,
        "precio_venta": ultimo["precio_venta"],
        "pvp_base": ultimo["pvp_base"],
        "coste_unitario": ultimo["coste_unitario"],
        "stock_disponible": np.maximum(ultimo["stock_disponible"] - demanda, 0),
        "promocion_activa": ultimo["promocion_activa"],
        "descuento_pct": ultimo["descuento_pct"],
    })


def precios_competencia(hist: pd.DataFrame, skus: pd.Series) -> pd.DataFrame:
    """Precios de competidores: CSV manual si existe; si no, carry-forward.

    PUNTO DE EXTENSIÓN: sustituir por llamada a Keepa/Rainforest/SP-API
    cuando haya presupuesto para precios de Amazon en tiempo real.
    """
    cols = ["precio_decathlon", "precio_trailzone", "precio_outdoorpro"]
    if COMPETITORS_CSV.exists():
        comp = pd.read_csv(COMPETITORS_CSV)
        comp = comp[["sku_id"] + [c for c in cols if c in comp.columns]]
    else:
        comp = (hist.sort_values("fecha").groupby("sku_id").last()
                .reset_index()[["sku_id"] + cols])
    return pd.DataFrame({"sku_id": skus}).merge(comp, on="sku_id", how="left")


# ── Features ───────────────────────────────────────────────────

def construir_dia(hist: pd.DataFrame, snap: pd.DataFrame, comp: pd.DataFrame,
                  fecha: date) -> pd.DataFrame:
    """Calcula las 47 columnas del día nuevo a partir del histórico."""
    hist = hist.copy()
    hist["fecha"] = pd.to_datetime(hist["fecha"])
    snap = snap.merge(comp, on="sku_id", how="left")

    meta = (hist.sort_values("fecha").groupby("sku_id").last().reset_index()
            [["sku_id", "nombre_producto", "categoria", "plataforma"]])
    snap = snap.merge(meta, on="sku_id", how="left")

    filas = []
    ts = pd.Timestamp(fecha)
    for _, r in snap.iterrows():
        h = hist[hist["sku_id"] == r["sku_id"]].sort_values("fecha")
        ventas_hist = h.set_index("fecha")["unidades_vendidas"]

        def lag(n):
            objetivo = ts - pd.Timedelta(days=n)
            return float(ventas_hist.get(objetivo, 0.0))

        ult7 = ventas_hist[ventas_hist.index > ts - pd.Timedelta(days=7)]
        ult30 = ventas_hist[ventas_hist.index > ts - pd.Timedelta(days=30)]
        hoy = pd.Series([float(r["unidades_vendidas"])])
        media7 = float(pd.concat([ult7.astype(float), hoy]).mean() if len(ult7) else hoy.mean())
        media30 = float(pd.concat([ult30.astype(float), hoy]).mean() if len(ult30) else hoy.mean())

        comp_vals = [r["precio_decathlon"], r["precio_trailzone"], r["precio_outdoorpro"]]
        comp_min, comp_avg, comp_max = (float(np.nanmin(comp_vals)),
                                        float(np.nanmean(comp_vals)),
                                        float(np.nanmax(comp_vals)))
        pvp = float(r["precio_venta"])
        coste = float(r["coste_unitario"] or 0)
        stock = int(r["stock_disponible"])
        cobertura = stock / max(media7, 0.1)

        ayer = h.iloc[-1] if len(h) else None
        hace7 = h[h["fecha"] <= ts - pd.Timedelta(days=7)]
        comp_min_7d = float(hace7.iloc[-1]["precio_comp_min"]) if len(hace7) else comp_min

        filas.append({
            "fecha": fecha.isoformat(), "sku_id": r["sku_id"],
            "nombre_producto": r["nombre_producto"], "categoria": r["categoria"],
            "plataforma": r["plataforma"],
            "unidades_vendidas": int(r["unidades_vendidas"]),
            "pvp_base": round(float(r["pvp_base"]), 2), "precio_venta": round(pvp, 2),
            "coste_unitario": round(coste, 2),
            "margen_bruto": round((pvp - coste) / pvp, 2) if pvp else 0,
            "promocion_activa": int(r["promocion_activa"]),
            "descuento_pct": float(r["descuento_pct"]),
            "precio_decathlon": round(float(r["precio_decathlon"]), 2),
            "precio_trailzone": round(float(r["precio_trailzone"]), 2),
            "precio_outdoorpro": round(float(r["precio_outdoorpro"]), 2),
            "precio_comp_min": round(comp_min, 2), "precio_comp_avg": round(comp_avg, 2),
            "precio_comp_max": round(comp_max, 2),
            "precio_mercado_ref": round((comp_avg + pvp) / 2, 2),
            "stock_disponible": stock,
            "dias_sin_stock": (int(ayer["dias_sin_stock"]) + 1 if (ayer is not None and stock == 0) else 0),
            "dia_semana": ts.dayofweek, "mes": ts.month,
            "semana_anio": int(ts.isocalendar().week),
            "es_festivo": int((ts.month, ts.day) in FESTIVOS_ES),
            "es_blackfriday": int(ts.month == 11 and 23 <= ts.day <= 30),
            "es_navidad": int(ts.month == 12 and ts.day >= 15),
            "ventas_lag_1": lag(1), "ventas_lag_7": lag(7), "ventas_lag_30": lag(30),
            "ventas_media_7d": round(media7, 2), "ventas_media_30d": round(media30, 2),
            "ratio_precio_mercado": round(pvp / comp_avg, 4) if comp_avg else 1.0,
            "diferencia_precio_min": round(pvp - comp_min, 2),
            "dias_cobertura_stock": round(cobertura, 1),
            "ingreso_estimado": round(r["unidades_vendidas"] * pvp, 2),
            "margen_estimado_eur": round(r["unidades_vendidas"] * (pvp - coste), 2),
            "var_precio_decathlon_1d": round(float(r["precio_decathlon"]) - float(ayer["precio_decathlon"]), 2) if ayer is not None else 0.0,
            "var_precio_trailzone_1d": round(float(r["precio_trailzone"]) - float(ayer["precio_trailzone"]), 2) if ayer is not None else 0.0,
            "var_precio_outdoorpro_1d": round(float(r["precio_outdoorpro"]) - float(ayer["precio_outdoorpro"]), 2) if ayer is not None else 0.0,
            "var_precio_comp_min_7d": round(comp_min - comp_min_7d, 2),
            "diferencia_precio_avg": round(pvp - comp_avg, 2),
            "alerta_bajada_competidor": int(comp_min_7d > 0 and (comp_min - comp_min_7d) / comp_min_7d < -0.05),
            "alerta_precio_alto": int(pvp - comp_min > comp_min * 0.10),
            "oportunidad_subida_precio": int(comp_avg > 0 and pvp / comp_avg < 0.92),
            "alerta_stockout_riesgo": int(cobertura < 7),
            "alerta_exceso_stock": int(cobertura > 45 and media7 <= media30),
        })
    return pd.DataFrame(filas)


# ── Main ───────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="simular día sin Shopify")
    ap.add_argument("--fecha", default=None, help="día a ingerir (por defecto: ayer)")
    args = ap.parse_args()

    fecha = (date.fromisoformat(args.fecha) if args.fecha
             else date.today() - timedelta(days=1))

    hist = pd.read_csv(CSV, parse_dates=["fecha"])
    if (hist["fecha"] == pd.Timestamp(fecha)).any():
        print(f"El día {fecha} ya está en el dataset; nada que hacer.")
        return 0

    if args.demo:
        snap = snapshot_demo(hist, np.random.default_rng(int(fecha.strftime('%Y%m%d'))))
        print(f"[demo] día {fecha} simulado para {len(snap)} SKUs")
    else:
        if not (os.environ.get("SHOPIFY_STORE") and os.environ.get("SHOPIFY_TOKEN")):
            print("Faltan SHOPIFY_STORE / SHOPIFY_TOKEN (usa --demo para probar).")
            return 1
        snap = snapshot_shopify(fecha)
        print(f"[shopify] {len(snap)} SKUs, ventas de {fecha}")

    comp = precios_competencia(hist, snap["sku_id"])
    nuevo = construir_dia(hist, snap, comp, fecha)

    out = pd.concat([hist.assign(fecha=hist["fecha"].dt.strftime("%Y-%m-%d")), nuevo],
                    ignore_index=True)[hist.columns]
    out.to_csv(CSV, index=False)
    print(f"OK: {len(nuevo)} filas añadidas → {CSV.name} ({len(out)} filas totales)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
