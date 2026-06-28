import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta

st.set_page_config(
    page_title="ILTONIF — Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'Inter', sans-serif !important; }

/* ── FONDO GENERAL ── */
.main { background: #F8F9FC !important; }
.block-container { padding: 1.5rem 2rem 2rem !important; max-width: 100% !important; background: #F8F9FC !important; }
[data-testid="stAppViewContainer"] { background: #F8F9FC !important; }
[data-testid="stVerticalBlock"] { background: transparent !important; }
.stApp { background: #F8F9FC !important; }
section.main { background: #F8F9FC !important; }

/* ── BARRA SUPERIOR STREAMLIT ── */
header[data-testid="stHeader"] { background: #ffffff !important; border-bottom: 1px solid #E4E7F0 !important; }
[data-testid="stSidebarCollapsedControl"] { opacity: 0 !important; pointer-events: none !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E4E7F0 !important;
    box-shadow: 2px 0 12px rgba(0,0,0,0.04) !important;
}
[data-testid="stSidebarContent"] { padding: 24px 20px !important; }
[data-testid="stSidebar"] label { color: #64748B !important; }
[data-testid="stSidebar"] .stSelectbox > div > div { color: #0F172A !important; }

/* ── MÉTRICAS ── */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E4E7F0 !important;
    border-radius: 14px !important;
    padding: 20px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
    transition: all 0.2s !important;
}
[data-testid="stMetric"]:hover {
    border-color: #4F46E5 !important;
    box-shadow: 0 4px 20px rgba(79,70,229,0.1) !important;
    transform: translateY(-2px) !important;
}
[data-testid="stMetricValue"] {
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    color: #0F172A !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #94A3B8 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.78rem !important; font-weight: 600 !important; }

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    padding: 4px !important;
    gap: 2px !important;
    border: 1px solid #E4E7F0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #94A3B8 !important;
    border-radius: 9px !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: #4F46E5 !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(79,70,229,0.3) !important;
}

/* ── SELECTBOX / INPUTS ── */
.stSelectbox > div > div, .stMultiSelect > div > div {
    background: #FFFFFF !important;
    border: 1px solid #E4E7F0 !important;
    border-radius: 10px !important;
    color: #0F172A !important;
}
.stDateInput > div > div {
    background: #FFFFFF !important;
    border: 1px solid #E4E7F0 !important;
    border-radius: 10px !important;
}

/* ── BOTÓN ── */
.stButton > button {
    background: #4F46E5 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 12px rgba(79,70,229,0.25) !important;
}
.stButton > button:hover {
    background: #4338CA !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(79,70,229,0.35) !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #E4E7F0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
/* Tablas en modo claro */
[data-testid="stDataFrame"] iframe { background: #FFFFFF !important; }
.stDataFrame { background: #FFFFFF !important; }

/* Fondo homogéneo en todas las secciones */
[data-testid="stTabsContent"] { background: transparent !important; }
[data-testid="stVerticalBlock"] { background: transparent !important; }
[data-testid="stHorizontalBlock"] { background: transparent !important; }
.element-container { background: transparent !important; }
[data-testid="column"] { background: transparent !important; }

/* Multiselect modo claro */
[data-baseweb="tag"] { background: #EEF2FF !important; color: #4338CA !important; }
[data-baseweb="popover"] { background: #FFFFFF !important; }
[data-baseweb="select"] { background: #FFFFFF !important; }
[data-baseweb="menu"] { background: #FFFFFF !important; }
[data-baseweb="option"]:hover { background: #F5F3FF !important; }

/* Texto general claro */
p, span, div, label { color: #0F172A; }
.stMarkdown p { color: #0F172A !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: #F8F9FC; }
::-webkit-scrollbar-thumb { background: #C7D2FE; border-radius: 4px; }

/* ── ALERT CARDS ── */
.alert-card {
    border-radius: 12px;
    padding: 16px 20px;
    margin: 8px 0;
    transition: all 0.2s;
    border: 1px solid;
    background: #FFFFFF;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.alert-card:hover {
    transform: translateX(3px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
.alert-critical {
    border-left: 4px solid #EF4444;
    border-color: #FEE2E2;
    background: linear-gradient(135deg, #FFF5F5, #FFFFFF);
}
.alert-warning {
    border-left: 4px solid #F59E0B;
    border-color: #FEF3C7;
    background: linear-gradient(135deg, #FFFBEB, #FFFFFF);
}
.alert-success {
    border-left: 4px solid #10B981;
    border-color: #D1FAE5;
    background: linear-gradient(135deg, #F0FDF9, #FFFFFF);
}
.alert-info {
    border-left: 4px solid #4F46E5;
    border-color: #E0E7FF;
    background: linear-gradient(135deg, #F5F3FF, #FFFFFF);
}

/* ── BADGES ── */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 100px;
    font-size: 0.62rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-right: 5px;
}
.badge-red    { background: #FEE2E2; color: #DC2626; border: 1px solid #FECACA; }
.badge-amber  { background: #FEF3C7; color: #D97706; border: 1px solid #FDE68A; }
.badge-green  { background: #D1FAE5; color: #059669; border: 1px solid #A7F3D0; }
.badge-indigo { background: #E0E7FF; color: #4338CA; border: 1px solid #C7D2FE; }

.impact-num {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem;
    font-weight: 700;
    color: #4F46E5;
}

.section-title {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #94A3B8;
    margin: 24px 0 14px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #E4E7F0;
}

.divider { height: 1px; background: #E4E7F0; margin: 20px 0; }

/* ── STAT MINI ── */
.stat-mini {
    background: #FFFFFF;
    border: 1px solid #E4E7F0;
    border-radius: 10px;
    padding: 14px 16px;
    text-align: center;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 8px;
}
.stat-mini-val {
    font-size: 1.3rem;
    font-weight: 800;
    color: #0F172A;
    display: block;
    letter-spacing: -0.01em;
}
.stat-mini-lbl {
    font-size: 0.62rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94A3B8;
    margin-top: 3px;
    display: block;
}
</style>
""", unsafe_allow_html=True)


# ── DATOS ─────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    base = Path(__file__).parent / "data"
    df = pd.read_csv(base / "iltonif_dataset_modelable_v3.csv", parse_dates=["fecha"])
    return df

@st.cache_data
def generar_recomendaciones(df):
    ultimo = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    recs = []
    for _, row in ultimo.iterrows():
        pvp      = row["precio_venta"]
        coste    = row["coste_unitario"]
        comp_min = row["precio_comp_min"]
        comp_avg = row["precio_comp_avg"]
        stock    = row["stock_disponible"]
        media_7d = max(row["ventas_media_7d"], 0.1)
        cobertura = stock / media_7d

        if cobertura < 7:
            ss = "CRÍTICO"; as_ = f"Repón {int(media_7d*30)} uds — rotura en {int(cobertura)} días"
            imp_s = round(media_7d * pvp * max(0, 7 - cobertura), 0)
        elif cobertura < 15:
            ss = "REPOSICIÓN"; as_ = f"Repón {int(media_7d*30)} uds esta semana"
            imp_s = round(media_7d * pvp * 3, 0)
        elif cobertura > 45:
            ss = "EXCESO"; as_ = f"{int(cobertura)} días cobertura — considera promoción"; imp_s = 0
        else:
            ss = "OK"; as_ = "Niveles óptimos"; imp_s = 0

        dif = pvp - comp_min
        precio_min_viable = coste / 0.80
        if dif > comp_min * 0.10:
            bajada = min((dif / pvp) * 0.6, 0.20)
            pr = max(round(pvp * (1 - bajada), 2), precio_min_viable)
            sp = "PRECIO ALTO"; ap = f"Bajar {bajada*100:.1f}% → {pr:.2f}€"
            imp_p = round(media_7d * bajada * 1.5 * (pr - coste), 0)
        elif pvp / comp_avg < 0.92:
            pr = round(pvp * 1.06, 2)
            sp = "SUBIR PRECIO"; ap = f"Subir 6% → {pr:.2f}€"
            imp_p = round(media_7d * 0.06 * pvp, 0)
        elif row.get("alerta_bajada_competidor", 0) == 1:
            sp = "ALERTA COMP."; ap = "Competidor bajó >5% esta semana"; pr = pvp; imp_p = 0
        else:
            sp = "OK"; ap = "Precio competitivo"; pr = pvp; imp_p = 0

        recs.append({
            "SKU": row["sku_id"], "Producto": row["nombre_producto"],
            "Categoría": row["categoria"], "Plataforma": row["plataforma"],
            "señal_stock": ss, "accion_stock": as_,
            "señal_pricing": sp, "accion_pricing": ap,
            "Precio actual": round(pvp, 2), "Precio rec.": round(pr, 2),
            "Comp. mín.": round(comp_min, 2), "Comp. avg": round(comp_avg, 2),
            "Stock": int(stock), "Cobertura (días)": round(cobertura, 1),
            "Demanda/día": round(media_7d, 1),
            "Impacto stock €": imp_s, "Impacto pricing €": imp_p,
            "Impacto total €": imp_s + imp_p,
        })
    return pd.DataFrame(recs)


# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:4px 0 24px">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
        <div style="width:38px;height:38px;background:linear-gradient(135deg,#4F46E5,#7C3AED);border-radius:10px;display:flex;align-items:center;justify-content:center;box-shadow:0 4px 12px rgba(79,70,229,0.3)">
          <svg width="20" height="20" viewBox="0 0 44 44" fill="none">
            <circle cx="16" cy="13" r="6" fill="white"/>
            <rect x="11" y="18" width="8" height="22" rx="4" fill="white" transform="rotate(-22 15 29)"/>
          </svg>
        </div>
        <div>
          <div style="font-size:1.1rem;font-weight:800;color:#0F172A;letter-spacing:-0.01em">ILTONIF</div>
          <div style="font-size:0.6rem;font-weight:600;letter-spacing:0.15em;color:#94A3B8;text-transform:uppercase">Intelligence Platform</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:#E4E7F0;margin-bottom:20px"></div>', unsafe_allow_html=True)

    df_raw = cargar_datos()

    st.markdown('<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#94A3B8;margin-bottom:8px">Filtros</div>', unsafe_allow_html=True)
    categorias = ["Todas"] + sorted(df_raw["categoria"].unique().tolist())
    cat_sel = st.selectbox("Categoría", categorias, label_visibility="collapsed")
    plataformas = ["Todas"] + sorted(df_raw["plataforma"].unique().tolist())
    plat_sel = st.selectbox("Plataforma", plataformas, label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:#E4E7F0;margin:16px 0"></div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.65rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#94A3B8;margin-bottom:8px">Período</div>', unsafe_allow_html=True)
    fecha_max = df_raw["fecha"].max().date()
    fecha_min = df_raw["fecha"].min().date()
    rango = st.date_input("Rango", value=(fecha_max - timedelta(days=90), fecha_max),
        min_value=fecha_min, max_value=fecha_max, label_visibility="collapsed")

    st.markdown('<div style="height:1px;background:#E4E7F0;margin:16px 0"></div>', unsafe_allow_html=True)

    if st.button("⟳  Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown(f"""
    <div style="margin-top:16px;padding:14px;background:#F8F9FC;border-radius:10px;border:1px solid #E4E7F0">
      <div style="font-size:0.6rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#94A3B8;margin-bottom:8px">Estado del sistema</div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
        <div style="width:7px;height:7px;border-radius:50%;background:#10B981;box-shadow:0 0 6px rgba(16,185,129,0.5)"></div>
        <div style="font-size:0.75rem;font-weight:500;color:#0F172A">Pipeline activo</div>
      </div>
      <div style="font-size:0.68rem;color:#94A3B8;font-family:'JetBrains Mono',monospace">{datetime.now().strftime('%d/%m/%Y  %H:%M')}</div>
    </div>
    """, unsafe_allow_html=True)


# ── FILTRAR ───────────────────────────────────────────────────
df = df_raw.copy()
if cat_sel  != "Todas": df = df[df["categoria"]  == cat_sel]
if plat_sel != "Todas": df = df[df["plataforma"] == plat_sel]
if len(rango) == 2:
    df = df[(df["fecha"] >= pd.Timestamp(rango[0])) & (df["fecha"] <= pd.Timestamp(rango[1]))]

df_rec = generar_recomendaciones(df_raw)
if cat_sel  != "Todas": df_rec = df_rec[df_rec["Categoría"] == cat_sel]
if plat_sel != "Todas": df_rec = df_rec[df_rec["Plataforma"] == plat_sel]

sku_nombres = {r["sku_id"]: r["nombre_producto"]
               for _, r in df[["sku_id","nombre_producto"]].drop_duplicates().iterrows()}


# ── HEADER ────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("""
    <div style="padding:4px 0 20px">
      <div style="font-size:1.6rem;font-weight:800;color:#0F172A;letter-spacing:-0.02em;line-height:1.1">
        Panel de control
      </div>
      <div style="font-size:0.82rem;color:#94A3B8;margin-top:4px;font-weight:400">
        Pricing & Stock Intelligence · Análisis en tiempo real
      </div>
    </div>
    """, unsafe_allow_html=True)
with col_h2:
    today = datetime.now().strftime("%d %b %Y")
    st.markdown(f"""
    <div style="padding:4px 0 20px;text-align:right">
      <div style="font-size:0.65rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#94A3B8">Última actualización</div>
      <div style="font-size:0.9rem;font-weight:700;color:#4F46E5;margin-top:2px;font-family:'JetBrains Mono',monospace">{today}</div>
    </div>
    """, unsafe_allow_html=True)


# ── KPIs ──────────────────────────────────────────────────────
criticos    = (df_rec["señal_stock"]   == "CRÍTICO").sum()
reposicion  = (df_rec["señal_stock"]   == "REPOSICIÓN").sum()
precio_alto = (df_rec["señal_pricing"] == "PRECIO ALTO").sum()
oportunidad = (df_rec["señal_pricing"] == "SUBIR PRECIO").sum()
impacto     = df_rec["Impacto total €"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("🔴  Stock Crítico",  f"{criticos} SKUs",    delta="Acción urgente", delta_color="inverse")
with c2: st.metric("🟡  Reposición",     f"{reposicion} SKUs",  delta="Esta semana")
with c3: st.metric("💸  Precio Alto",    f"{precio_alto} SKUs", delta="vs competencia", delta_color="inverse")
with c4: st.metric("📈  Oportunidad",    f"{oportunidad} SKUs", delta="Subida posible")
with c5: st.metric("💶  Impacto Total",  f"{impacto:,.0f}€",    delta="Estimado hoy")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ── TABS ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🚨  Alertas del día",
    "📊  Demanda por SKU",
    "💰  Pricing",
    "📦  Stock"
])


# ══ TAB 1 — ALERTAS ══════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown('<div class="section-title">Recomendaciones accionables</div>', unsafe_allow_html=True)

        PRIO = {"CRÍTICO":0,"PRECIO ALTO":1,"REPOSICIÓN":2,"SUBIR PRECIO":3,"ALERTA COMP.":4,"EXCESO":5,"OK":99}
        df_rec["_prio"] = df_rec["señal_stock"].map(PRIO).fillna(99)
        df_sorted = df_rec[df_rec["_prio"] < 99].sort_values(["_prio","Impacto total €"], ascending=[True,False])

        for _, row in df_sorted.iterrows():
            ss = row["señal_stock"]
            sp = row["señal_pricing"]
            imp = row["Impacto total €"]

            if ss == "CRÍTICO":
                css = "alert-critical"
                badge_s = '<span class="badge badge-red">⬤ CRÍTICO</span>'
            elif ss == "REPOSICIÓN":
                css = "alert-warning"
                badge_s = '<span class="badge badge-amber">↻ REPOSICIÓN</span>'
            elif ss == "EXCESO":
                css = "alert-info"
                badge_s = '<span class="badge badge-indigo">↓ EXCESO</span>'
            else:
                css = "alert-success"
                badge_s = '<span class="badge badge-green">✓ OK</span>'

            if sp == "PRECIO ALTO":
                badge_p = '<span class="badge badge-red">↓ PRECIO ALTO</span>'
            elif sp == "SUBIR PRECIO":
                badge_p = '<span class="badge badge-green">↑ SUBIR PRECIO</span>'
            elif sp == "ALERTA COMP.":
                badge_p = '<span class="badge badge-amber">⚡ ALERTA COMP.</span>'
            else:
                badge_p = '<span class="badge badge-indigo">✓ PRECIO OK</span>'

            imp_html = f'<span class="impact-num">+{imp:,.0f}€</span>' if imp > 0 else ""

            st.markdown(f"""
            <div class="alert-card {css}">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:10px">
                <div>
                  <div style="font-weight:700;font-size:0.92rem;color:#0F172A;margin-bottom:2px">{row['Producto']}</div>
                  <div style="font-size:0.72rem;color:#94A3B8">{row['Categoría']} &nbsp;·&nbsp; {row['Plataforma']}</div>
                </div>
                <div style="display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end">{badge_s}{badge_p}</div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">
                <div style="font-size:0.78rem;color:#64748B">📦 {row['accion_stock']}</div>
                <div style="font-size:0.78rem;color:#64748B">💰 {row['accion_pricing']}</div>
              </div>
              <div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;border-top:1px solid rgba(0,0,0,0.04);padding-top:8px">
                <span style="font-size:0.72rem;color:#94A3B8">Precio: <b style="color:#0F172A">{row['Precio actual']}€</b></span>
                <span style="font-size:0.72rem;color:#94A3B8">Comp.mín: <b style="color:#0F172A">{row['Comp. mín.']}€</b></span>
                <span style="font-size:0.72rem;color:#94A3B8">Stock: <b style="color:#0F172A">{row['Stock']} uds</b></span>
                <span style="font-size:0.72rem;color:#94A3B8">Cobertura: <b style="color:#0F172A">{row['Cobertura (días)']} días</b></span>
                {('<span>' + imp_html + ' impacto estimado</span>') if imp_html else ''}
              </div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="section-title">Resumen ejecutivo</div>', unsafe_allow_html=True)

        total_skus     = len(df_rec)
        skus_ok_stock  = (df_rec["señal_stock"]   == "OK").sum()
        skus_ok_price  = (df_rec["señal_pricing"]  == "OK").sum()
        cobertura_avg  = df_rec["Cobertura (días)"].mean()

        for label, val, color in [
            ("SKUs analizados",     total_skus,                   "#4F46E5"),
            ("Stock saludable",     f"{skus_ok_stock}/{total_skus}", "#10B981"),
            ("Precio competitivo",  f"{skus_ok_price}/{total_skus}", "#10B981"),
            ("Cobertura media",     f"{cobertura_avg:.0f} días",     "#F59E0B"),
        ]:
            st.markdown(f"""
            <div class="stat-mini">
              <span class="stat-mini-val" style="color:{color}">{val}</span>
              <span class="stat-mini-lbl">{label}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:20px">Distribución stock</div>', unsafe_allow_html=True)
        COLORS_S = {"CRÍTICO":"#EF4444","REPOSICIÓN":"#F59E0B","EXCESO":"#6366F1","OK":"#10B981"}
        cs = df_rec["señal_stock"].value_counts().reset_index()
        cs.columns = ["Señal","N"]
        fig_d1 = px.pie(cs, values="N", names="Señal", hole=0.68,
                        color="Señal", color_discrete_map=COLORS_S)
        fig_d1.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#64748B", height=210, margin=dict(t=0,b=0,l=0,r=0),
            legend=dict(font=dict(color="#64748B",size=11), orientation="h", y=-0.1))
        fig_d1.update_traces(textfont_color="white", textfont_size=11)
        st.plotly_chart(fig_d1, use_container_width=True)

        st.markdown('<div class="section-title">Distribución pricing</div>', unsafe_allow_html=True)
        COLORS_P = {"PRECIO ALTO":"#EF4444","SUBIR PRECIO":"#10B981","ALERTA COMP.":"#F59E0B","OK":"#6366F1"}
        cp = df_rec["señal_pricing"].value_counts().reset_index()
        cp.columns = ["Señal","N"]
        fig_d2 = px.pie(cp, values="N", names="Señal", hole=0.68,
                        color="Señal", color_discrete_map=COLORS_P)
        fig_d2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#64748B", height=210, margin=dict(t=0,b=0,l=0,r=0),
            legend=dict(font=dict(color="#64748B",size=11), orientation="h", y=-0.1))
        fig_d2.update_traces(textfont_color="white", textfont_size=11)
        st.plotly_chart(fig_d2, use_container_width=True)


# ══ TAB 2 — DEMANDA ══════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-title">Evolución de demanda por SKU</div>', unsafe_allow_html=True)
    skus = sorted(df["sku_id"].unique())
    sku_sel = st.multiselect("Selecciona SKUs", options=skus, default=skus[:4],
                             format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
    if sku_sel:
        df_plot = df[df["sku_id"].isin(sku_sel)].copy()
        df_agg  = df_plot.groupby(["fecha","sku_id","nombre_producto"])["unidades_vendidas"].sum().reset_index()
        PALETTE = ["#4F46E5","#10B981","#F59E0B","#EF4444","#7C3AED","#06B6D4"]
        fig_line = go.Figure()
        for i, sku in enumerate(sku_sel):
            df_s = df_agg[df_agg["sku_id"] == sku]
            fig_line.add_trace(go.Scatter(
                x=df_s["fecha"], y=df_s["unidades_vendidas"],
                name=sku_nombres.get(sku, sku),
                line=dict(color=PALETTE[i % len(PALETTE)], width=2.5),
                mode="lines"))
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFF",
            font_color="#64748B", height=380,
            legend=dict(orientation="h", y=-0.25, font=dict(color="#64748B", size=11)),
            xaxis=dict(gridcolor="#F1F3F9", showline=False, tickfont=dict(size=11)),
            yaxis=dict(gridcolor="#F1F3F9", showline=False, title="Unidades", tickfont=dict(size=11)),
            hovermode="x unified", margin=dict(t=10,b=10))
        st.plotly_chart(fig_line, use_container_width=True)

        col_h, col_e = st.columns(2, gap="large")
        with col_h:
            st.markdown('<div class="section-title">Estacionalidad</div>', unsafe_allow_html=True)
            sku_h = st.selectbox("SKU heatmap", options=sku_sel,
                                 format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
            df_heat = df[df["sku_id"] == sku_h].copy()
            dias   = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
            meses  = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
            pivot  = df_heat.groupby(["mes","dia_semana"])["unidades_vendidas"].mean().unstack(fill_value=0)
            pivot.index   = [meses[i-1] for i in pivot.index]
            pivot.columns = [dias[i]    for i in pivot.columns]
            fig_h = px.imshow(pivot,
                              color_continuous_scale=[[0,"#EEF2FF"],[0.5,"#818CF8"],[1,"#3730A3"]],
                              labels=dict(color="Uds/día"))
            fig_h.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="#64748B",
                                height=300, margin=dict(t=10,b=10))
            st.plotly_chart(fig_h, use_container_width=True)

        with col_e:
            st.markdown('<div class="section-title">Métricas por producto</div>', unsafe_allow_html=True)
            res = df_plot.groupby(["sku_id","nombre_producto"]).agg(
                Ventas=("unidades_vendidas","sum"),
                Media=("unidades_vendidas","mean"),
                Ingreso=("ingreso_estimado","sum"),
                Margen=("margen_estimado_eur","sum"),
            ).reset_index().round(1)
            res.columns = ["SKU","Producto","Ventas","Media/día","Ingreso €","Margen €"]
            st.dataframe(res, use_container_width=True, hide_index=True, height=300)


# ══ TAB 3 — PRICING ══════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-title">Comparativa de precios vs competencia</div>', unsafe_allow_html=True)
    ultimo_df = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    productos_list = ultimo_df["nombre_producto"].tolist()
    comp_cols = [c for c in ultimo_df.columns if c.startswith("precio_") and c not in
                 ["precio_venta","precio_comp_min","precio_comp_avg","precio_comp_max","precio_mercado_ref","precio_min_viable"]]
    nombre_comp_map = {
        "precio_decathlon": "Decathlon", "precio_trailzone": "TrailZone",
        "precio_outdoorpro": "OutdoorPro", "precio_ortoweb": "Ortoweb",
        "precio_medicalexpo": "Medicalexpo",
    }
    PALETTE_P = ["#4F46E5","#EF4444","#F59E0B","#10B981"]
    fig_bar = go.Figure()
    for i, (col, name) in enumerate(zip(
        ["precio_venta"] + comp_cols,
        ["Tu precio"] + [nombre_comp_map.get(c, c.replace("precio_","").replace("_"," ").title()) for c in comp_cols]
    )):
        fig_bar.add_trace(go.Bar(name=name, x=productos_list, y=ultimo_df[col],
                                 marker_color=PALETTE_P[i%len(PALETTE_P)], marker_line_width=0))
    fig_bar.update_layout(
        barmode="group", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFF",
        font_color="#64748B", height=400, xaxis_tickangle=-30,
        legend=dict(orientation="h", y=-0.45, font=dict(color="#64748B")),
        xaxis=dict(gridcolor="#F1F3F9", tickfont=dict(size=10)),
        yaxis=dict(gridcolor="#F1F3F9", title="Precio (€)"),
        bargap=0.2, bargroupgap=0.05, margin=dict(t=10,b=10))
    st.plotly_chart(fig_bar, use_container_width=True)

    col_ev, col_tabla = st.columns([1.2, 1], gap="large")
    with col_ev:
        st.markdown('<div class="section-title">Evolución precio vs competencia</div>', unsafe_allow_html=True)
        sku_p = st.selectbox("Producto", options=sorted(df["sku_id"].unique()),
                             format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}", key="p_sku")
        df_sku = df[df["sku_id"] == sku_p]
        fig_ev = go.Figure()
        ev_cols = [("precio_venta","Tu precio","#4F46E5","solid",2.5)] + \
                  [(c, nombre_comp_map.get(c, c.replace("precio_","").title()),
                    PALETTE_P[(i+1)%len(PALETTE_P)], "dot", 1.5)
                   for i,c in enumerate(comp_cols) if c in df_sku.columns]
        for col, name, color, dash, width in ev_cols:
            if col in df_sku.columns:
                fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku[col], name=name,
                    line=dict(color=color, width=width, dash=dash)))
        fig_ev.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFF",
            font_color="#64748B", height=320,
            legend=dict(orientation="h", y=-0.35, font=dict(color="#64748B",size=11)),
            xaxis=dict(gridcolor="#F1F3F9"),
            yaxis=dict(gridcolor="#F1F3F9", title="Precio (€)"),
            margin=dict(t=10,b=10))
        st.plotly_chart(fig_ev, use_container_width=True)

    with col_tabla:
        st.markdown('<div class="section-title">Recomendaciones de pricing</div>', unsafe_allow_html=True)
        cols_p = ["Producto","Categoría","señal_pricing","accion_pricing","Precio actual","Precio rec.","Comp. mín.","Impacto pricing €"]
        df_tp = df_rec[cols_p].copy()
        df_tp.columns = ["Producto","Categoría","Señal","Acción","Precio actual €","Precio rec. €","Comp. mín. €","Impacto €"]
        def color_pricing(val):
            m = {"PRECIO ALTO":"background-color:#FEE2E2;color:#DC2626",
                 "SUBIR PRECIO":"background-color:#D1FAE5;color:#059669",
                 "ALERTA COMP.":"background-color:#FEF3C7;color:#D97706"}
            return m.get(val,"background-color:#EEF2FF;color:#4338CA")
        st.dataframe(df_tp.style.map(color_pricing, subset=["Señal"]),
                     use_container_width=True, hide_index=True, height=380)


# ══ TAB 4 — STOCK ════════════════════════════════════════════
with tab4:
    col_s1, col_s2 = st.columns(2, gap="large")

    with col_s1:
        st.markdown('<div class="section-title">Stock disponible por SKU</div>', unsafe_allow_html=True)
        ultimo_s = df.sort_values("fecha").groupby("sku_id").last().reset_index()
        ultimo_s_sorted = ultimo_s.sort_values("stock_disponible", ascending=True)
        colores_bar = []
        for _, r in ultimo_s_sorted.iterrows():
            cob = r["stock_disponible"] / max(r["ventas_media_7d"], 0.1)
            if cob < 7:    colores_bar.append("#EF4444")
            elif cob < 15: colores_bar.append("#F59E0B")
            elif cob > 45: colores_bar.append("#6366F1")
            else:          colores_bar.append("#10B981")
        fig_stock = go.Figure()
        fig_stock.add_trace(go.Bar(
            x=ultimo_s_sorted["stock_disponible"], y=ultimo_s_sorted["nombre_producto"],
            orientation="h", marker_color=colores_bar, marker_line_width=0,
            text=ultimo_s_sorted["stock_disponible"].astype(str)+" uds",
            textposition="outside", textfont=dict(color="#64748B", size=10)))
        fig_stock.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFF",
            font_color="#64748B", height=480, xaxis_title="Unidades en stock",
            xaxis=dict(gridcolor="#F1F3F9"),
            margin=dict(t=10,b=10,l=10,r=60))
        st.plotly_chart(fig_stock, use_container_width=True)

    with col_s2:
        st.markdown('<div class="section-title">Días de cobertura por SKU</div>', unsafe_allow_html=True)
        df_cob = df_rec.sort_values("Cobertura (días)")
        colores_cob = ["#EF4444" if c<7 else "#F59E0B" if c<15 else "#6366F1" if c>45 else "#10B981"
                       for c in df_cob["Cobertura (días)"].tolist()]
        fig_cob = go.Figure()
        fig_cob.add_trace(go.Bar(
            x=df_cob["Cobertura (días)"], y=df_cob["Producto"],
            orientation="h", marker_color=colores_cob, marker_line_width=0,
            text=[f"{c} días" for c in df_cob["Cobertura (días)"].tolist()],
            textposition="outside", textfont=dict(color="#64748B", size=10)))
        for x_val, color, label in [(7,"#EF4444","Crítico"),(15,"#F59E0B","Riesgo"),(45,"#6366F1","Exceso")]:
            fig_cob.add_vline(x=x_val, line_dash="dash", line_color=color,
                              line_width=1.5, opacity=0.6,
                              annotation_text=label, annotation_font_color=color,
                              annotation_font_size=10)
        fig_cob.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#FAFBFF",
            font_color="#64748B", height=480, xaxis_title="Días",
            xaxis=dict(gridcolor="#F1F3F9"),
            margin=dict(t=10,b=10,l=10,r=60))
        st.plotly_chart(fig_cob, use_container_width=True)

    st.markdown('<div class="section-title">Tabla de alertas de stock</div>', unsafe_allow_html=True)
    cols_s = ["Producto","Categoría","señal_stock","accion_stock","Stock","Cobertura (días)","Demanda/día","Impacto stock €"]
    df_ts = df_rec[cols_s].copy()
    df_ts.columns = ["Producto","Categoría","Señal","Acción","Stock uds","Cobertura días","Demanda/día","Impacto €"]
    def color_stock(val):
        m = {"CRÍTICO":"background-color:#FEE2E2;color:#DC2626",
             "REPOSICIÓN":"background-color:#FEF3C7;color:#D97706",
             "EXCESO":"background-color:#EEF2FF;color:#4338CA"}
        return m.get(val,"background-color:#D1FAE5;color:#059669")
    st.dataframe(df_ts.style.map(color_stock, subset=["Señal"]),
                 use_container_width=True, hide_index=True, height=380)


# ── FOOTER ────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:20px 0 8px;border-top:1px solid #E4E7F0;margin-top:16px">
  <span style="font-family:'JetBrains Mono',monospace;font-size:0.62rem;color:#CBD5E1;letter-spacing:0.15em">
    ILTONIF © 2025 &nbsp;·&nbsp; INTELLIGENCE PLATFORM &nbsp;·&nbsp; PRICING & STOCK AI
  </span>
</div>
""", unsafe_allow_html=True)
