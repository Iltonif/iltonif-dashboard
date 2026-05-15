import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime, timedelta

st.set_page_config(
    page_title="ILTONIF — Intelligence Platform",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

* { font-family: 'Space Grotesk', sans-serif; }
.main { background: #060912; }
[data-testid="stSidebar"] { background: #0a0e1a !important; border-right: 1px solid rgba(37,99,235,0.15) !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; color: #fff !important; }
[data-testid="stMetricLabel"] { font-size: 0.75rem !important; color: #94a3b8 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; }
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0f172a, #1e293b) !important;
    border: 1px solid rgba(37,99,235,0.2) !important;
    border-radius: 16px !important;
    padding: 20px !important;
    transition: all 0.3s ease !important;
}
[data-testid="stMetric"]:hover { border-color: rgba(37,99,235,0.6) !important; transform: translateY(-2px) !important; }
.stTabs [data-baseweb="tab-list"] { background: #0a0e1a !important; border-radius: 12px !important; padding: 4px !important; gap: 4px !important; border: 1px solid rgba(37,99,235,0.15) !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #64748b !important; border-radius: 8px !important; font-weight: 500 !important; font-size: 0.85rem !important; letter-spacing: 0.05em !important; }
.stTabs [aria-selected="true"] { background: #2563eb !important; color: white !important; }
.stSelectbox > div > div { background: #0f172a !important; border: 1px solid rgba(37,99,235,0.2) !important; border-radius: 10px !important; color: #e2e8f0 !important; }
.stDateInput > div > div { background: #0f172a !important; border: 1px solid rgba(37,99,235,0.2) !important; border-radius: 10px !important; }
.stButton > button { background: linear-gradient(135deg, #2563eb, #1d4ed8) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; letter-spacing: 0.05em !important; transition: all 0.3s !important; }
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: 0 8px 24px rgba(37,99,235,0.4) !important; }

.alert-critico {
    background: linear-gradient(135deg, rgba(239,68,68,0.08), rgba(239,68,68,0.03));
    border: 1px solid rgba(239,68,68,0.3);
    border-left: 3px solid #ef4444;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    transition: all 0.3s;
}
.alert-critico:hover { border-color: rgba(239,68,68,0.6); background: rgba(239,68,68,0.1); }
.alert-warning {
    background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(245,158,11,0.03));
    border: 1px solid rgba(245,158,11,0.3);
    border-left: 3px solid #f59e0b;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    transition: all 0.3s;
}
.alert-warning:hover { border-color: rgba(245,158,11,0.6); }
.alert-info {
    background: linear-gradient(135deg, rgba(37,99,235,0.08), rgba(37,99,235,0.03));
    border: 1px solid rgba(37,99,235,0.3);
    border-left: 3px solid #2563eb;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    transition: all 0.3s;
}
.alert-ok {
    background: linear-gradient(135deg, rgba(16,185,129,0.08), rgba(16,185,129,0.03));
    border: 1px solid rgba(16,185,129,0.3);
    border-left: 3px solid #10b981;
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
}
.kpi-highlight { color: #3b82f6; font-weight: 700; font-size: 1.1em; }
.tag { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; margin-right: 6px; }
.tag-red { background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }
.tag-amber { background: rgba(245,158,11,0.15); color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }
.tag-blue { background: rgba(37,99,235,0.15); color: #60a5fa; border: 1px solid rgba(37,99,235,0.3); }
.tag-green { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(37,99,235,0.3), transparent); margin: 24px 0; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def cargar_datos():
    base = Path(__file__).parent / "data"
    df = pd.read_csv(base / "iltonif_dataset_modelable_v3.csv", parse_dates=["fecha"])
    return df


@st.cache_data
def generar_recomendaciones(df):
    ultimo = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    recomendaciones = []
    for _, row in ultimo.iterrows():
        pvp = row["precio_venta"]
        coste = row["coste_unitario"]
        comp_min = row["precio_comp_min"]
        comp_avg = row["precio_comp_avg"]
        stock = row["stock_disponible"]
        media_7d = row["ventas_media_7d"] if row["ventas_media_7d"] > 0 else 1
        media_30d = row["ventas_media_30d"] if row["ventas_media_30d"] > 0 else 1
        cobertura = stock / media_7d if media_7d > 0 else 999

        if cobertura < 7:
            señal_stock = "CRÍTICO"
            accion_stock = f"Repón {int(media_7d*30)} uds — rotura en {int(cobertura)} días"
            impacto_stock = round(media_7d * pvp * max(0, 7 - cobertura), 0)
        elif cobertura < 15:
            señal_stock = "REPOSICIÓN"
            accion_stock = f"Repón {int(media_7d*30)} uds esta semana"
            impacto_stock = round(media_7d * pvp * 3, 0)
        elif cobertura > 45 and media_7d <= media_30d:
            señal_stock = "EXCESO"
            accion_stock = f"{int(cobertura)} días cobertura — considera promoción 15%"
            impacto_stock = round(stock * coste * 0.0003 * (cobertura - 30), 0)
        else:
            señal_stock = "OK"
            accion_stock = "Niveles óptimos"
            impacto_stock = 0

        dif_min = pvp - comp_min
        ratio = pvp / comp_avg if comp_avg > 0 else 1
        precio_min_viable = coste / 0.8

        if dif_min > comp_min * 0.10:
            bajada = min((dif_min / pvp) * 0.6, 0.20)
            precio_rec = max(round(pvp * (1 - bajada), 2), precio_min_viable)
            señal_pricing = "PRECIO ALTO"
            accion_pricing = f"Bajar {bajada*100:.1f}% → {precio_rec:.2f}€"
            impacto_pricing = round(media_7d * bajada * 1.5 * (precio_rec - coste), 0)
        elif ratio < 0.92:
            subida = 0.06
            precio_rec = round(pvp * (1 + subida), 2)
            señal_pricing = "SUBIR PRECIO"
            accion_pricing = f"Subir {subida*100:.0f}% → {precio_rec:.2f}€"
            impacto_pricing = round(media_7d * subida * pvp, 0)
        elif row.get("alerta_bajada_competidor", 0) == 1:
            señal_pricing = "ALERTA COMP."
            accion_pricing = "Competidor bajó >5% esta semana"
            precio_rec = pvp
            impacto_pricing = 0
        else:
            señal_pricing = "OK"
            accion_pricing = "Precio competitivo"
            precio_rec = pvp
            impacto_pricing = 0

        recomendaciones.append({
            "SKU": row["sku_id"], "Producto": row["nombre_producto"],
            "Categoría": row["categoria"], "Plataforma": row["plataforma"],
            "señal_stock": señal_stock, "accion_stock": accion_stock,
            "señal_pricing": señal_pricing, "accion_pricing": accion_pricing,
            "Precio actual": round(pvp, 2), "Precio rec.": round(precio_rec, 2),
            "Comp. mín.": round(comp_min, 2), "Comp. avg": round(comp_avg, 2),
            "Stock": int(stock), "Cobertura (días)": round(cobertura, 1),
            "Demanda/día": round(media_7d, 1),
            "Impacto stock €": impacto_stock, "Impacto pricing €": impacto_pricing,
            "Impacto total €": impacto_stock + impacto_pricing,
        })
    return pd.DataFrame(recomendaciones)


# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg"><rect width="44" height="44" rx="10" fill="#2563eb"/><circle cx="16" cy="13" r="6" fill="white"/><rect x="11" y="18" width="8" height="22" rx="4" fill="white" transform="rotate(-22 15 29)"/></svg><span style="font-size:18px;font-weight:800;color:#fff;letter-spacing:2px;vertical-align:middle;margin-left:10px">ILTONIF</span>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Filtros")

    df_raw = cargar_datos()
    categorias = ["Todas"] + sorted(df_raw["categoria"].unique().tolist())
    cat_sel = st.selectbox("Categoría", categorias)
    plataformas = ["Todas"] + sorted(df_raw["plataforma"].unique().tolist())
    plat_sel = st.selectbox("Plataforma", plataformas)

    st.markdown("---")
    fecha_min = df_raw["fecha"].min().date()
    fecha_max = df_raw["fecha"].max().date()
    rango = st.date_input("Rango histórico",
        value=(fecha_max - timedelta(days=90), fecha_max),
        min_value=fecha_min, max_value=fecha_max)

    st.markdown("---")
    st.markdown("**Pipeline**")
    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.caption(f"Último update: {datetime.now().strftime('%d/%m/%Y %H:%M')}")


# ── FILTRAR DATOS ─────────────────────────────────────────
df = df_raw.copy()
if cat_sel != "Todas":
    df = df[df["categoria"] == cat_sel]
if plat_sel != "Todas":
    df = df[df["plataforma"] == plat_sel]
if len(rango) == 2:
    df = df[(df["fecha"] >= pd.Timestamp(rango[0])) & (df["fecha"] <= pd.Timestamp(rango[1]))]

df_rec = generar_recomendaciones(df_raw)
if cat_sel != "Todas":
    df_rec = df_rec[df_rec["Categoría"] == cat_sel]

sku_nombres = {row["sku_id"]: row["nombre_producto"]
               for _, row in df[["sku_id","nombre_producto"]].drop_duplicates().iterrows()}


# ── HEADER ────────────────────────────────────────────────
st.markdown('''
<div style="display:flex;align-items:center;gap:20px;padding:24px 0 28px 0;border-bottom:1px solid rgba(37,99,235,0.2);margin-bottom:8px">
  <svg width="72" height="72" viewBox="0 0 72 72" xmlns="http://www.w3.org/2000/svg">
    <rect width="72" height="72" rx="18" fill="#2563eb"/>
    <circle cx="26" cy="21" r="10" fill="white"/>
    <rect x="18" y="30" width="13" height="38" rx="6" fill="white" transform="rotate(-22 24 49)"/>
  </svg>
  <div>
    <div style="font-size:40px;font-weight:900;color:#ffffff;letter-spacing:4px;line-height:1;font-family:'Space Grotesk',sans-serif">ILTONIF</div>
    <div style="font-size:13px;color:#2563eb;letter-spacing:3px;margin-top:6px;font-weight:600">Intelligence Platform</div>
  </div>
</div>''', unsafe_allow_html=True)


# ── KPIs ──────────────────────────────────────────────────
criticos   = (df_rec["señal_stock"] == "CRÍTICO").sum()
reposicion = (df_rec["señal_stock"] == "REPOSICIÓN").sum()
precio_alto= (df_rec["señal_pricing"] == "PRECIO ALTO").sum()
oportunidad= (df_rec["señal_pricing"] == "SUBIR PRECIO").sum()
impacto    = df_rec["Impacto total €"].sum()

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("🔴 Stock crítico", f"{criticos} SKUs", delta=f"-{criticos} requieren acción", delta_color="inverse")
with col2:
    st.metric("🟠 Reposición", f"{reposicion} SKUs", delta="Esta semana")
with col3:
    st.metric("💰 Precio alto", f"{precio_alto} SKUs", delta="vs competencia", delta_color="inverse")
with col4:
    st.metric("📈 Oportunidad", f"{oportunidad} SKUs", delta="Subida posible")
with col5:
    st.metric("💶 Impacto total", f"{impacto:,.0f}€", delta="Estimado hoy")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🚨  Alertas del día", "📊  Demanda por SKU", "💰  Pricing", "📦  Stock"])


# ══ TAB 1: ALERTAS ════════════════════════════════════════
with tab1:
    st.markdown("### Recomendaciones accionables de hoy")

    PRIORIDAD = {"CRÍTICO":0,"PRECIO ALTO":1,"REPOSICIÓN":2,"SUBIR PRECIO":3,"ALERTA COMP.":4,"EXCESO":5,"OK":99}
    df_rec["prio"] = df_rec["señal_stock"].map(PRIORIDAD).fillna(99)
    df_sorted = df_rec[df_rec["prio"] < 99].sort_values("prio")

    for _, row in df_sorted.iterrows():
        ss = row["señal_stock"]
        sp = row["señal_pricing"]
        imp = row["Impacto total €"]

        if ss == "CRÍTICO":
            css = "alert-critico"
            badge_s = '<span class="tag tag-red">CRÍTICO</span>'
        elif ss == "REPOSICIÓN":
            css = "alert-warning"
            badge_s = '<span class="tag tag-amber">REPOSICIÓN</span>'
        elif ss == "EXCESO":
            css = "alert-info"
            badge_s = '<span class="tag tag-blue">EXCESO</span>'
        else:
            css = "alert-ok"
            badge_s = '<span class="tag tag-green">OK</span>'

        if sp == "PRECIO ALTO":
            badge_p = '<span class="tag tag-red">PRECIO ALTO</span>'
        elif sp == "SUBIR PRECIO":
            badge_p = '<span class="tag tag-green">SUBIR PRECIO</span>'
        elif sp == "ALERTA COMP.":
            badge_p = '<span class="tag tag-amber">ALERTA COMP.</span>'
        else:
            badge_p = '<span class="tag tag-blue">OK</span>'

        impacto_html = f'<span style="color:#3b82f6;font-weight:700;font-size:0.95em">+{imp:,.0f}€ impacto estimado</span>' if imp > 0 else ""

        st.markdown(f"""
        <div class="{css}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px">
            <div>
              <span style="font-weight:700;font-size:1em;color:#f1f5f9">{row['Producto']}</span>
              <span style="color:#475569;font-size:0.8em;margin-left:8px">{row['Categoría']} · {row['Plataforma']}</span>
            </div>
            <div>{badge_s}{badge_p}</div>
          </div>
          <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:4px">
            <div style="font-size:0.82em;color:#94a3b8">📦 {row['accion_stock']}</div>
            <div style="font-size:0.82em;color:#94a3b8">💰 {row['accion_pricing']}</div>
          </div>
          <div style="margin-top:8px;display:flex;gap:16px;font-size:0.78em;color:#64748b">
            <span>Precio: <b style="color:#e2e8f0">{row['Precio actual']}€</b></span>
            <span>Comp.mín: <b style="color:#e2e8f0">{row['Comp. mín.']}€</b></span>
            <span>Stock: <b style="color:#e2e8f0">{row['Stock']} uds</b></span>
            <span>Cobertura: <b style="color:#e2e8f0">{row['Cobertura (días)']} días</b></span>
          </div>
          {'<div style="margin-top:10px">' + impacto_html + '</div>' if impacto_html else ''}
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown("### Distribución de alertas")
    col_a, col_b = st.columns(2)

    with col_a:
        conteo_stock = df_rec["señal_stock"].value_counts().reset_index()
        conteo_stock.columns = ["Señal","Count"]
        fig_s = px.pie(conteo_stock, values="Count", names="Señal", hole=0.6,
                       color="Señal",
                       color_discrete_map={"CRÍTICO":"#ef4444","REPOSICIÓN":"#f59e0b","EXCESO":"#3b82f6","OK":"#10b981"},
                       title="Estado de stock")
        fig_s.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#94a3b8", height=280,
                            title_font_color="#e2e8f0",
                            legend=dict(font=dict(color="#94a3b8")))
        st.plotly_chart(fig_s, use_container_width=True)

    with col_b:
        conteo_p = df_rec["señal_pricing"].value_counts().reset_index()
        conteo_p.columns = ["Señal","Count"]
        fig_p = px.pie(conteo_p, values="Count", names="Señal", hole=0.6,
                       color="Señal",
                       color_discrete_map={"PRECIO ALTO":"#ef4444","SUBIR PRECIO":"#10b981","ALERTA COMP.":"#f59e0b","OK":"#3b82f6"},
                       title="Estado de pricing")
        fig_p.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#94a3b8", height=280,
                            title_font_color="#e2e8f0",
                            legend=dict(font=dict(color="#94a3b8")))
        st.plotly_chart(fig_p, use_container_width=True)


# ══ TAB 2: DEMANDA ════════════════════════════════════════
with tab2:
    st.markdown("### Evolución de demanda por SKU")
    skus = sorted(df["sku_id"].unique())
    sku_sel = st.multiselect("Selecciona SKUs", options=skus, default=skus[:4],
                              format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")

    if sku_sel:
        df_plot = df[df["sku_id"].isin(sku_sel)].copy()
        df_agg = df_plot.groupby(["fecha","sku_id","nombre_producto"])["unidades_vendidas"].sum().reset_index()
        fig_dem = px.line(df_agg, x="fecha", y="unidades_vendidas", color="nombre_producto",
                          labels={"unidades_vendidas":"Unidades","fecha":"Fecha","nombre_producto":"Producto"})
        fig_dem.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              font_color="#94a3b8", height=380,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.4, font=dict(color="#94a3b8")),
                              xaxis=dict(gridcolor="rgba(37,99,235,0.1)"),
                              yaxis=dict(gridcolor="rgba(37,99,235,0.1)"))
        st.plotly_chart(fig_dem, use_container_width=True)

        st.markdown("### Estacionalidad por mes y día de semana")
        sku_heat = st.selectbox("SKU para heatmap", options=sku_sel, format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
        df_heat = df[df["sku_id"] == sku_heat].copy()
        dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        pivot = df_heat.groupby(["mes","dia_semana"])["unidades_vendidas"].mean().unstack(fill_value=0)
        pivot.index = [meses[i-1] for i in pivot.index]
        pivot.columns = [dias[i] for i in pivot.columns]
        fig_heat = px.imshow(pivot, color_continuous_scale="Blues",
                             labels=dict(color="Uds/día"),
                             title=f"Demanda media — {sku_nombres.get(sku_heat,'')}")
        fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                               font_color="#94a3b8", height=320, title_font_color="#e2e8f0")
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("### Métricas por producto")
        resumen = df_plot.groupby(["sku_id","nombre_producto"]).agg(
            Ventas_total=("unidades_vendidas","sum"),
            Media_diaria=("unidades_vendidas","mean"),
            Ingreso_total=("ingreso_estimado","sum"),
            Margen_total=("margen_estimado_eur","sum"),
        ).reset_index().round(1)
        resumen.columns = ["SKU","Producto","Ventas totales","Media/día","Ingreso €","Margen €"]
        st.dataframe(resumen, use_container_width=True, hide_index=True)


# ══ TAB 3: PRICING ════════════════════════════════════════
with tab3:
    st.markdown("### Comparativa de precios vs competencia")
    ultimo_df = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    productos = ultimo_df["nombre_producto"].tolist()

    fig_precio = go.Figure()
    fig_precio.add_trace(go.Bar(name="Tu precio", x=productos, y=ultimo_df["precio_venta"], marker_color="#2563eb"))
    fig_precio.add_trace(go.Bar(name="Decathlon", x=productos, y=ultimo_df["precio_decathlon"], marker_color="#ef4444"))
    fig_precio.add_trace(go.Bar(name="TrailZone", x=productos, y=ultimo_df["precio_trailzone"], marker_color="#a855f7"))
    fig_precio.add_trace(go.Bar(name="OutdoorPro", x=productos, y=ultimo_df["precio_outdoorpro"], marker_color="#10b981"))
    fig_precio.update_layout(barmode="group", paper_bgcolor="rgba(0,0,0,0)",
                             plot_bgcolor="rgba(0,0,0,0)", font_color="#94a3b8", height=400,
                             xaxis_tickangle=-35, legend=dict(orientation="h", yanchor="bottom", y=-0.5, font=dict(color="#94a3b8")),
                             xaxis=dict(gridcolor="rgba(37,99,235,0.1)"),
                             yaxis=dict(gridcolor="rgba(37,99,235,0.1)", title="Precio (€)"))
    st.plotly_chart(fig_precio, use_container_width=True)

    st.markdown("### Evolución de precio vs competencia")
    sku_precio = st.selectbox("Producto", options=sorted(df["sku_id"].unique()),
                               format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}", key="p_sku")
    df_sku = df[df["sku_id"] == sku_precio].copy()

    fig_ev = go.Figure()
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_venta"], name="Tu precio", line=dict(color="#2563eb", width=2.5)))
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_decathlon"], name="Decathlon", line=dict(color="#ef4444", width=1.2, dash="dot")))
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_trailzone"], name="TrailZone", line=dict(color="#a855f7", width=1.2, dash="dot")))
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_outdoorpro"], name="OutdoorPro", line=dict(color="#10b981", width=1.2, dash="dot")))
    fig_ev.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         font_color="#94a3b8", height=360,
                         legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(color="#94a3b8")),
                         xaxis=dict(gridcolor="rgba(37,99,235,0.1)"),
                         yaxis=dict(gridcolor="rgba(37,99,235,0.1)", title="Precio (€)"))
    st.plotly_chart(fig_ev, use_container_width=True)

    st.markdown("### Recomendaciones de pricing")
    cols_p = ["Producto","Categoría","señal_pricing","accion_pricing","Precio actual","Precio rec.","Comp. mín.","Comp. avg","Impacto pricing €"]
    df_tp = df_rec[cols_p].copy()
    df_tp.columns = ["Producto","Categoría","Señal","Acción","Precio actual €","Precio rec. €","Comp. mín. €","Comp. avg €","Impacto €"]
    def color_p(val):
        if val == "PRECIO ALTO": return "background-color:rgba(239,68,68,0.15);color:#ef4444"
        if val == "SUBIR PRECIO": return "background-color:rgba(16,185,129,0.15);color:#10b981"
        if val == "ALERTA COMP.": return "background-color:rgba(245,158,11,0.15);color:#f59e0b"
        return "background-color:rgba(37,99,235,0.15);color:#60a5fa"
    st.dataframe(df_tp.style.map(color_p, subset=["Señal"]), use_container_width=True, hide_index=True, height=380)


# ══ TAB 4: STOCK ══════════════════════════════════════════
with tab4:
    st.markdown("### Stock disponible por SKU")
    ultimo_s = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    ultimo_s_sorted = ultimo_s.sort_values("stock_disponible", ascending=True)

    colores_bar = []
    for _, r in ultimo_s_sorted.iterrows():
        cob = r["stock_disponible"] / max(r["ventas_media_7d"], 0.1)
        if cob < 7: colores_bar.append("#ef4444")
        elif cob < 15: colores_bar.append("#f59e0b")
        elif cob > 45: colores_bar.append("#3b82f6")
        else: colores_bar.append("#10b981")

    fig_stock = go.Figure()
    fig_stock.add_trace(go.Bar(x=ultimo_s_sorted["stock_disponible"], y=ultimo_s_sorted["nombre_producto"],
                               orientation="h", marker_color=colores_bar,
                               text=ultimo_s_sorted["stock_disponible"].astype(str)+" uds", textposition="outside"))
    fig_stock.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#94a3b8", height=460, xaxis_title="Unidades en stock",
                            xaxis=dict(gridcolor="rgba(37,99,235,0.1)"))
    st.plotly_chart(fig_stock, use_container_width=True)

    st.markdown("### Días de cobertura")
    df_cob = df_rec.sort_values("Cobertura (días)")
    cols_cob = [r["Cobertura (días)"] for _, r in df_cob.iterrows()]
    colores_cob = ["#ef4444" if c < 7 else "#f59e0b" if c < 15 else "#3b82f6" if c > 45 else "#10b981" for c in cols_cob]

    fig_cob = go.Figure()
    fig_cob.add_trace(go.Bar(x=df_cob["Cobertura (días)"], y=df_cob["Producto"],
                             orientation="h", marker_color=colores_cob,
                             text=[f"{c} días" for c in cols_cob], textposition="outside"))
    fig_cob.add_vline(x=7, line_dash="dash", line_color="#ef4444", annotation_text="Crítico", annotation_font_color="#ef4444")
    fig_cob.add_vline(x=15, line_dash="dash", line_color="#f59e0b", annotation_text="Riesgo", annotation_font_color="#f59e0b")
    fig_cob.add_vline(x=45, line_dash="dash", line_color="#3b82f6", annotation_text="Exceso", annotation_font_color="#3b82f6")
    fig_cob.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#94a3b8", height=460, xaxis_title="Días",
                          xaxis=dict(gridcolor="rgba(37,99,235,0.1)"))
    st.plotly_chart(fig_cob, use_container_width=True)

    st.markdown("### Alertas de stock")
    cols_s = ["Producto","Categoría","señal_stock","accion_stock","Stock","Cobertura (días)","Demanda/día","Impacto stock €"]
    df_ts = df_rec[cols_s].copy()
    df_ts.columns = ["Producto","Categoría","Señal","Acción","Stock uds","Cobertura días","Demanda/día","Impacto €"]
    def color_s(val):
        if val == "CRÍTICO": return "background-color:rgba(239,68,68,0.15);color:#ef4444"
        if val == "REPOSICIÓN": return "background-color:rgba(245,158,11,0.15);color:#f59e0b"
        if val == "EXCESO": return "background-color:rgba(37,99,235,0.15);color:#60a5fa"
        return "background-color:rgba(16,185,129,0.15);color:#10b981"
    st.dataframe(df_ts.style.map(color_s, subset=["Señal"]), use_container_width=True, hide_index=True, height=380)


# ── FOOTER ────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(
    "<div style='text-align:center;color:#334155;font-size:11px;letter-spacing:2px;padding:8px 0'>ILTONIF © 2025 — INTELLIGENCE PLATFORM · PRICING & STOCK AI</div>",
    unsafe_allow_html=True
)
