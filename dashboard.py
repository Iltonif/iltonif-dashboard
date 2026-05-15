LOGO_SVG = """<svg width="100" height="100" viewBox="0 0 110 110" xmlns="http://www.w3.org/2000/svg"><rect width="110" height="110" rx="18" fill="#0a0f1e"/><rect width="110" height="110" rx="18" fill="none" stroke="#22d3ee" stroke-width="2" opacity="0.8"/><rect x="18" y="62" width="14" height="28" rx="4" fill="#185FA5" opacity="0.8"/><rect x="37" y="44" width="14" height="46" rx="4" fill="#378ADD"/><rect x="56" y="28" width="14" height="62" rx="4" fill="#22d3ee"/><circle cx="83" cy="20" r="7" fill="#22d3ee"/><line x1="18" y1="68" x2="83" y2="20" stroke="#22d3ee" stroke-width="2" stroke-dasharray="4 3" opacity="0.6"/></svg>"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import json
from datetime import datetime, timedelta

# --- CONFIG ---
st.set_page_config(
    page_title="ILTONIF — Dashboard",
    page_icon="https://raw.githubusercontent.com/iltonifsaas/iltonif-dashboard/main/iltonif_logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS ---
st.markdown("""
<style>
    .main { background-color: #0e1117; }
    .metric-card {
        background: linear-gradient(135deg, #1e2130, #252a3d);
        border-radius: 12px;
        padding: 20px;
        border-left: 4px solid;
        margin-bottom: 10px;
    }
    .card-critico  { border-color: #ff4b4b; }
    .card-warning  { border-color: #ffa500; }
    .card-ok       { border-color: #00c853; }
    .card-info     { border-color: #2196f3; }
    .alert-critico {
        background: rgba(255,75,75,0.15);
        border: 1px solid #ff4b4b;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .alert-warning {
        background: rgba(255,165,0,0.15);
        border: 1px solid #ffa500;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .alert-ok {
        background: rgba(0,200,83,0.15);
        border: 1px solid #00c853;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .alert-info {
        background: rgba(33,150,243,0.15);
        border: 1px solid #2196f3;
        border-radius: 10px;
        padding: 14px;
        margin: 6px 0;
    }
    .stMetric { background: #1e2130; border-radius: 10px; padding: 10px; }
    h1, h2, h3 { color: #ffffff; }
    .sidebar .sidebar-content { background: #1e2130; }
</style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS ---
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
        pvp       = row["precio_venta"]
        coste     = row["coste_unitario"]
        comp_min  = row["precio_comp_min"]
        comp_avg  = row["precio_comp_avg"]
        stock     = row["stock_disponible"]
        media_7d  = row["ventas_media_7d"] if row["ventas_media_7d"] > 0 else 1
        media_30d = row["ventas_media_30d"] if row["ventas_media_30d"] > 0 else 1
        cobertura = stock / media_7d if media_7d > 0 else 999

        # Señal stock
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

        # Señal pricing
        dif_min = pvp - comp_min
        ratio   = pvp / comp_avg if comp_avg > 0 else 1
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
            "SKU":              row["sku_id"],
            "Producto":         row["nombre_producto"],
            "Categoría":        row["categoria"],
            "Plataforma":       row["plataforma"],
            "señal_stock":      señal_stock,
            "accion_stock":     accion_stock,
            "señal_pricing":    señal_pricing,
            "accion_pricing":   accion_pricing,
            "Precio actual":    round(pvp, 2),
            "Precio rec.":      round(precio_rec, 2),
            "Comp. mín.":       round(comp_min, 2),
            "Comp. avg":        round(comp_avg, 2),
            "Stock":            int(stock),
            "Cobertura (días)": round(cobertura, 1),
            "Demanda/día":      round(media_7d, 1),
            "Impacto stock €":  impacto_stock,
            "Impacto pricing €":impacto_pricing,
            "Impacto total €":  impacto_stock + impacto_pricing,
        })
    return pd.DataFrame(recomendaciones)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown('''
<div style="display:flex;align-items:center;gap:20px;padding:8px 0 24px 0">
  <svg width="56" height="56" viewBox="0 0 56 56" xmlns="http://www.w3.org/2000/svg">
    <rect width="56" height="56" rx="14" fill="#2563eb"/>
    <circle cx="20" cy="17" r="8" fill="white"/>
    <rect x="14" y="24" width="10" height="28" rx="5" fill="white" transform="rotate(-22 19 38)"/>
  </svg>
  <div>
    <div style="font-size:32px;font-weight:800;color:#ffffff;letter-spacing:2px;line-height:1.1">ILTONIF</div>
    <div style="font-size:10px;color:rgba(255,255,255,0.4);letter-spacing:4px;margin-top:2px">PREDICE · DECIDE · CRECE</div>
  </div>
</div>''', unsafe_allow_html=True)
    st.markdown('''<svg width="80" height="80" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
<rect width="80" height="80" rx="16" fill="#2563eb"/>
<circle cx="28" cy="22" r="11" fill="white"/>
<rect x="20" y="32" width="12" height="42" rx="6" fill="white" transform="rotate(-22 26 53)"/>
</svg>''', unsafe_allow_html=True)
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

# --- FILTRAR DATOS ---
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

# --- HEADER ---
col_logo, col_title = st.columns([1, 4])
with col_logo:
    st.markdown('''
<div style="display:flex;align-items:center;gap:16px;margin-bottom:8px">
<svg width="52" height="52" viewBox="0 0 52 52" xmlns="http://www.w3.org/2000/svg">
<rect width="52" height="52" rx="10" fill="#2563eb"/>
<circle cx="18" cy="16" r="7" fill="white"/>
<rect x="13" y="22" width="8" height="26" rx="4" fill="white" transform="rotate(-22 17 35)"/>
</svg>
<div>
<div style="font-size:28px;font-weight:800;color:#ffffff;letter-spacing:1px;line-height:1">ILTONIF</div>
<div style="font-size:11px;color:#2563eb;letter-spacing:3px">INTELLIGENCE PLATFORM</div>
</div>
</div>''', unsafe_allow_html=True)
with col_title:
        st.markdown("---")

# --- KPIs ---
col1, col2, col3, col4, col5 = st.columns(5)
criticos   = (df_rec["señal_stock"] == "CRÍTICO").sum()
reposicion = (df_rec["señal_stock"] == "REPOSICIÓN").sum()
precio_alto= (df_rec["señal_pricing"] == "PRECIO ALTO").sum()
oportunidad= (df_rec["señal_pricing"] == "SUBIR PRECIO").sum()
impacto    = df_rec["Impacto total €"].sum()

with col1:
    st.metric("🔴 Stock crítico", f"{criticos} SKUs",
              delta=f"-{criticos} requieren acción", delta_color="inverse")
with col2:
    st.metric("🟠 Reposición", f"{reposicion} SKUs",
              delta="Esta semana")
with col3:
    st.metric("💰 Precio alto", f"{precio_alto} SKUs",
              delta="vs competencia", delta_color="inverse")
with col4:
    st.metric("📈 Oportunidad", f"{oportunidad} SKUs",
              delta="Subida posible")
with col5:
    st.metric("💶 Impacto total", f"{impacto:,.0f}€",
              delta="Estimado hoy")

st.markdown("---")

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "🚨 Alertas del día",
    "📊 Demanda por SKU",
    "💰 Pricing",
    "📦 Stock"
])

# ==================== TAB 1: ALERTAS ====================
with tab1:
    st.markdown("### Recomendaciones accionables de hoy")

    prioridad_map = {"CRÍTICO": 0, "PRECIO ALTO": 1, "REPOSICIÓN": 2,
                     "SUBIR PRECIO": 3, "ALERTA COMP.": 4, "EXCESO": 5, "OK": 99}
    df_rec["prio"] = df_rec["señal_stock"].map(prioridad_map).fillna(99)
    df_sorted = df_rec[df_rec["prio"] < 99].sort_values("prio")

    for _, row in df_sorted.iterrows():
        señal_s = row["señal_stock"]
        señal_p = row["señal_pricing"]

        if señal_s == "CRÍTICO":
            css = "alert-critico"
            icono = "🔴"
        elif señal_s == "REPOSICIÓN":
            css = "alert-warning"
            icono = "🟠"
        elif señal_p in ["PRECIO ALTO", "ALERTA COMP."]:
            css = "alert-warning"
            icono = "🟡"
        elif señal_p == "SUBIR PRECIO":
            css = "alert-info"
            icono = "🔵"
        else:
            css = "alert-ok"
            icono = "🟢"

        impacto_str = f"**Impacto estimado: {row['Impacto total €']:,.0f}€**" if row["Impacto total €"] > 0 else ""

        st.markdown(f"""
        <div class="{css}">
            <b>{icono} {row['Producto']}</b> &nbsp;|&nbsp; {row['Categoría']} &nbsp;|&nbsp; {row['Plataforma']}<br>
            <span style='color:#aaa; font-size:13px'>
                📦 Stock: <b>{señal_s}</b> — {row['accion_stock']} &nbsp;&nbsp;
                💰 Precio: <b>{señal_p}</b> — {row['accion_pricing']}
            </span><br>
            <span style='font-size:12px; color:#888'>
                Precio actual: {row['Precio actual']}€ | Comp. mín: {row['Comp. mín.']:.2f}€ |
                Stock: {row['Stock']} uds | Cobertura: {row['Cobertura (días)']} días
            </span>
            {"<br><span style='color:#4fc3f7; font-size:13px'>" + impacto_str + "</span>" if impacto_str else ""}
        </div>
        """, unsafe_allow_html=True)

    # Resumen gráfico
    st.markdown("### Distribución de alertas")
    col_a, col_b = st.columns(2)

    with col_a:
        conteo_stock = df_rec["señal_stock"].value_counts().reset_index()
        conteo_stock.columns = ["Señal", "Count"]
        colores_stock = {"CRÍTICO":"#ff4b4b","REPOSICIÓN":"#ffa500",
                         "EXCESO":"#2196f3","OK":"#00c853"}
        fig_stock = px.pie(conteo_stock, values="Count", names="Señal",
                           color="Señal", color_discrete_map=colores_stock,
                           title="Estado de stock", hole=0.5)
        fig_stock.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=300)
        st.plotly_chart(fig_stock, use_container_width=True)

    with col_b:
        conteo_pricing = df_rec["señal_pricing"].value_counts().reset_index()
        conteo_pricing.columns = ["Señal", "Count"]
        colores_pricing = {"PRECIO ALTO":"#ff4b4b","SUBIR PRECIO":"#00c853",
                           "ALERTA COMP.":"#ffa500","OK":"#2196f3"}
        fig_pricing = px.pie(conteo_pricing, values="Count", names="Señal",
                             color="Señal", color_discrete_map=colores_pricing,
                             title="Estado de pricing", hole=0.5)
        fig_pricing.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                  plot_bgcolor="rgba(0,0,0,0)",
                                  font_color="white", height=300)
        st.plotly_chart(fig_pricing, use_container_width=True)

# ==================== TAB 2: DEMANDA ====================
with tab2:
    st.markdown("### Evolución de demanda por SKU")

    skus = sorted(df["sku_id"].unique())
    sku_nombres = {row["sku_id"]: row["nombre_producto"]
                   for _, row in df[["sku_id","nombre_producto"]].drop_duplicates().iterrows()}
    sku_sel = st.multiselect("Selecciona SKUs",
                              options=skus,
                              default=skus[:4],
                              format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")

    if sku_sel:
        df_plot = df[df["sku_id"].isin(sku_sel)].copy()
        df_agg = df_plot.groupby(["fecha","sku_id","nombre_producto"])["unidades_vendidas"].sum().reset_index()

        fig_dem = px.line(df_agg, x="fecha", y="unidades_vendidas",
                          color="nombre_producto",
                          title="Unidades vendidas diarias",
                          labels={"unidades_vendidas":"Unidades","fecha":"Fecha",
                                  "nombre_producto":"Producto"})
        fig_dem.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font_color="white", height=400,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.4))
        fig_dem.update_xaxes(gridcolor="#2a2a3d")
        fig_dem.update_yaxes(gridcolor="#2a2a3d")
        st.plotly_chart(fig_dem, use_container_width=True)

        # Heatmap estacionalidad
        st.markdown("### Estacionalidad por mes y día de semana")
        sku_heat = st.selectbox("SKU para heatmap",
                                 options=sku_sel,
                                 format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
        df_heat = df[df["sku_id"] == sku_heat].copy()
        dias = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        pivot = df_heat.groupby(["mes","dia_semana"])["unidades_vendidas"].mean().unstack(fill_value=0)
        pivot.index = [meses[i-1] for i in pivot.index]
        pivot.columns = [dias[i] for i in pivot.columns]

        fig_heat = px.imshow(pivot, color_continuous_scale="Blues",
                              title=f"Demanda media — {sku_nombres.get(sku_heat,'')}",
                              labels=dict(color="Uds/día"))
        fig_heat.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)",
                               font_color="white", height=350)
        st.plotly_chart(fig_heat, use_container_width=True)

        # Métricas por SKU
        st.markdown("### Métricas por producto")
        resumen = df_plot.groupby(["sku_id","nombre_producto"]).agg(
            Ventas_total=("unidades_vendidas","sum"),
            Media_diaria=("unidades_vendidas","mean"),
            Ingreso_total=("ingreso_estimado","sum"),
            Margen_total=("margen_estimado_eur","sum"),
        ).reset_index().round(1)
        resumen.columns = ["SKU","Producto","Ventas totales","Media/día","Ingreso €","Margen €"]
        st.dataframe(resumen, use_container_width=True, hide_index=True)

# ==================== TAB 3: PRICING ====================
with tab3:
    st.markdown("### Análisis de pricing vs competencia")

    ultimo_df = df.sort_values("fecha").groupby("sku_id").last().reset_index()

    fig_precio = go.Figure()
    productos  = ultimo_df["nombre_producto"].tolist()
    fig_precio.add_trace(go.Bar(name="Tu precio", x=productos,
                                y=ultimo_df["precio_venta"],
                                marker_color="#4fc3f7"))
    fig_precio.add_trace(go.Bar(name="Decathlon", x=productos,
                                y=ultimo_df["precio_decathlon"],
                                marker_color="#ff7043"))
    fig_precio.add_trace(go.Bar(name="TrailZone", x=productos,
                                y=ultimo_df["precio_trailzone"],
                                marker_color="#ab47bc"))
    fig_precio.add_trace(go.Bar(name="OutdoorPro", x=productos,
                                y=ultimo_df["precio_outdoorpro"],
                                marker_color="#66bb6a"))
    fig_precio.update_layout(barmode="group", title="Comparativa precios vs competencia",
                              paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              font_color="white", height=420,
                              xaxis_tickangle=-35,
                              legend=dict(orientation="h", yanchor="bottom", y=-0.5))
    fig_precio.update_xaxes(gridcolor="#2a2a3d")
    fig_precio.update_yaxes(gridcolor="#2a2a3d", title="Precio (€)")
    st.plotly_chart(fig_precio, use_container_width=True)

    # Evolución precio vs competencia de un SKU
    st.markdown("### Evolución precio en el tiempo")
    sku_precio = st.selectbox("Selecciona producto",
                               options=sorted(df["sku_id"].unique()),
                               format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
    df_sku = df[df["sku_id"] == sku_precio].copy()

    fig_ev = go.Figure()
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_venta"],
                                name="Tu precio", line=dict(color="#4fc3f7", width=2)))
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_decathlon"],
                                name="Decathlon", line=dict(color="#ff7043", width=1, dash="dot")))
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_trailzone"],
                                name="TrailZone", line=dict(color="#ab47bc", width=1, dash="dot")))
    fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku["precio_outdoorpro"],
                                name="OutdoorPro", line=dict(color="#66bb6a", width=1, dash="dot")))
    fig_ev.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                         plot_bgcolor="rgba(0,0,0,0)",
                         font_color="white", height=380,
                         legend=dict(orientation="h", yanchor="bottom", y=-0.3))
    fig_ev.update_xaxes(gridcolor="#2a2a3d")
    fig_ev.update_yaxes(gridcolor="#2a2a3d", title="Precio (€)")
    st.plotly_chart(fig_ev, use_container_width=True)

    # Tabla recomendaciones pricing
    st.markdown("### Tabla de recomendaciones de pricing")
    cols_precio = ["Producto","Categoría","señal_pricing","accion_pricing",
                   "Precio actual","Precio rec.","Comp. mín.","Comp. avg","Impacto pricing €"]
    df_tabla_p = df_rec[cols_precio].copy()
    df_tabla_p.columns = ["Producto","Categoría","Señal","Acción recomendada",
                           "Precio actual €","Precio rec. €","Comp. mín. €","Comp. avg €","Impacto €"]

    def color_señal_p(val):
        if val == "PRECIO ALTO": return "background-color:#ff4b4b22; color:#ff4b4b"
        if val == "SUBIR PRECIO": return "background-color:#00c85322; color:#00c853"
        if val == "ALERTA COMP.": return "background-color:#ffa50022; color:#ffa500"
        return "background-color:#2196f322; color:#2196f3"

    st.dataframe(df_tabla_p.style.map(color_señal_p, subset=["Señal"]),
                 use_container_width=True, hide_index=True, height=400)

# ==================== TAB 4: STOCK ====================
with tab4:
    st.markdown("### Estado de stock por SKU")

    fig_stock = go.Figure()
    ultimo_df_sorted = ultimo_df.sort_values("stock_disponible", ascending=True)
    colores_bar = []
    for _, r in ultimo_df_sorted.iterrows():
        cob = r["stock_disponible"] / max(r["ventas_media_7d"], 0.1)
        if cob < 7:   colores_bar.append("#ff4b4b")
        elif cob < 15: colores_bar.append("#ffa500")
        elif cob > 45: colores_bar.append("#2196f3")
        else:          colores_bar.append("#00c853")

    fig_stock.add_trace(go.Bar(
        x=ultimo_df_sorted["stock_disponible"],
        y=ultimo_df_sorted["nombre_producto"],
        orientation="h",
        marker_color=colores_bar,
        text=ultimo_df_sorted["stock_disponible"].astype(str) + " uds",
        textposition="outside"
    ))
    fig_stock.update_layout(title="Stock disponible por producto",
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            font_color="white", height=480,
                            xaxis_title="Unidades en stock")
    fig_stock.update_xaxes(gridcolor="#2a2a3d")
    st.plotly_chart(fig_stock, use_container_width=True)

    # Cobertura en días
    st.markdown("### Días de cobertura por SKU")
    df_rec_stock = df_rec.copy()
    df_rec_stock = df_rec_stock.sort_values("Cobertura (días)")

    fig_cob = go.Figure()
    colores_cob = []
    for _, r in df_rec_stock.iterrows():
        c = r["Cobertura (días)"]
        if c < 7:   colores_cob.append("#ff4b4b")
        elif c < 15: colores_cob.append("#ffa500")
        elif c > 45: colores_cob.append("#2196f3")
        else:        colores_cob.append("#00c853")

    fig_cob.add_trace(go.Bar(
        x=df_rec_stock["Cobertura (días)"],
        y=df_rec_stock["Producto"],
        orientation="h",
        marker_color=colores_cob,
        text=df_rec_stock["Cobertura (días)"].astype(str) + " días",
        textposition="outside"
    ))
    fig_cob.add_vline(x=7, line_dash="dash", line_color="#ff4b4b",
                      annotation_text="Crítico (<7)", annotation_font_color="#ff4b4b")
    fig_cob.add_vline(x=15, line_dash="dash", line_color="#ffa500",
                      annotation_text="Riesgo (<15)", annotation_font_color="#ffa500")
    fig_cob.add_vline(x=45, line_dash="dash", line_color="#2196f3",
                      annotation_text="Exceso (>45)", annotation_font_color="#2196f3")
    fig_cob.update_layout(title="Días de cobertura de stock",
                          paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",
                          font_color="white", height=480,
                          xaxis_title="Días")
    fig_cob.update_xaxes(gridcolor="#2a2a3d")
    st.plotly_chart(fig_cob, use_container_width=True)

    # Tabla stock
    st.markdown("### Tabla de alertas de stock")
    cols_stock = ["Producto","Categoría","señal_stock","accion_stock",
                  "Stock","Cobertura (días)","Demanda/día","Impacto stock €"]
    df_tabla_s = df_rec[cols_stock].copy()
    df_tabla_s.columns = ["Producto","Categoría","Señal","Acción recomendada",
                           "Stock uds","Cobertura días","Demanda/día","Impacto €"]

    def color_señal_s(val):
        if val == "CRÍTICO":    return "background-color:#ff4b4b22; color:#ff4b4b"
        if val == "REPOSICIÓN": return "background-color:#ffa50022; color:#ffa500"
        if val == "EXCESO":     return "background-color:#2196f322; color:#2196f3"
        return "background-color:#00c85322; color:#00c853"

    st.dataframe(df_tabla_s.style.map(color_señal_s, subset=["Señal"]),
                 use_container_width=True, hide_index=True, height=400)

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#555; font-size:12px'>"
    "ILTONIF © 2025 — Plataforma SaaS de Optimización de Pricing y Stock para eCommerce"
    "</div>", unsafe_allow_html=True
)
