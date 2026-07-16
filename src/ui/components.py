"""
Componentes reutilizables de UI: cabecera, selector de periodo, tarjetas KPI,
avisos de origen de datos y helpers de gráficos con Plotly.
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.config import COLOR_PLATAFORMA, TEMA
from src.ui.theme import badge_origen, eur, num, pct


def cabecera(titulo: str, subtitulo: str = "") -> None:
    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.title(titulo)
        if subtitulo:
            st.caption(subtitulo)
    with col2:
        st.caption("UVic · WeRise")
        st.caption("Dashboard de marketing")


def selector_periodo(default: int = 30) -> int:
    opciones = {"Últimos 7 días": 7, "Últimos 14 días": 14,
                "Últimos 30 días": 30, "Últimos 90 días": 90}
    etiqueta = st.sidebar.selectbox("Periodo", list(opciones.keys()),
                                    index=list(opciones.values()).index(default))
    return opciones[etiqueta]


def aviso_origenes(origenes: dict, detalles: dict | None = None) -> None:
    """Muestra en el sidebar de qué fuente vienen los datos de cada plataforma.
    Si una fuente NO está en vivo y hay un motivo (ej. error de API), lo enseña."""
    from src import config

    st.sidebar.markdown("**Origen de los datos**")
    for plataforma, origen in origenes.items():
        st.sidebar.markdown(
            f"{plataforma}: {badge_origen(origen)}", unsafe_allow_html=True
        )
        if detalles and origen != "api":
            d = str(detalles.get(plataforma) or "")
            if d and d not in ("Caché local", "Datos de ejemplo"):
                st.sidebar.caption(f"↳ {d[:220]}")
    if st.sidebar.button("🔄 Actualizar ahora", width='stretch'):
        st.cache_data.clear()
        st.rerun()
    st.sidebar.caption(
        f"HubSpot se refresca cada {config.CACHE_TTL_HUBSPOT // 60} min · "
        f"Ads/GA4 cada {config.CACHE_TTL_ADS // 60} min. "
        "Usa «Actualizar ahora» para forzar."
    )
    if all(o == "sample" for o in origenes.values()):
        st.sidebar.info(
            "Estás viendo **datos de ejemplo**. Configura credenciales en "
            "`.streamlit/secrets.toml` o rellena la caché para ver datos reales."
        )


def kpi(col, titulo: str, valor: str, sub: str = "", estado: str | None = None,
        delta: float | None = None, delta_bueno: bool = True) -> None:
    """Tarjeta KPI con borde de color (ok/warn/off) y, opcionalmente, una flecha
    de tendencia (delta = variación vs. mitad anterior del periodo)."""
    borde = {"ok": TEMA.verde_ok, "warn": TEMA.ambar_riesgo,
             "off": TEMA.rojo_off}.get(estado, TEMA.primario)
    delta_html = ""
    if delta is not None:
        flecha = "▲" if delta >= 0 else "▼"
        positivo = (delta >= 0) == delta_bueno
        color = TEMA.verde_ok if positivo else TEMA.rojo_off
        delta_html = (f'<span style="color:{color};font-weight:700;font-size:.78rem">'
                      f'{flecha} {abs(delta)*100:.0f}%</span> ')
    col.markdown(
        f"""<div class="kpi-card" style="border-left-color:{borde}">
              <h3>{titulo}</h3>
              <div class="val">{valor}</div>
              <div class="sub">{delta_html}{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )


_LBL_TOTAL = {
    "sesiones": "Sesiones", "usuarios": "Usuarios", "eventos": "Eventos",
    "eventos_clave": "Eventos clave", "vistas": "Páginas vistas",
    "rebote": "Rebote", "duracion_media": "Dur. media",
    "resultados_meta": "Meta", "resultados_google": "Google",
    "leads_hubspot": "HubSpot", "eventos_ga4": "GA4",
    "leads": "Leads", "impresiones": "Impr.", "clics": "Clics",
    "coste": "Inversión", "conversiones": "Resultados",
    "ctr": "CTR", "cpc": "CPC", "cpl_meta": "CPL", "cpl_google": "CPL",
}
_SUF_TOTAL = {"coste": " €"}


def tabla_totales(df: pd.DataFrame, columnas: list[str], sum_cols: list[str],
                  column_config: dict, weighted: list[str] | None = None,
                  weight_col: str = "sesiones",
                  ratios: dict | None = None) -> None:
    """Muestra la tabla y, debajo, un **pie de TOTAL fijo** (siempre visible,
    fuera del scroll interno del grid). `sum_cols` se suman; `weighted` se
    promedian ponderando por `weight_col`; `ratios` = {col: (num, den, mult,
    sufijo)} se recalculan como sum(num)/sum(den)*mult (CTR/CPC/CPL exactos)."""
    if df is None or df.empty:
        st.info("Sin datos.")
        return
    cols = [c for c in columnas if c in df.columns]
    st.dataframe(df[cols], width='stretch', hide_index=True, column_config=column_config)

    partes = []
    for c in sum_cols:
        if c in df.columns:
            partes.append(f"{_LBL_TOTAL.get(c, c)} <strong>{num(int(df[c].sum()))}"
                          f"{_SUF_TOTAL.get(c, '')}</strong>")
    for c, (nc, dc, mult, suf) in (ratios or {}).items():
        if nc in df.columns and dc in df.columns:
            den = df[dc].sum()
            v = df[nc].sum() / den * mult if den else 0
            v_str = f"{v:,.2f}".replace(",", "·").replace(".", ",").replace("·", ".")
            partes.append(f"{_LBL_TOTAL.get(c, c)} <strong>{v_str}{suf}</strong>")
    if weighted and weight_col in df.columns:
        w = df[weight_col].sum()
        for c in weighted:
            if c not in df.columns:
                continue
            v = (df[c] * df[weight_col]).sum() / w if w else 0
            if c == "rebote":
                partes.append(f"{_LBL_TOTAL.get(c, c)} <strong>{v:.1f}%</strong>")
            elif c == "duracion_media":
                partes.append(f"{_LBL_TOTAL.get(c, c)} <strong>{v:.0f}s</strong>")
            else:
                partes.append(f"{_LBL_TOTAL.get(c, c)} <strong>{num(v)}</strong>")
    st.markdown(
        f"<div style='border-top:2px solid {TEMA.primario};padding:.45rem .2rem;margin-top:-.4rem'>"
        f"🧮 <strong>TOTAL</strong> — {' · '.join(partes)}</div>",
        unsafe_allow_html=True,
    )


def caja_insights(wins: list[str], concerns: list[str]) -> None:
    """Dos columnas: 'Lo que funciona' (verde) y 'A mejorar' (rojo)."""
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("##### ✅ Lo que funciona")
        for w in (wins[:5] or ["—"]):
            st.markdown(f"- {w}")
    with c2:
        st.markdown("##### ⚠️ A mejorar")
        for c in (concerns[:5] or ["Sin alertas relevantes en el periodo."]):
            st.markdown(f"- {c}")


def tabla_recomendaciones(recos: list[dict]) -> None:
    """Recomendaciones priorizadas por impacto/esfuerzo (matriz 2x2)."""
    if not recos:
        st.info("Sin recomendaciones para el periodo.")
        return
    # dedup por texto conservando orden
    vistos, unicas = set(), []
    for r in recos:
        if r["texto"] not in vistos:
            vistos.add(r["texto"]); unicas.append(r)

    def prio(r: dict) -> tuple[int, str]:
        if r["impacto"] == "Alto" and r["esfuerzo"] == "Bajo":
            return (0, "🔴 Hacer ya")
        if r["impacto"] == "Alto":
            return (1, "🟠 Prioritario")
        if r["impacto"] == "Medio":
            return (2, "🟡 Siguiente sprint")
        return (3, "⚪ Si hay tiempo")

    filas = []
    for r in unicas:
        orden, etiqueta = prio(r)
        filas.append(dict(_o=orden, Recomendación=r["texto"], Impacto=r["impacto"],
                          Esfuerzo=r["esfuerzo"], Prioridad=etiqueta))
    df = pd.DataFrame(filas).sort_values("_o").drop(columns="_o")
    st.dataframe(df, width='stretch', hide_index=True)


# --------------------------------------------------------------------------- #
# Gráficos
# --------------------------------------------------------------------------- #
def linea_temporal(df: pd.DataFrame, x: str, y: str, color: str | None,
                   titulo: str, y_label: str = "") -> None:
    if df.empty:
        st.info("Sin datos para el periodo seleccionado.")
        return
    fig = px.line(df, x=x, y=y, color=color, markers=True,
                  color_discrete_map=COLOR_PLATAFORMA,
                  color_discrete_sequence=list(TEMA.paleta))
    fig.update_layout(
        title=titulo, height=340, margin=dict(l=10, r=10, t=40, b=10),
        legend_title="", yaxis_title=y_label, xaxis_title="",
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')


def barras(df: pd.DataFrame, x: str, y: str, color: str | None,
           titulo: str, orientacion: str = "v", texto: str | None = None) -> None:
    if df.empty:
        st.info("Sin datos.")
        return
    fig = px.bar(df, x=x, y=y, color=color, orientation=orientacion,
                 text=texto, color_discrete_map=COLOR_PLATAFORMA,
                 color_discrete_sequence=list(TEMA.paleta))
    fig.update_layout(
        title=titulo, height=360, margin=dict(l=10, r=10, t=40, b=10),
        legend_title="", plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width='stretch')


def embudo_chart(df: pd.DataFrame) -> None:
    if df.empty:
        st.info("Sin datos de embudo.")
        return
    fig = go.Figure(go.Funnel(
        y=df["etapa"], x=df["leads"],
        textposition="inside",
        texttemplate="%{value} (%{percentInitial})",
        marker=dict(color=list(TEMA.paleta)),
    ))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width='stretch')


def donut(df: pd.DataFrame, nombres: str, valores: str, titulo: str) -> None:
    if df.empty:
        st.info("Sin datos.")
        return
    fig = px.pie(df, names=nombres, values=valores, hole=0.55,
                 color_discrete_sequence=list(TEMA.paleta))
    fig.update_layout(title=titulo, height=320, margin=dict(l=10, r=10, t=40, b=10),
                      paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width='stretch')
