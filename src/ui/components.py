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


def aviso_origenes(origenes: dict) -> None:
    """Muestra en el sidebar de qué fuente vienen los datos de cada plataforma."""
    st.sidebar.markdown("**Origen de los datos**")
    for plataforma, origen in origenes.items():
        st.sidebar.markdown(
            f"{plataforma}: {badge_origen(origen)}", unsafe_allow_html=True
        )
    if all(o == "sample" for o in origenes.values()):
        st.sidebar.info(
            "Estás viendo **datos de ejemplo**. Configura credenciales en "
            "`.streamlit/secrets.toml` o rellena la caché para ver datos reales."
        )


def kpi(col, titulo: str, valor: str, sub: str = "", estado: str | None = None) -> None:
    """Tarjeta KPI con borde de color según estado (ok/warn/off)."""
    borde = {"ok": TEMA.verde_ok, "warn": TEMA.ambar_riesgo,
             "off": TEMA.rojo_off}.get(estado, TEMA.primario)
    col.markdown(
        f"""<div class="kpi-card" style="border-left-color:{borde}">
              <h3>{titulo}</h3>
              <div class="val">{valor}</div>
              <div class="sub">{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )


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
