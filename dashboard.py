import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta

from decision_engine import evaluar_sku, clasificar_cobertura

st.set_page_config(
    page_title="ILTONIF — Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ── Autenticación ─────────────────────────────────────────────
def check_password() -> bool:
    """Gate de acceso con contraseña definida en st.secrets['password']."""

    def _password_entered():
        if st.session_state.get("_password") == st.secrets.get("password"):
            st.session_state["_password_correct"] = True
            del st.session_state["_password"]
        else:
            st.session_state["_password_correct"] = False

    if "password" not in st.secrets:
        st.error("⚠️ Falta 'password' en st.secrets. Configúrala en .streamlit/secrets.toml (local) o en Settings → Secrets (Streamlit Cloud).")
        return False

    if st.session_state.get("_password_correct", False):
        return True

    st.text_input("Contraseña", type="password", key="_password", on_change=_password_entered)
    if st.session_state.get("_password_correct") is False:
        st.error("Contraseña incorrecta")
    return False


if not check_password():
    st.stop()


# ── Tracking (PostHog) ────────────────────────────────────────
import uuid


@st.cache_resource
def _get_posthog():
    """Cliente PostHog; devuelve None si no hay API key configurada (tracking desactivado)."""
    api_key = st.secrets.get("posthog_api_key")
    if not api_key:
        return None
    try:
        from posthog import Posthog
        return Posthog(project_api_key=api_key, host=st.secrets.get("posthog_host", "https://eu.i.posthog.com"))
    except Exception:
        return None


def track(event: str, props: dict = None):
    """Emite un evento a PostHog. No-op silencioso si no hay cliente."""
    ph = _get_posthog()
    if ph is None:
        return
    if "_distinct_id" not in st.session_state:
        st.session_state["_distinct_id"] = str(uuid.uuid4())
    try:
        ph.capture(distinct_id=st.session_state["_distinct_id"], event=event, properties=props or {})
    except Exception:
        pass

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

* { font-family: 'Outfit', sans-serif !important; }

/* FONDO */
.main { background: #020408 !important; }
.block-container { padding: 0 2rem 2rem !important; max-width: 100% !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #030610 !important;
    border-right: 1px solid rgba(29,106,245,0.2) !important;
}
[data-testid="stSidebar"] * { color: #94a3b8 !important; }
[data-testid="stSidebarContent"] { padding: 20px 16px !important; }

/* MÉTRICAS */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #060d1a, #0a1020) !important;
    border: 1px solid rgba(29,106,245,0.15) !important;
    border-radius: 16px !important;
    padding: 24px 20px !important;
    position: relative !important;
    overflow: hidden !important;
    transition: all 0.3s ease !important;
}
[data-testid="stMetric"]:hover {
    border-color: rgba(29,106,245,0.5) !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 12px 40px rgba(29,106,245,0.15) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 2.8rem !important;
    letter-spacing: 0.04em !important;
    color: #fff !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #475569 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* TABS */
.stTabs [data-baseweb="tab-list"] {
    background: #060d1a !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 4px !important;
    border: 1px solid rgba(29,106,245,0.15) !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #475569 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    padding: 10px 20px !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #1d6af5, #1d4ed8) !important;
    color: white !important;
    box-shadow: 0 4px 16px rgba(29,106,245,0.4) !important;
}

/* SELECTBOX / INPUTS */
.stSelectbox > div > div {
    background: #060d1a !important;
    border: 1px solid rgba(29,106,245,0.2) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
.stDateInput > div > div {
    background: #060d1a !important;
    border: 1px solid rgba(29,106,245,0.2) !important;
    border-radius: 10px !important;
}

/* BOTONES */
.stButton > button {
    background: linear-gradient(135deg, #1d6af5, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    font-size: 0.78rem !important;
    transition: all 0.3s !important;
    box-shadow: 0 0 20px rgba(29,106,245,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(29,106,245,0.5) !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; }

/* CARDS DE ALERTAS */
.alert-critico {
    background: linear-gradient(135deg, rgba(244,63,94,0.08), rgba(244,63,94,0.03));
    border: 1px solid rgba(244,63,94,0.25);
    border-left: 4px solid #f43f5e;
    border-radius: 14px;
    padding: 18px 24px;
    margin: 10px 0;
    transition: all 0.3s;
    position: relative;
    overflow: hidden;
}
.alert-critico::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 80px; height: 80px;
    background: radial-gradient(circle, rgba(244,63,94,0.08), transparent);
    border-radius: 50%;
}
.alert-critico:hover { border-color: rgba(244,63,94,0.5); background: rgba(244,63,94,0.08); }

.alert-warning {
    background: linear-gradient(135deg, rgba(251,146,60,0.08), rgba(251,146,60,0.03));
    border: 1px solid rgba(251,146,60,0.25);
    border-left: 4px solid #fb923c;
    border-radius: 14px;
    padding: 18px 24px;
    margin: 10px 0;
    transition: all 0.3s;
}
.alert-warning:hover { border-color: rgba(251,146,60,0.5); }

.alert-info {
    background: linear-gradient(135deg, rgba(29,106,245,0.08), rgba(29,106,245,0.03));
    border: 1px solid rgba(29,106,245,0.25);
    border-left: 4px solid #1d6af5;
    border-radius: 14px;
    padding: 18px 24px;
    margin: 10px 0;
    transition: all 0.3s;
}
.alert-ok {
    background: linear-gradient(135deg, rgba(74,222,128,0.08), rgba(74,222,128,0.03));
    border: 1px solid rgba(74,222,128,0.25);
    border-left: 4px solid #4ade80;
    border-radius: 14px;
    padding: 18px 24px;
    margin: 10px 0;
    transition: all 0.3s;
}

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
.tag-red   { background: rgba(244,63,94,0.15); color: #f43f5e; border: 1px solid rgba(244,63,94,0.3); }
.tag-amber { background: rgba(251,146,60,0.15); color: #fb923c; border: 1px solid rgba(251,146,60,0.3); }
.tag-blue  { background: rgba(29,106,245,0.15); color: #60a5fa; border: 1px solid rgba(29,106,245,0.3); }
.tag-green { background: rgba(74,222,128,0.15); color: #4ade80; border: 1px solid rgba(74,222,128,0.3); }

.impact-val {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    font-weight: 700;
    color: #1d6af5;
    letter-spacing: 0.05em;
}

.section-header {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    letter-spacing: 0.06em;
    color: #fff;
    margin: 24px 0 16px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.kpi-banner {
    background: linear-gradient(135deg, #060d1a, #0a1428);
    border: 1px solid rgba(29,106,245,0.2);
    border-radius: 20px;
    padding: 24px 32px;
    margin: 20px 0;
    display: flex;
    align-items: center;
    gap: 32px;
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(29,106,245,0.3), transparent);
    margin: 28px 0;
}

/* HEADER */
.main-header {
    background: linear-gradient(135deg, #030610, #060d1a);
    border-bottom: 1px solid rgba(29,106,245,0.2);
    padding: 20px 32px;
    margin: -1rem -2rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* SCROLLBAR */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #020408; }
::-webkit-scrollbar-thumb { background: rgba(29,106,245,0.4); border-radius: 4px; }
</style>
""", unsafe_allow_html=True)


# ── DATOS ──────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    base = Path(__file__).parent / "data"
    df = pd.read_csv(base / "iltonif_dataset_modelable_v3.csv", parse_dates=["fecha"])
    return df

# Mapeo de señales del motor (sin acentos, testable) a etiquetas de UI
SENAL_LABEL = {"CRITICO": "CRÍTICO", "REPOSICION": "REPOSICIÓN"}


@st.cache_data
def generar_recomendaciones(df):
    """Genera la tabla de recomendaciones delegando la lógica en decision_engine."""
    ultimo = df.sort_values("fecha").groupby("sku_id").last().reset_index()
    recs = []
    for _, row in ultimo.iterrows():
        r = evaluar_sku(row.to_dict())
        recs.append({
            "SKU": row["sku_id"], "Producto": row["nombre_producto"],
            "Categoría": row["categoria"], "Plataforma": row["plataforma"],
            "señal_stock": SENAL_LABEL.get(r["senal_stock"], r["senal_stock"]),
            "accion_stock": r["accion_stock"],
            "señal_pricing": r["senal_pricing"], "accion_pricing": r["accion_pricing"],
            "Precio actual": round(row["precio_venta"], 2), "Precio rec.": round(r["precio_rec"], 2),
            "Comp. mín.": round(row["precio_comp_min"], 2), "Comp. avg": round(row["precio_comp_avg"], 2),
            "Stock": int(row["stock_disponible"]), "Cobertura (días)": r["cobertura_dias"],
            "Demanda/día": round(max(row["ventas_media_7d"], 0.1), 1),
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
        <div style="font-family:\'Bebas Neue\',sans-serif;font-size:1.4rem;letter-spacing:0.12em;color:#fff">ILTONIF</div>
        <div style="font-size:0.65rem;letter-spacing:0.2em;color:#1d6af5;text-transform:uppercase;margin-top:2px">Intelligence Platform</div>
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
st.markdown('''
<div style="
  background:linear-gradient(135deg,#030610,#060d1a);
  border-bottom:1px solid rgba(29,106,245,0.2);
  padding:24px 0 20px;
  margin-bottom:32px;
">
  <div style="display:flex;align-items:center;gap:20px">
    <svg width="56" height="56" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
      <rect width="44" height="44" rx="10" fill="#1d6af5"/>
      <circle cx="16" cy="13" r="6" fill="white"/>
      <rect x="11" y="18" width="8" height="22" rx="4" fill="white" transform="rotate(-22 15 29)"/>
    </svg>
    <div>
      <div style="font-family:\'Bebas Neue\',sans-serif;font-size:2.6rem;letter-spacing:0.06em;line-height:1;color:#fff">ILTONIF</div>
      <div style="font-size:0.75rem;letter-spacing:0.25em;color:#1d6af5;text-transform:uppercase;margin-top:4px">Intelligence Platform · Pricing & Stock AI</div>
    </div>
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

    for idx, row in df_sorted.iterrows():
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

        estado_key = f"rec_estado_{row['Producto']}"
        estado = st.session_state.get(estado_key)
        if estado:
            st.caption(f"✓ Recomendación marcada como {estado}")
        else:
            col_ap, col_desc, _sp = st.columns([1, 1, 5])
            rec_props = {
                "producto": row["Producto"],
                "categoria": row["Categoría"],
                "plataforma": row["Plataforma"],
                "señal_stock": ss,
                "señal_pricing": sp,
                "impacto_estimado_eur": float(imp),
            }
            if col_ap.button("✅ Aplicada", key=f"rec_ap_{idx}"):
                track("recommendation_actioned", {**rec_props, "action": "aplicada"})
                st.session_state[estado_key] = "aplicada"
                st.rerun()
            if col_desc.button("✖ Descartada", key=f"rec_desc_{idx}"):
                track("recommendation_actioned", {**rec_props, "action": "descartada"})
                st.session_state[estado_key] = "descartada"
                st.rerun()

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

    COLOR_SENAL = {"CRITICO": "#f43f5e", "REPOSICION": "#fb923c", "EXCESO": "#3b82f6", "OK": "#4ade80"}
    colores_bar = []
    for _, r in ultimo_s_sorted.iterrows():
        media_7d = max(r["ventas_media_7d"], 0.1)
        media_30d = max(r.get("ventas_media_30d", media_7d), 0.1)
        cob = r["stock_disponible"] / media_7d
        senal = clasificar_cobertura(cob, media_7d, media_30d)
        colores_bar.append(COLOR_SENAL[senal])

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
    cols_cob = df_cob["Cobertura (días)"].tolist()
    COLOR_SENAL_UI = {"CRÍTICO": "#f43f5e", "REPOSICIÓN": "#fb923c", "EXCESO": "#3b82f6", "OK": "#4ade80"}
    colores_cob = [COLOR_SENAL_UI.get(s, "#4ade80") for s in df_cob["señal_stock"]]

    fig_cob = go.Figure()
    fig_cob.add_trace(go.Bar(
        x=df_cob["Cobertura (días)"], y=df_cob["Producto"],
        orientation="h", marker_color=colores_cob,
        text=[f"{c} días" for c in cols_cob], textposition="outside",
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
    '<div style="text-align:center;font-family:\'JetBrains Mono\',monospace;color:#1e293b;font-size:0.65rem;letter-spacing:0.2em;padding:8px 0">ILTONIF © 2025 — INTELLIGENCE PLATFORM · PRICING & STOCK AI</div>',
    unsafe_allow_html=True)
