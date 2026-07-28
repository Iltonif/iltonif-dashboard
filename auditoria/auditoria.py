# -*- coding: utf-8 -*-
"""
Auditoría gratuita ILTONIF — genera el informe PDF a partir de los CSVs
de un prospecto.

Uso:
    python3 auditoria.py --ventas ventas.csv --stock stock.csv --tienda "Nombre Tienda"

Formato esperado (nombres de columna flexibles, ver MAPEOS):
  ventas.csv : una fila por venta/día → fecha, sku, unidades
  stock.csv  : una fila por SKU → sku, nombre, stock, precio [, coste]

Si el prospecto tiene coste: el capital atrapado se calcula con coste real.
Si no: se estima coste = 60% del precio (supuesto declarado en el informe).

El análisis de precios frente a competencia NO va en la auditoría (requiere
la integración de Google Shopping, disponible en el piloto) — el informe lo
dice explícitamente como parte de la propuesta de valor del piloto.
"""
import argparse
import sys
import unicodedata
from datetime import timedelta
from pathlib import Path

import pandas as pd

# decision_engine puede vivir en la raíz del repo o en scripts/ (según versión
# del layout). Se añaden ambas rutas para que la auditoría funcione en los dos.
_RAIZ = Path(__file__).resolve().parent.parent
for _ruta in (_RAIZ, _RAIZ / "scripts"):
    if (_ruta / "decision_engine.py").exists():
        sys.path.insert(0, str(_ruta))
        break
from decision_engine import clasificar_cobertura, UMBRAL_EXCESO  # noqa: E402

# ── Mapeo flexible de nombres de columna (Shopify ES/EN, genéricos) ──
MAPEOS = {
    "fecha":    ["fecha", "date", "day", "created_at", "dia", "fecha_pedido", "order_date"],
    "sku":      ["sku", "sku_id", "referencia", "ref", "variant_sku", "codigo", "ean", "product_id"],
    "unidades": ["unidades", "units", "cantidad", "qty", "quantity", "net_quantity", "uds", "ventas"],
    "nombre":   ["nombre", "name", "producto", "product", "title", "product_title", "descripcion"],
    "stock":    ["stock", "inventario", "inventory", "existencias", "available", "inventory_quantity", "stock_disponible"],
    "precio":   ["precio", "price", "pvp", "precio_venta", "variant_price", "importe_unitario"],
    "coste":    ["coste", "cost", "costo", "coste_unitario", "cost_per_item", "coste_unidad"],
}

def _normalizar(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.strip().lower().replace(" ", "_")

def mapear_columnas(df: pd.DataFrame, requeridas: list[str], opcionales: list[str] = ()) -> pd.DataFrame:
    cols = {_normalizar(c): c for c in df.columns}
    out = {}
    for destino in list(requeridas) + list(opcionales):
        for candidato in MAPEOS[destino]:
            if candidato in cols:
                out[destino] = cols[candidato]
                break
    faltan = [r for r in requeridas if r not in out]
    if faltan:
        raise SystemExit(
            f"ERROR: no encuentro columnas para {faltan}.\n"
            f"Columnas del archivo: {list(df.columns)}\n"
            f"Nombres aceptados: " + "; ".join(f"{k}: {v}" for k, v in MAPEOS.items() if k in faltan)
        )
    return df.rename(columns={v: k for k, v in out.items()})[list(out.keys())]


def parsear_fechas(serie: pd.Series) -> pd.Series:
    """Detecta el formato antes de parsear. Nunca aplicar dayfirst a fechas
    ISO (YYYY-MM-DD): pandas intercambia mes y día cuando ambos son <=12 y
    corrompe los cálculos en silencio."""
    muestra = serie.astype(str).str.strip().head(50)
    es_iso = muestra.str.match(r"^\d{4}-\d{1,2}-\d{1,2}").mean() > 0.8
    return pd.to_datetime(serie, errors="coerce", dayfirst=not es_iso)


def analizar(ventas: pd.DataFrame, stock: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    ventas = ventas.copy()
    ventas["fecha"] = parsear_fechas(ventas["fecha"])
    ventas = ventas.dropna(subset=["fecha"])
    ventas["unidades"] = pd.to_numeric(ventas["unidades"], errors="coerce").fillna(0)
    ventas["sku"] = ventas["sku"].astype(str).str.strip()
    fin, inicio = ventas["fecha"].max(), ventas["fecha"].min()
    dias_datos = max((fin - inicio).days + 1, 1)
    d7, d30 = min(7, dias_datos), min(30, dias_datos)
    v7 = ventas[ventas["fecha"] > fin - timedelta(days=d7)].groupby("sku")["unidades"].sum() / d7
    v30 = ventas[ventas["fecha"] > fin - timedelta(days=d30)].groupby("sku")["unidades"].sum() / d30

    df = stock.copy()
    df["sku"] = df["sku"].astype(str).str.strip()
    df["stock"] = pd.to_numeric(df["stock"], errors="coerce").fillna(0)
    df["precio"] = pd.to_numeric(df["precio"], errors="coerce").fillna(0)
    hay_coste = "coste" in df.columns and pd.to_numeric(df["coste"], errors="coerce").notna().any()
    if hay_coste:
        df["coste"] = pd.to_numeric(df["coste"], errors="coerce").fillna(df["precio"] * 0.6)
    else:
        df["coste"] = df["precio"] * 0.6

    df["media_7d"] = df["sku"].map(v7).fillna(0.0)
    df["media_30d"] = df["sku"].map(v30).fillna(0.0)
    df["cobertura"] = df.apply(
        lambda r: r["stock"] / max(r["media_7d"], 0.05), axis=1)
    df["senal"] = df.apply(
        lambda r: clasificar_cobertura(r["cobertura"], r["media_7d"], r["media_30d"])
        if r["media_7d"] > 0 or r["stock"] > 0 else "OK", axis=1)
    # SKUs con stock pero cero ventas en 30 días → capital dormido (caso especial de EXCESO)
    df.loc[(df["stock"] > 0) & (df["media_30d"] == 0), "senal"] = "SIN VENTAS"

    # € atrapado: stock por encima de UMBRAL_EXCESO días de cobertura, a coste
    def atrapado(r):
        if r["senal"] == "SIN VENTAS":
            return r["stock"] * r["coste"]
        if r["senal"] == "EXCESO":
            exceso_uds = r["stock"] - UMBRAL_EXCESO * r["media_7d"]
            return max(exceso_uds, 0) * r["coste"]
        return 0.0
    df["eur_atrapado"] = df.apply(atrapado, axis=1).round(0)

    # € en riesgo por rotura: ventas diarias × precio × 14 días (hueco típico de reposición)
    df["eur_riesgo"] = df.apply(
        lambda r: r["media_7d"] * r["precio"] * 14 if r["senal"] == "CRITICO"
        else (r["media_7d"] * r["precio"] * 7 if r["senal"] == "REPOSICION" else 0), axis=1).round(0)

    resumen = {
        "n_skus": len(df),
        "valor_stock": float((df["stock"] * df["coste"]).sum()),
        "eur_atrapado": float(df["eur_atrapado"].sum()),
        "eur_riesgo": float(df["eur_riesgo"].sum()),
        "n_criticos": int((df["senal"] == "CRITICO").sum()),
        "n_reposicion": int((df["senal"] == "REPOSICION").sum()),
        "n_exceso": int(df["senal"].isin(["EXCESO", "SIN VENTAS"]).sum()),
        "hay_coste_real": bool(hay_coste),
        "fecha_fin_datos": fin.strftime("%d/%m/%Y"),
    }
    return df, resumen


# ── PDF ──────────────────────────────────────────────────────────
def generar_pdf(df, res, tienda: str, salida: str):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, white
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    FONDO = HexColor("#05070f"); AZUL = HexColor("#4d9aff"); CIAN = HexColor("#22d3ee")
    BLANCO = HexColor("#f8fafc"); GRIS = HexColor("#94a3b8"); GRIS_O = HexColor("#64748b")
    VERDE = HexColor("#4ade80"); AMBAR = HexColor("#fb923c"); ROJO = HexColor("#f43f5e")
    PANEL = HexColor("#0d1526"); TINTA = HexColor("#0f172a")
    LOGO = Path(__file__).resolve().parent.parent / "branding" / "logo_fondo_oscuro.png"

    W, H = A4
    c = canvas.Canvas(salida, pagesize=A4)

    def eur(x): return f"{x:,.0f} €".replace(",", ".")

    # ── Portada oscura ──
    c.setFillColor(FONDO); c.rect(0, 0, W, H, fill=1, stroke=0)
    if LOGO.exists():
        c.drawImage(ImageReader(str(LOGO)), 18*mm, H-40*mm, width=80*mm, height=20*mm, mask="auto")
    c.setFillColor(BLANCO); c.setFont("Helvetica-Bold", 26)
    c.drawString(18*mm, H-105*mm, "Auditoría de stock y rotación")
    c.setFillColor(CIAN); c.setFont("Helvetica-Bold", 17)
    c.drawString(18*mm, H-116*mm, tienda)
    c.setFillColor(GRIS); c.setFont("Helvetica", 10.5)
    c.drawString(18*mm, H-128*mm, f"Datos analizados hasta {res['fecha_fin_datos']} · {res['n_skus']} referencias")
    # 3 cifras grandes
    cifras = [(eur(res["eur_atrapado"]), "capital atrapado en stock", AMBAR),
              (eur(res["eur_riesgo"]), "ventas en riesgo por rotura", ROJO),
              (str(res["n_criticos"] + res["n_reposicion"]), "referencias que reponer ya", CIAN)]
    y = H-165*mm
    for i, (v, lab, col) in enumerate(cifras):
        x = 18*mm + i*60*mm
        c.setFillColor(PANEL); c.roundRect(x, y-16*mm, 56*mm, 30*mm, 3*mm, fill=1, stroke=0)
        c.setFillColor(col); c.setFont("Helvetica-Bold", 17)
        c.drawString(x+5*mm, y+2*mm, v)
        c.setFillColor(GRIS); c.setFont("Helvetica", 8.5)
        c.drawString(x+5*mm, y-5*mm, lab)
    c.setFillColor(GRIS_O); c.setFont("Helvetica", 8.5)
    c.drawString(18*mm, 20*mm, "Informe gratuito · ILTONIF — Inventory & Pricing Intelligence · confidencial, solo para el destinatario")
    c.showPage()

    # ── Página 2: detalle (fondo claro) ──
    def cabecera(titulo):
        c.setFillColor(TINTA); c.setFont("Helvetica-Bold", 15)
        c.drawString(18*mm, H-25*mm, titulo)
        c.setFillColor(GRIS_O); c.setFont("Helvetica", 8)
        c.drawRightString(W-18*mm, H-25*mm, f"ILTONIF · Auditoría — {tienda}")
        c.setStrokeColor(HexColor("#e2e8f0")); c.line(18*mm, H-28*mm, W-18*mm, H-28*mm)

    def tabla(y0, titulo, filas, columnas, anchos, color_titulo):
        c.setFillColor(color_titulo); c.setFont("Helvetica-Bold", 11.5)
        c.drawString(18*mm, y0, titulo)
        y = y0 - 7*mm
        c.setFillColor(GRIS_O); c.setFont("Helvetica-Bold", 8)
        x = 18*mm
        for col, w in zip(columnas, anchos):
            c.drawString(x, y, col); x += w
        y -= 2*mm
        c.setStrokeColor(HexColor("#e2e8f0")); c.line(18*mm, y, W-18*mm, y)
        y -= 5*mm
        c.setFont("Helvetica", 8.5)
        for fila in filas:
            x = 18*mm
            c.setFillColor(TINTA)
            for val, w in zip(fila, anchos):
                c.drawString(x, y, str(val)[:int(w/1.6)]); x += w
            y -= 5.5*mm
        return y - 6*mm

    cabecera("Dónde está tu dinero parado")
    top_exceso = df[df["eur_atrapado"] > 0].nlargest(10, "eur_atrapado")
    filas_e = [(r["nombre"][:38], r["sku"][:14], int(r["stock"]),
                ("sin ventas 30d" if r["senal"] == "SIN VENTAS" else f"{r['cobertura']:.0f} d cobertura"),
                eur(r["eur_atrapado"])) for _, r in top_exceso.iterrows()]
    y = tabla(H-40*mm, f"Top {len(filas_e)} referencias con capital atrapado — {eur(res['eur_atrapado'])} en total",
              filas_e, ["Producto", "SKU", "Stock", "Situación", "€ atrapado"],
              [72*mm, 30*mm, 15*mm, 32*mm, 25*mm], AMBAR)

    top_riesgo = df[df["eur_riesgo"] > 0].nlargest(10, "eur_riesgo")
    filas_r = [(r["nombre"][:38], r["sku"][:14], int(r["stock"]),
                f"{r['cobertura']:.0f} días y bajando", eur(r["eur_riesgo"]))
               for _, r in top_riesgo.iterrows()]
    y = tabla(y, f"Top {len(filas_r)} referencias a punto de romper stock — {eur(res['eur_riesgo'])} de venta en riesgo",
              filas_r, ["Producto", "SKU", "Stock", "Cobertura", "€ en riesgo"],
              [72*mm, 30*mm, 15*mm, 32*mm, 25*mm], ROJO)
    c.showPage()

    # ── Página 3: metodología + siguiente paso ──
    cabecera("Cómo se ha calculado (y qué falta)")
    c.setFillColor(TINTA); c.setFont("Helvetica", 10)
    metodo = [
        f"• Ventas: media diaria de los últimos 7 y 30 días por referencia (datos hasta {res['fecha_fin_datos']}).",
        "• Cobertura: stock actual ÷ venta media diaria. Umbrales: crítico <7 días, reposición <15, exceso >45.",
        "• Un exceso solo se marca si la demanda reciente no está subiendo (si crece, ese stock se consumirá).",
        "• Capital atrapado: unidades por encima de 45 días de cobertura, valoradas a coste"
        + (" real (tu CSV)." if res["hay_coste_real"] else " estimado (60% del PVP — ajustable con tus costes reales)."),
        "• Ventas en riesgo: venta diaria × precio × hueco típico de reposición (14 días si crítico, 7 si urgente).",
        "",
        "Lo que esta auditoría NO incluye (y el piloto sí):",
        "• Comparativa de tus precios frente a Tiendanimal, Kiwoko y Zooplus, referencia a referencia.",
        "• Recomendaciones diarias actualizadas con cada venta, no una foto estática.",
        "• Seguimiento de qué acciones aplicas y cuánto ahorro generan, medido.",
    ]
    y = H-40*mm
    for l in metodo:
        c.drawString(18*mm, y, l); y -= 6.5*mm

    c.setFillColor(PANEL); c.roundRect(18*mm, y-38*mm, W-36*mm, 34*mm, 3*mm, fill=1, stroke=0)
    c.setFillColor(VERDE); c.setFont("Helvetica-Bold", 12)
    c.drawString(24*mm, y-9*mm, "Siguiente paso: piloto gratuito de 30 días")
    c.setFillColor(BLANCO); c.setFont("Helvetica", 9.5)
    c.drawString(24*mm, y-17*mm, "Este informe con tus datos, vivo y actualizado cada mañana, con la comparativa de precios incluida.")
    c.drawString(24*mm, y-23*mm, "Si en 30 días el ahorro identificado no supera 3 veces la suscripción, no seguimos. Sin permanencia.")
    c.setFillColor(CIAN); c.setFont("Helvetica-Bold", 9.5)
    c.drawString(24*mm, y-31*mm, "Responde a este email y lo arrancamos esta semana. — Pedro Gómez · ILTONIF")
    c.save()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Auditoría gratuita ILTONIF")
    ap.add_argument("--ventas", required=True)
    ap.add_argument("--stock", required=True)
    ap.add_argument("--tienda", required=True)
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()

    ventas = mapear_columnas(pd.read_csv(a.ventas), ["fecha", "sku", "unidades"])
    stock = mapear_columnas(pd.read_csv(a.stock), ["sku", "nombre", "stock", "precio"], ["coste"])
    df, res = analizar(ventas, stock)
    salida = a.salida or f"AUDITORIA_{a.tienda.replace(' ', '_')}.pdf"
    generar_pdf(df, res, a.tienda, salida)
    print(f"Informe generado: {salida}")
    print(f"  Capital atrapado: {res['eur_atrapado']:,.0f} € | En riesgo: {res['eur_riesgo']:,.0f} € "
          f"| Críticos: {res['n_criticos']} | Exceso: {res['n_exceso']}")
