import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta
import decision_engine as de
 
try:
    import posthog
    _POSTHOG_OK = True
except ImportError:
    _POSTHOG_OK = False
 
st.set_page_config(
    page_title="ILTONIF — Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# ── AUTENTICACIÓN ────────────────────────────────────────────
def check_password():
    """Devuelve True si el usuario ya introdujo la contraseña correcta."""
    def password_entered():
        if st.session_state["password"] == st.secrets["dashboard_password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False
 
    if st.session_state.get("password_correct", False):
        return True
 
    # Pantalla de acceso con identidad de marca (solo presentación;
    # la lógica de autenticación es idéntica a la de siempre).
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Outfit:wght@300;400;600&display=swap');
    #MainMenu, footer { visibility: hidden; }
    header[data-testid="stHeader"] { background: transparent !important; }
    .stApp {
        background:
          radial-gradient(900px 420px at 50% -10%, rgba(29,106,245,0.22), transparent 60%),
          radial-gradient(700px 380px at 80% 100%, rgba(34,211,238,0.08), transparent 55%),
          #05070f !important;
    }
    .login-card { text-align:center; padding: 90px 12px 10px; font-family:'Outfit',sans-serif; }
    .login-card .brand {
        font-family:'Space Grotesk',sans-serif; font-size:2.5rem; font-weight:700;
        letter-spacing:.1em; color:#f8fafc; margin-top:20px; line-height:1.1;
    }
    .login-card .brand span {
        background:linear-gradient(90deg,#4d9aff,#22d3ee);
        -webkit-background-clip:text; background-clip:text; color:transparent;
    }
    .login-card .sub {
        color:#64748b; font-size:.72rem; letter-spacing:.3em;
        text-transform:uppercase; margin-top:8px;
    }
    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(148,163,184,0.2) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 14px 16px !important;
        text-align: center !important;
        letter-spacing: .25em !important;
    }
    .stTextInput input:focus {
        border-color: #1d6af5 !important;
        box-shadow: 0 0 0 3px rgba(29,106,245,0.25) !important;
    }
    .login-note {
        text-align:center; color:#475569; font-size:.72rem;
        margin-top:20px; letter-spacing:.08em;
    }
    </style>
    <div class="login-card">
      <svg width="66" height="66" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" style="filter:drop-shadow(0 10px 34px rgba(29,106,245,0.5))">
        <rect width="44" height="44" rx="11" fill="#1d6af5"/>
        <circle cx="16" cy="13" r="6" fill="white"/>
        <rect x="11" y="18" width="8" height="22" rx="4" fill="white" transform="rotate(-22 15 29)"/>
      </svg>
      <div class="brand">ILTONIF <span>INTELLIGENCE</span></div>
      <div class="sub">Pricing · Stock · Competencia</div>
    </div>
    """, unsafe_allow_html=True)
 
    _izq, centro, _der = st.columns([1, 1.1, 1])
    with centro:
        st.text_input(
            "Contraseña", type="password",
            on_change=password_entered, key="password",
            placeholder="Contraseña de acceso",
            label_visibility="collapsed"
        )
        if "password_correct" in st.session_state and not st.session_state["password_correct"]:
            st.error("Contraseña incorrecta")
        st.markdown(
            '<div class="login-note">🔒 Acceso privado · Datos actualizados a diario desde tu tienda</div>',
            unsafe_allow_html=True
        )
    return False
 
if not check_password():
    st.stop()
 
# ── TRACKING DE PRODUCTO ─────────────────────────────────────
if _POSTHOG_OK and "posthog_api_key" in st.secrets:
    posthog.api_key = st.secrets["posthog_api_key"]
    posthog.host = st.secrets.get("posthog_host", "https://eu.i.posthog.com")
 
def registrar_evento(nombre_evento: str, propiedades: dict):
    """Envía un evento de producto. No lanza excepción si falla, para que
    un problema de tracking nunca rompa el dashboard."""
    if not (_POSTHOG_OK and "posthog_api_key" in st.secrets):
        return
    try:
        posthog.capture(
            distinct_id="pedro-beta",
            event=nombre_evento,
            properties=propiedades,
        )
    except Exception:
        pass
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
 
* { font-family: 'Outfit', sans-serif !important; }
 
/* CHROME DE STREAMLIT */
#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }
 
/* FONDO — aurora corporativa sutil */
.stApp {
    background:
      radial-gradient(1100px 480px at 15% -8%, rgba(29,106,245,0.16), transparent 60%),
      radial-gradient(900px 420px at 85% -5%, rgba(34,211,238,0.10), transparent 55%),
      radial-gradient(760px 520px at 50% 112%, rgba(29,106,245,0.07), transparent 60%),
      #05070f !important;
}
.main { background: transparent !important; }
.block-container { padding: 0.8rem 2.2rem 2rem !important; max-width: 1500px !important; }
 
/* SIDEBAR */
[data-testid="stSidebar"] {
    background: rgba(7,11,22,0.94) !important;
    border-right: 1px solid rgba(148,163,184,0.09) !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebarContent"] { padding: 20px 16px !important; }
 
/* MÉTRICAS — tarjetas de cristal con filo luminoso */
[data-testid="stMetric"] {
    background: linear-gradient(160deg, rgba(255,255,255,0.05), rgba(255,255,255,0.015)) !important;
    border: 1px solid rgba(148,163,184,0.13) !important;
    border-radius: 18px !important;
    padding: 22px 22px 18px !important;
    position: relative !important;
    overflow: hidden !important;
    transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease !important;
}
[data-testid="stMetric"]::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #1d6af5, #22d3ee 60%, transparent);
    opacity: .85;
}
[data-testid="stMetric"]:hover {
    transform: translateY(-4px) !important;
    border-color: rgba(29,106,245,0.45) !important;
    box-shadow: 0 18px 50px rgba(29,106,245,0.18) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2.3rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #f8fafc !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: #64748b !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }
 
/* TABS — píldoras */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.03) !important;
    border-radius: 14px !important;
    padding: 5px !important;
    gap: 4px !important;
    border: 1px solid rgba(148,163,184,0.12) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #64748b !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 22px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d6af5, #0ea5e9) !important;
    color: white !important;
    box-shadow: 0 6px 22px rgba(29,106,245,0.45) !important;
}
 
/* SELECTBOX / INPUTS */
.stSelectbox > div > div, .stDateInput > div > div, .stMultiSelect > div > div {
    background: rgba(255,255,255,0.035) !important;
    border: 1px solid rgba(148,163,184,0.16) !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: rgba(29,106,245,0.18) !important;
    border: 1px solid rgba(29,106,245,0.35) !important;
    border-radius: 8px !important;
}
 
/* BOTONES */
.stButton > button {
    background: linear-gradient(135deg, #1d6af5, #0ea5e9) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.78rem !important;
    transition: all 0.25s !important;
    box-shadow: 0 4px 18px rgba(29,106,245,0.28) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 32px rgba(29,106,245,0.5) !important;
}
 
/* DATAFRAME */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(148,163,184,0.12) !important;
    border-radius: 14px !important;
    overflow: hidden !important;
}
 
/* CARDS DE ALERTAS — cristal con acento lateral */
.alert-critico, .alert-warning, .alert-info, .alert-ok {
    background: linear-gradient(160deg, rgba(255,255,255,0.04), rgba(255,255,255,0.012));
    border: 1px solid rgba(148,163,184,0.12);
    border-radius: 16px;
    padding: 18px 24px;
    margin: 10px 0;
    transition: all 0.25s;
    position: relative;
    overflow: hidden;
}
.alert-critico { border-left: 3px solid #fb7185; }
.alert-critico:hover { border-color: rgba(251,113,133,0.55); box-shadow: 0 12px 36px rgba(251,113,133,0.12); transform: translateY(-2px); }
.alert-warning { border-left: 3px solid #fbbf24; }
.alert-warning:hover { border-color: rgba(251,191,36,0.55); box-shadow: 0 12px 36px rgba(251,191,36,0.10); transform: translateY(-2px); }
.alert-info { border-left: 3px solid #38bdf8; }
.alert-info:hover { border-color: rgba(56,189,248,0.55); box-shadow: 0 12px 36px rgba(56,189,248,0.10); transform: translateY(-2px); }
.alert-ok { border-left: 3px solid #34d399; }
.alert-ok:hover { border-color: rgba(52,211,153,0.55); transform: translateY(-2px); }
 
.tag {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 100px;
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-right: 8px;
}
.tag-red   { background: rgba(251,113,133,0.14); color: #fb7185; border: 1px solid rgba(251,113,133,0.32); }
.tag-amber { background: rgba(251,191,36,0.13); color: #fbbf24; border: 1px solid rgba(251,191,36,0.3); }
.tag-blue  { background: rgba(56,189,248,0.13); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3); }
.tag-green { background: rgba(52,211,153,0.13); color: #34d399; border: 1px solid rgba(52,211,153,0.3); }
 
.impact-val {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.92rem;
    font-weight: 700;
    background: linear-gradient(90deg, #22d3ee, #4d9aff);
    -webkit-background-clip: text; background-clip: text; color: transparent;
    letter-spacing: 0.04em;
}
 
.section-header {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.01em;
    color: #f1f5f9;
    margin: 26px 0 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.section-header::before {
    content: '';
    width: 4px; height: 22px; border-radius: 3px;
    background: linear-gradient(180deg, #1d6af5, #22d3ee);
    box-shadow: 0 0 14px rgba(29,106,245,0.6);
}
 
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(29,106,245,0.35), rgba(34,211,238,0.25), transparent);
    margin: 30px 0;
}
 
/* HERO — cabecera principal */
.hero {
    background: linear-gradient(160deg, rgba(255,255,255,0.045), rgba(255,255,255,0.012));
    border: 1px solid rgba(148,163,184,0.13);
    border-radius: 22px;
    padding: 26px 32px;
    margin: 6px 0 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 18px;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, #1d6af5, #22d3ee 55%, transparent);
}
.hero-title {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 2.2rem; font-weight: 700; line-height: 1.05;
    letter-spacing: 0.06em; color: #f8fafc;
}
.hero-title span {
    background: linear-gradient(90deg, #4d9aff, #22d3ee);
    -webkit-background-clip: text; background-clip: text; color: transparent;
}
.hero-sub {
    font-size: 0.78rem; letter-spacing: 0.22em; text-transform: uppercase;
    color: #64748b; margin-top: 6px;
}
.hero-chips { display: flex; gap: 10px; flex-wrap: wrap; }
.hero-chip {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(148,163,184,0.15);
    border-radius: 100px;
    padding: 7px 16px;
    font-size: 0.75rem; font-weight: 600; color: #cbd5e1;
    display: flex; align-items: center; gap: 8px;
}
.hero-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #34d399; box-shadow: 0 0 10px rgba(52,211,153,0.9);
    animation: pulso 2.2s infinite;
}
@keyframes pulso { 0%,100% { opacity: 1; } 50% { opacity: 0.35; } }
 
/* SCROLLBAR */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(29,106,245,0.4); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)
 
 
# ── DATOS ──────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    base = Path(__file__).parent / "data"
    df = pd.read_csv(base / "iltonif_dataset_modelable_v3.csv", parse_dates=["fecha"])
    return df
 
# Mapa de las señales de stock que devuelve decision_engine (sin acentos,
# por diseño: evita problemas de encoding en el módulo de lógica pura) a
# las etiquetas con acentos que ya usa toda la interfaz de este dashboard.
_MAPA_SENAL_STOCK = {
    "CRITICO": "CRÍTICO",
    "REPOSICION": "REPOSICIÓN",
    "EXCESO": "EXCESO",
    "OK": "OK",
}
 
@st.cache_data
def generar_recomendaciones(df):
    """Genera las recomendaciones por SKU usando decision_engine.evaluar_sku,
    para que la lógica de negocio viva en un único sitio (testeado con
    pytest) en vez de estar duplicada aquí y en el Tab 4."""
    ultimo = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    recs = []
    for _, row in ultimo.iterrows():
        r = de.evaluar_sku(row.to_dict())
        media_7d = max(row["ventas_media_7d"], 0.1)
 
        recs.append({
            "SKU": row["sku_id"], "Producto": row["nombre_producto"],
            "Categoría": row["categoria"], "Plataforma": row["plataforma"],
            "señal_stock": _MAPA_SENAL_STOCK[r["senal_stock"]],
            "accion_stock": r["accion_stock"],
            "señal_pricing": r["senal_pricing"], "accion_pricing": r["accion_pricing"],
            "Precio actual": round(row["precio_venta"], 2), "Precio rec.": round(r["precio_rec"], 2),
            "Comp. mín.": round(row["precio_comp_min"], 2), "Comp. avg": round(row["precio_comp_avg"], 2),
            "Stock": int(row["stock_disponible"]), "Cobertura (días)": r["cobertura_dias"],
            "Demanda/día": round(media_7d, 1),
            "Impacto stock €": r["impacto_stock"],
            "Impacto pricing €": r["impacto_pricing"],
            "Impacto total €": r["impacto_total"],
        })
    return pd.DataFrame(recs)
 
 
# ── SIDEBAR ────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('''
    <div style="padding:12px 0 20px">
      <svg width="40" height="40" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" style="display:block">
        <rect width="44" height="44" rx="10" fill="#1d6af5"/>
        <circle cx="16" cy="13" r="6" fill="white"/>
        <rect x="11" y="18" width="8" height="22" rx="4" fill="white" transform="rotate(-22 15 29)"/>
      </svg>
      <div style="margin-top:10px">
        <div style="font-family:\'Space Grotesk\',sans-serif;font-weight:700;font-size:1.3rem;letter-spacing:0.12em;color:#f8fafc">ILTONIF</div>
        <div style="font-size:0.62rem;letter-spacing:0.22em;color:#4d9aff;text-transform:uppercase;margin-top:3px">Intelligence Platform</div>
      </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown("---")
 
    df_raw = cargar_datos()
    st.markdown('<div style="font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;color:#475569;margin-bottom:8px">Filtros</div>', unsafe_allow_html=True)
 
    categorias = ["Todas"] + sorted(df_raw["categoria"].unique().tolist())
    cat_sel = st.selectbox("Categoría", categorias, label_visibility="collapsed")
    plataformas = ["Todas"] + sorted(df_raw["plataforma"].unique().tolist())
    plat_sel = st.selectbox("Plataforma", plataformas, label_visibility="collapsed")
 
    st.markdown("---")
    fecha_max = df_raw["fecha"].max().date()
    fecha_min = df_raw["fecha"].min().date()
    rango = st.date_input("Rango histórico",
        value=(fecha_max - timedelta(days=90), fecha_max),
        min_value=fecha_min, max_value=fecha_max)
 
    st.markdown("---")
    st.markdown('<div style="font-size:0.7rem;letter-spacing:0.15em;text-transform:uppercase;color:#475569;margin-bottom:8px">Pipeline</div>', unsafe_allow_html=True)
    if st.button("⟳  Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown(f'<div style="font-size:0.68rem;color:#334155;margin-top:8px">Último update: {datetime.now().strftime("%d/%m/%Y %H:%M")}</div>', unsafe_allow_html=True)
 
 
# ── FILTRAR ────────────────────────────────────────────────────
df = df_raw.copy()
if cat_sel  != "Todas": df = df[df["categoria"]  == cat_sel]
if plat_sel != "Todas": df = df[df["plataforma"] == plat_sel]
if len(rango) == 2:
    df = df[(df["fecha"] >= pd.Timestamp(rango[0])) & (df["fecha"] <= pd.Timestamp(rango[1]))]
 
df_rec = generar_recomendaciones(df_raw)
if cat_sel  != "Todas": df_rec = df_rec[df_rec["Categoría"]  == cat_sel]
if plat_sel != "Todas": df_rec = df_rec[df_rec["Plataforma"] == plat_sel]
 
sku_nombres = {r["sku_id"]: r["nombre_producto"]
               for _, r in df[["sku_id","nombre_producto"]].drop_duplicates().iterrows()}
 
 
# ── HEADER PRINCIPAL ───────────────────────────────────────────
n_skus_total = df_raw["sku_id"].nunique()
fecha_dato   = df_raw["fecha"].max().strftime("%d/%m/%Y")
st.markdown(f'''
<div class="hero">
  <div style="display:flex;align-items:center;gap:20px">
    <svg width="58" height="58" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg" style="filter:drop-shadow(0 8px 26px rgba(29,106,245,0.5))">
      <rect width="44" height="44" rx="11" fill="#1d6af5"/>
      <circle cx="16" cy="13" r="6" fill="white"/>
      <rect x="11" y="18" width="8" height="22" rx="4" fill="white" transform="rotate(-22 15 29)"/>
    </svg>
    <div>
      <div class="hero-title">ILTONIF <span>INTELLIGENCE</span></div>
      <div class="hero-sub">Pricing & Stock AI · Decisiones con datos, cada día</div>
    </div>
  </div>
  <div class="hero-chips">
    <div class="hero-chip"><span class="hero-dot"></span>Datos al día · {fecha_dato}</div>
    <div class="hero-chip">📦 {n_skus_total} SKUs monitorizados</div>
    <div class="hero-chip">🛰️ 3 competidores vigilados</div>
  </div>
</div>
''', unsafe_allow_html=True)
 
 
# ── KPIs ───────────────────────────────────────────────────────
criticos    = (df_rec["señal_stock"]   == "CRÍTICO").sum()
reposicion  = (df_rec["señal_stock"]   == "REPOSICIÓN").sum()
precio_alto = (df_rec["señal_pricing"] == "PRECIO ALTO").sum()
oportunidad = (df_rec["señal_pricing"] == "SUBIR PRECIO").sum()
impacto     = df_rec["Impacto total €"].sum()
 
col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("🔴  STOCK CRÍTICO",  f"{criticos} SKUs",    delta=f"−{criticos} requieren acción", delta_color="inverse")
with col2: st.metric("🟠  REPOSICIÓN",     f"{reposicion} SKUs",  delta="↑ Esta semana")
with col3: st.metric("💰  PRECIO ALTO",    f"{precio_alto} SKUs", delta="↑ vs competencia", delta_color="inverse")
with col4: st.metric("📈  OPORTUNIDAD",    f"{oportunidad} SKUs", delta="↑ Subida posible")
with col5: st.metric("💶  IMPACTO TOTAL",  f"{impacto:,.0f}€",    delta="↑ Estimado hoy")
 
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
 
 
# ── TABS ───────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🚨  ALERTAS DEL DÍA",
    "📊  DEMANDA POR SKU",
    "💰  PRICING",
    "📦  STOCK"
])
 
 
# ══ TAB 1: ALERTAS ════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">⚡ Recomendaciones accionables de hoy</div>', unsafe_allow_html=True)
 
    PRIO = {"CRÍTICO":0,"PRECIO ALTO":1,"REPOSICIÓN":2,"SUBIR PRECIO":3,"ALERTA COMP.":4,"EXCESO":5,"OK":99}
    df_rec["prio"] = df_rec["señal_stock"].map(PRIO).fillna(99)
    df_sorted = df_rec[df_rec["prio"] < 99].sort_values("prio")
 
    for _, row in df_sorted.iterrows():
        ss = row["señal_stock"]
        sp = row["señal_pricing"]
        imp = row["Impacto total €"]
 
        if ss == "CRÍTICO":
            css = "alert-critico"
            badge_s = '<span class="tag tag-red">⚠ CRÍTICO</span>'
        elif ss == "REPOSICIÓN":
            css = "alert-warning"
            badge_s = '<span class="tag tag-amber">↻ REPOSICIÓN</span>'
        elif ss == "EXCESO":
            css = "alert-info"
            badge_s = '<span class="tag tag-blue">↓ EXCESO</span>'
        else:
            css = "alert-ok"
            badge_s = '<span class="tag tag-green">✓ OK</span>'
 
        if sp == "PRECIO ALTO":
            badge_p = '<span class="tag tag-red">↓ PRECIO ALTO</span>'
        elif sp == "SUBIR PRECIO":
            badge_p = '<span class="tag tag-green">↑ SUBIR PRECIO</span>'
        elif sp == "ALERTA COMP.":
            badge_p = '<span class="tag tag-amber">⚡ ALERTA COMP.</span>'
        else:
            badge_p = '<span class="tag tag-blue">✓ PRECIO OK</span>'
 
        impacto_html = f'<span class="impact-val">+{imp:,.0f}€ impacto estimado</span>' if imp > 0 else ""
 
        st.markdown(f"""
        <div class="{css}">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;margin-bottom:10px">
            <div>
              <span style="font-weight:700;font-size:1.05rem;color:#f0f9ff">{row['Producto']}</span>
              <span style="color:#334155;font-size:0.78rem;margin-left:10px">{row['Categoría']} · {row['Plataforma']}</span>
            </div>
            <div>{badge_s}{badge_p}</div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">
            <div style="font-size:0.82rem;color:#64748b">📦 {row['accion_stock']}</div>
            <div style="font-size:0.82rem;color:#64748b">💰 {row['accion_pricing']}</div>
          </div>
          <div style="display:flex;gap:20px;font-size:0.75rem;color:#334155;flex-wrap:wrap">
            <span>Precio: <b style="color:#cbd5e1">{row['Precio actual']}€</b></span>
            <span>Comp.mín: <b style="color:#cbd5e1">{row['Comp. mín.']}€</b></span>
            <span>Stock: <b style="color:#cbd5e1">{row['Stock']} uds</b></span>
            <span>Cobertura: <b style="color:#cbd5e1">{row['Cobertura (días)']} días</b></span>
            {'<span>' + impacto_html + '</span>' if impacto_html else ''}
          </div>
        </div>
        """, unsafe_allow_html=True)
 
        col_apply, col_dismiss, _sp = st.columns([1, 1, 3])
        with col_apply:
            if st.button("✓ Aplicada", key=f"apply_{row['SKU']}"):
                registrar_evento("recommendation_actioned", {
                    "sku": row["SKU"],
                    "accion": "aplicada",
                    "senal_stock": row["señal_stock"],
                    "senal_pricing": row["señal_pricing"],
                    "impacto_estimado_eur": row["Impacto total €"],
                })
                st.toast(f"Marcada como aplicada: {row['Producto']}")
        with col_dismiss:
            if st.button("✕ Descartar", key=f"dismiss_{row['SKU']}"):
                registrar_evento("recommendation_actioned", {
                    "sku": row["SKU"],
                    "accion": "descartada",
                    "senal_stock": row["señal_stock"],
                    "senal_pricing": row["señal_pricing"],
                    "impacto_estimado_eur": row["Impacto total €"],
                })
                st.toast(f"Descartada: {row['Producto']}")
 
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-header">📊 Distribución de alertas</div>', unsafe_allow_html=True)
 
    col_a, col_b = st.columns(2)
    COLORS_S = {"CRÍTICO":"#f43f5e","REPOSICIÓN":"#fb923c","EXCESO":"#3b82f6","OK":"#4ade80"}
    COLORS_P = {"PRECIO ALTO":"#f43f5e","SUBIR PRECIO":"#4ade80","ALERTA COMP.":"#fb923c","OK":"#3b82f6"}
 
    with col_a:
        cs = df_rec["señal_stock"].value_counts().reset_index()
        cs.columns = ["Señal","N"]
        fig = px.pie(cs, values="N", names="Señal", hole=0.65,
                     color="Señal", color_discrete_map=COLORS_S, title="Estado de stock")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#64748b", height=280, title_font_color="#e2e8f0",
                          title_font_size=14,
                          legend=dict(font=dict(color="#64748b",size=11)))
        fig.update_traces(textfont_color="white")
        st.plotly_chart(fig, use_container_width=True)
 
    with col_b:
        cp = df_rec["señal_pricing"].value_counts().reset_index()
        cp.columns = ["Señal","N"]
        fig2 = px.pie(cp, values="N", names="Señal", hole=0.65,
                      color="Señal", color_discrete_map=COLORS_P, title="Estado de pricing")
        fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                           font_color="#64748b", height=280, title_font_color="#e2e8f0",
                           title_font_size=14,
                           legend=dict(font=dict(color="#64748b",size=11)))
        fig2.update_traces(textfont_color="white")
        st.plotly_chart(fig2, use_container_width=True)
 
 
# ══ TAB 2: DEMANDA ════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">📈 Evolución de demanda por SKU</div>', unsafe_allow_html=True)
    skus = sorted(df["sku_id"].unique())
    sku_sel = st.multiselect("Selecciona SKUs", options=skus, default=skus[:4],
                             format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
    if sku_sel:
        df_plot = df[df["sku_id"].isin(sku_sel)].copy()
        df_agg = df_plot.groupby(["fecha","sku_id","nombre_producto"])["unidades_vendidas"].sum().reset_index()
        fig_dem = px.line(df_agg, x="fecha", y="unidades_vendidas", color="nombre_producto",
                          labels={"unidades_vendidas":"Unidades","fecha":"Fecha","nombre_producto":"Producto"})
        fig_dem.update_traces(line=dict(width=2))
        fig_dem.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(6,13,26,0.5)",
            font_color="#64748b", height=400,
            legend=dict(orientation="h", yanchor="bottom", y=-0.4, font=dict(color="#94a3b8",size=11)),
            xaxis=dict(gridcolor="rgba(29,106,245,0.08)", showline=False),
            yaxis=dict(gridcolor="rgba(29,106,245,0.08)", showline=False),
        )
        st.plotly_chart(fig_dem, use_container_width=True)
 
        st.markdown('<div class="section-header">🗓 Estacionalidad</div>', unsafe_allow_html=True)
        sku_h = st.selectbox("SKU para heatmap", options=sku_sel,
                             format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}")
        df_heat = df[df["sku_id"] == sku_h].copy()
        dias   = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"]
        meses  = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
        pivot  = df_heat.groupby(["mes","dia_semana"])["unidades_vendidas"].mean().unstack(fill_value=0)
        pivot.index   = [meses[i-1] for i in pivot.index]
        pivot.columns = [dias[i]    for i in pivot.columns]
        fig_h = px.imshow(pivot, color_continuous_scale="Blues",
                          labels=dict(color="Uds/día"),
                          title=f"Demanda media — {sku_nombres.get(sku_h,'')}")
        fig_h.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                            font_color="#64748b", height=320, title_font_color="#e2e8f0")
        st.plotly_chart(fig_h, use_container_width=True)
 
        st.markdown('<div class="section-header">📋 Métricas por producto</div>', unsafe_allow_html=True)
        res = df_plot.groupby(["sku_id","nombre_producto"]).agg(
            Ventas_total=("unidades_vendidas","sum"),
            Media_diaria=("unidades_vendidas","mean"),
            Ingreso_total=("ingreso_estimado","sum"),
            Margen_total=("margen_estimado_eur","sum"),
        ).reset_index().round(1)
        res.columns = ["SKU","Producto","Ventas totales","Media/día","Ingreso €","Margen €"]
        st.dataframe(res, use_container_width=True, hide_index=True)
 
 
# ══ TAB 3: PRICING ════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">💰 Comparativa de precios vs competencia</div>', unsafe_allow_html=True)
    ultimo_df = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    productos = ultimo_df["nombre_producto"].tolist()
 
    PALETTE = ["#1d6af5","#f43f5e","#a855f7","#4ade80"]
    fig_p = go.Figure()
    for i,(col,name) in enumerate(zip(
        ["precio_venta","precio_decathlon","precio_trailzone","precio_outdoorpro"],
        ["Tu precio","Decathlon","TrailZone","OutdoorPro"])):
        fig_p.add_trace(go.Bar(name=name, x=productos, y=ultimo_df[col], marker_color=PALETTE[i]))
 
    fig_p.update_layout(barmode="group",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(6,13,26,0.5)",
        font_color="#64748b", height=420, xaxis_tickangle=-35,
        legend=dict(orientation="h", yanchor="bottom", y=-0.55, font=dict(color="#94a3b8")),
        xaxis=dict(gridcolor="rgba(29,106,245,0.08)"),
        yaxis=dict(gridcolor="rgba(29,106,245,0.08)", title="Precio (€)"))
    st.plotly_chart(fig_p, use_container_width=True)
 
    st.markdown('<div class="section-header">📉 Evolución precio vs competencia</div>', unsafe_allow_html=True)
    sku_p = st.selectbox("Producto", options=sorted(df["sku_id"].unique()),
                         format_func=lambda x: f"{x} — {sku_nombres.get(x,'')}", key="p_sku")
    df_sku = df[df["sku_id"] == sku_p]
    fig_ev = go.Figure()
    for col, name, color, dash in [
        ("precio_venta","Tu precio","#1d6af5","solid"),
        ("precio_decathlon","Decathlon","#f43f5e","dot"),
        ("precio_trailzone","TrailZone","#a855f7","dot"),
        ("precio_outdoorpro","OutdoorPro","#4ade80","dot"),
    ]:
        fig_ev.add_trace(go.Scatter(x=df_sku["fecha"], y=df_sku[col],
            name=name, line=dict(color=color, width=2.5 if dash=="solid" else 1.5, dash=dash)))
    fig_ev.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(6,13,26,0.5)",
        font_color="#64748b", height=360,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, font=dict(color="#94a3b8")),
        xaxis=dict(gridcolor="rgba(29,106,245,0.08)"),
        yaxis=dict(gridcolor="rgba(29,106,245,0.08)", title="Precio (€)"))
    st.plotly_chart(fig_ev, use_container_width=True)
 
    st.markdown('<div class="section-header">📋 Tabla de recomendaciones</div>', unsafe_allow_html=True)
    cols_p = ["Producto","Categoría","señal_pricing","accion_pricing","Precio actual","Precio rec.","Comp. mín.","Impacto pricing €"]
    df_tp = df_rec[cols_p].copy()
    df_tp.columns = ["Producto","Categoría","Señal","Acción","Precio actual €","Precio rec. €","Comp. mín. €","Impacto €"]
    def color_p(val):
        m = {"PRECIO ALTO":"background-color:rgba(244,63,94,0.12);color:#f43f5e",
             "SUBIR PRECIO":"background-color:rgba(74,222,128,0.12);color:#4ade80",
             "ALERTA COMP.":"background-color:rgba(251,146,60,0.12);color:#fb923c"}
        return m.get(val,"background-color:rgba(29,106,245,0.12);color:#60a5fa")
    st.dataframe(df_tp.style.map(color_p, subset=["Señal"]), use_container_width=True, hide_index=True, height=380)
 
 
# ══ TAB 4: STOCK ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">📦 Stock disponible por SKU</div>', unsafe_allow_html=True)
    ultimo_s = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    ultimo_s_sorted = ultimo_s.sort_values("stock_disponible", ascending=True)
 
    # Coloreado basado en decision_engine.clasificar_cobertura, en vez de
    # repetir aquí los umbrales 7/15/45 (y la regla de media_30d) a mano
    # como se hacía antes — evita que este tab quede desincronizado del
    # resto del dashboard si se cambia un umbral en el futuro.
    _COLOR_POR_SENAL = {"CRITICO": "#f43f5e", "REPOSICION": "#fb923c", "EXCESO": "#3b82f6", "OK": "#4ade80"}
    colores_bar = []
    for _, r in ultimo_s_sorted.iterrows():
        media_7d = max(r["ventas_media_7d"], 0.1)
        cob = r["stock_disponible"] / media_7d
        senal = de.clasificar_cobertura(cob, media_7d, r.get("ventas_media_30d"))
        colores_bar.append(_COLOR_POR_SENAL[senal])
 
    fig_s = go.Figure()
    fig_s.add_trace(go.Bar(
        x=ultimo_s_sorted["stock_disponible"],
        y=ultimo_s_sorted["nombre_producto"],
        orientation="h", marker_color=colores_bar,
        text=ultimo_s_sorted["stock_disponible"].astype(str)+" uds",
        textposition="outside", textfont=dict(color="#94a3b8", size=11)))
    fig_s.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(6,13,26,0.5)",
        font_color="#64748b", height=480, xaxis_title="Unidades en stock",
        xaxis=dict(gridcolor="rgba(29,106,245,0.08)"))
    st.plotly_chart(fig_s, use_container_width=True)
 
    st.markdown('<div class="section-header">⏱ Días de cobertura</div>', unsafe_allow_html=True)
    df_cob = df_rec.sort_values("Cobertura (días)")
    # df_rec["señal_stock"] ya viene de decision_engine (vía _MAPA_SENAL_STOCK),
    # así que reutilizamos esa columna en vez de recalcular el umbral aquí.
    _COLOR_POR_SENAL_ACENTOS = {"CRÍTICO": "#f43f5e", "REPOSICIÓN": "#fb923c", "EXCESO": "#3b82f6", "OK": "#4ade80"}
    colores_cob = [_COLOR_POR_SENAL_ACENTOS.get(s, "#4ade80") for s in df_cob["señal_stock"]]
 
    fig_cob = go.Figure()
    fig_cob.add_trace(go.Bar(
        x=df_cob["Cobertura (días)"], y=df_cob["Producto"],
        orientation="h", marker_color=colores_cob,
        text=[f"{c} días" for c in df_cob["Cobertura (días)"].tolist()], textposition="outside",
        textfont=dict(color="#94a3b8", size=11)))
    for x, color, label in [(7,"#f43f5e","Crítico"),(15,"#fb923c","Riesgo"),(45,"#3b82f6","Exceso")]:
        fig_cob.add_vline(x=x, line_dash="dash", line_color=color, opacity=0.5,
                          annotation_text=label, annotation_font_color=color,
                          annotation_font_size=11)
    fig_cob.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(6,13,26,0.5)",
        font_color="#64748b", height=480, xaxis_title="Días",
        xaxis=dict(gridcolor="rgba(29,106,245,0.08)"))
    st.plotly_chart(fig_cob, use_container_width=True)
 
    st.markdown('<div class="section-header">📋 Tabla de alertas de stock</div>', unsafe_allow_html=True)
    cols_s = ["Producto","Categoría","señal_stock","accion_stock","Stock","Cobertura (días)","Demanda/día","Impacto stock €"]
    df_ts = df_rec[cols_s].copy()
    df_ts.columns = ["Producto","Categoría","Señal","Acción","Stock uds","Cobertura días","Demanda/día","Impacto €"]
    def color_s(val):
        m = {"CRÍTICO":"background-color:rgba(244,63,94,0.12);color:#f43f5e",
             "REPOSICIÓN":"background-color:rgba(251,146,60,0.12);color:#fb923c",
             "EXCESO":"background-color:rgba(29,106,245,0.12);color:#60a5fa"}
        return m.get(val,"background-color:rgba(74,222,128,0.12);color:#4ade80")
    st.dataframe(df_ts.style.map(color_s, subset=["Señal"]), use_container_width=True, hide_index=True, height=380)
 
 
# ── FOOTER ────────────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div style="text-align:center;font-family:\'JetBrains Mono\',monospace;color:#334155;font-size:0.65rem;letter-spacing:0.22em;padding:10px 0">ILTONIF © 2026 · INTELLIGENCE PLATFORM · PRICING & STOCK AI · DATOS ACTUALIZADOS A DIARIO</div>',
    unsafe_allow_html=True)
 
