# -*- coding: utf-8 -*-
"""
Genera el dataset demo del nicho MASCOTAS (v4) a partir del dataset outdoor v3.

Estrategia: se conservan las dinámicas reales del v3 (ventas, estacionalidad,
lags, alertas) y se remapea la identidad de cada SKU a un producto de tienda
de mascotas con precio objetivo realista. Todas las columnas de precio se
escalan por SKU con factor = pvp_objetivo / pvp_base_original, de modo que
ratios, márgenes relativos y señales del decision_engine se mantienen coherentes.

Competidores: Decathlon/TrailZone/OutdoorPro → Tiendanimal/Kiwoko/Zooplus.
Se añade columna `ean` (sintética, prefijo 84) para reflejar el encaje del ICP.

Uso:  python3 scripts/build_dataset_mascotas_demo.py
Salida: data/iltonif_dataset_modelable_v4_mascotas.csv
"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SRC = BASE / "data" / "iltonif_dataset_modelable_v3.csv"
DST = BASE / "data" / "iltonif_dataset_modelable_v4_mascotas.csv"

# sku_id original → (nombre_producto, categoria, pvp_objetivo, ean)
MAPEO = {
    "SKU-001": ("Royal Canin Medium Adult 15kg", "Pienso perro", 62.99, "8410054001011"),
    "SKU-002": ("Advance Sterilized gato 10kg", "Pienso gato", 44.99, "8410054001028"),
    "SKU-003": ("Acana Prairie Poultry 11,4kg", "Pienso perro", 79.99, "8410054001035"),
    "SKU-004": ("Orijen Original 11,4kg", "Pienso perro", 94.99, "8410054001042"),
    "SKU-005": ("Ultima esterilizados gato 7,5kg", "Pienso gato", 27.99, "8410054001059"),
    "SKU-006": ("Collar Seresto perro grande", "Antiparasitarios", 36.99, "8410054001066"),
    "SKU-007": ("Frontline Tri-Act 6 pipetas M", "Antiparasitarios", 42.99, "8410054001073"),
    "SKU-008": ("Fuente de agua para gatos 2L", "Accesorios", 29.99, "8410054001080"),
    "SKU-009": ("Cama viscoelástica perro XL", "Descanso", 74.99, "8410054001097"),
    "SKU-010": ("Arena aglomerante gato 15kg", "Higiene", 19.99, "8410054001103"),
    "SKU-011": ("Comedero antiglotón mediano", "Accesorios", 15.99, "8410054001110"),
    "SKU-012": ("Transportín rígido IATA M", "Viaje", 59.99, "8410054001127"),
    "SKU-013": ("Kong Classic talla L", "Juguetes", 17.99, "8410054001134"),
    "SKU-014": ("Rascador torre gato 1,5m", "Accesorios", 109.99, "8410054001141"),
    "SKU-015": ("Arnés antitirones talla M", "Paseo", 27.99, "8410054001158"),
    "shopify-42431836586066": ("Natural Greatness pollo 12kg", "Pienso perro", 58.99, "8410054002018"),
    "shopify-42431836618834": ("Ownat Just Grain Free 14kg", "Pienso perro", 64.99, "8410054002025"),
    "shopify-42431836651602": ("Taste of the Wild 12,2kg", "Pienso perro", 71.99, "8410054002032"),
    "shopify-42431836684370": ("Tarjeta regalo 10€", "Tarjetas regalo", 10.00, "8410054009010"),
    "shopify-42431836717138": ("Tarjeta regalo 25€", "Tarjetas regalo", 25.00, "8410054009025"),
    "shopify-42431836749906": ("Tarjeta regalo 50€", "Tarjetas regalo", 50.00, "8410054009050"),
    "shopify-42431836782674": ("Tarjeta regalo 100€", "Tarjetas regalo", 100.00, "8410054009100"),
    "shopify-42431836815442": ("Hill's Science Plan Adult 14kg", "Pienso perro", 76.99, "8410054002049"),
    "shopify-42431836848210": ("Comida húmeda perro pollo — pack 12", "Comida húmeda", 21.99, "8410054002056"),
    "shopify-42431836880978": ("Comida húmeda perro buey — pack 12", "Comida húmeda", 21.99, "8410054002063"),
    "shopify-42431836913746": ("Comida húmeda gato salmón — pack 24", "Comida húmeda", 26.99, "8410054002070"),
    "shopify-42431836946514": ("Comida húmeda gato pollo — pack 24", "Comida húmeda", 26.99, "8410054002087"),
    "shopify-42431836979282": ("Comida húmeda gato atún — pack 24", "Comida húmeda", 26.99, "8410054002094"),
    "shopify-42431837012050": ("Eukanuba Adult Large 15kg", "Pienso perro", 66.99, "8410054002100"),
    "shopify-42431837044818": ("Caseta madera perro XL exterior", "Accesorios", 289.99, "8410054002117"),
    "shopify-42431837077586": ("Purina Pro Plan Medium Adult 14kg", "Pienso perro", 69.99, "8410054002124"),
    "shopify-42431837110354": ("Snacks dentales perro — pack 28", "Snacks", 24.95, "8410054003015"),
    "shopify-42431837143122": ("Snacks naturales gato — pack surtido", "Snacks", 18.95, "8410054003022"),
    "shopify-42431837175890": ("Churu gato — pack degustación", "Snacks", 9.95, "8410054003039"),
    "shopify-42431837208658": ("Pienso hipoalergénico salmón 12kg", "Pienso perro", 67.99, "8410054002131"),
    "shopify-42431837306962": ("Farmina N&D Grain Free 12kg", "Pienso perro", 84.99, "8410054002148"),
    "shopify-42431837405266": ("Advance Medium Adult 14kg", "Pienso perro", 52.99, "8410054002155"),
    "shopify-42431837536338": ("Acana Wild Prairie gato 4,5kg", "Pienso gato", 49.99, "8410054002162"),
    "sku-hosted-1": ("Jaula parque cachorros profesional", "Accesorios", 149.99, "8410054002179"),
    "sku-managed-1": ("Cama ortopédica perro senior L", "Descanso", 89.99, "8410054002186"),
    "sku-untracked-1": ("Bolso transportín gato premium", "Viaje", 64.99, "8410054002193"),
}

# Columnas de precio/€ que escalan con el factor por SKU
COLS_ESCALAR = [
    "pvp_base", "precio_venta", "coste_unitario",
    "precio_decathlon", "precio_trailzone", "precio_outdoorpro",
    "precio_comp_min", "precio_comp_avg", "precio_comp_max", "precio_mercado_ref",
    "diferencia_precio_min", "diferencia_precio_avg",
    "ingreso_estimado", "margen_estimado_eur",
    "var_precio_decathlon_1d", "var_precio_trailzone_1d",
    "var_precio_outdoorpro_1d", "var_precio_comp_min_7d",
]

RENOMBRAR = {
    "precio_decathlon": "precio_tiendanimal",
    "precio_trailzone": "precio_kiwoko",
    "precio_outdoorpro": "precio_zooplus",
    "var_precio_decathlon_1d": "var_precio_tiendanimal_1d",
    "var_precio_trailzone_1d": "var_precio_kiwoko_1d",
    "var_precio_outdoorpro_1d": "var_precio_zooplus_1d",
}


def main():
    df = pd.read_csv(SRC)
    faltan = set(df["sku_id"].unique()) - set(MAPEO)
    if faltan:
        raise SystemExit(f"SKUs sin mapear: {faltan}")

    pvp_orig = df.groupby("sku_id")["pvp_base"].first()
    for sku, (nombre, cat, pvp_obj, ean) in MAPEO.items():
        m = df["sku_id"] == sku
        factor = pvp_obj / pvp_orig[sku]
        df.loc[m, COLS_ESCALAR] = (df.loc[m, COLS_ESCALAR] * factor).round(2)
        df.loc[m, "nombre_producto"] = nombre
        df.loc[m, "categoria"] = cat
        df.loc[m, "ean"] = ean

    df = df.rename(columns=RENOMBRAR)
    df.to_csv(DST, index=False)
    print(f"OK → {DST.name}: {len(df)} filas, {df['sku_id'].nunique()} SKUs, "
          f"{df['categoria'].nunique()} categorías")


if __name__ == "__main__":
    main()
