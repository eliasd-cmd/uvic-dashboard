"""Página: Planificación trimestral (Jul–Ago–Sep) — Google Sheet en vivo.

Replica las 3 pestañas del Excel de marketing: TOTAL, Por Programa y Por
Plataforma. Se lee en vivo de una Google Sheet; si cambias el plan en la hoja,
el dashboard lo refleja al recargar (o con «Actualizar ahora»).
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.data import loader
from src.ui import components as ui
from src.ui.theme import aplicar_tema, badge_origen, eur, num, pct

st.set_page_config(page_title="Planificación · UVic", page_icon="📋", layout="wide")
aplicar_tema()

data, origen, detalle = loader.cargar_plan()

# Origen + botón de refresco en el sidebar (coherente con el resto).
st.sidebar.markdown("**Origen del plan**")
st.sidebar.markdown(f"Planificación: {badge_origen(origen)}", unsafe_allow_html=True)
if origen != "api" and detalle:
    st.sidebar.caption(f"↳ {detalle}")
if st.sidebar.button("🔄 Actualizar ahora", width="stretch"):
    st.cache_data.clear()
    st.rerun()

ui.cabecera("Planificación",
            "Objetivos del trimestre Jul–Ago–Sep · editable en la Google Sheet")

if not data:
    st.warning(
        "No hay planificación conectada todavía. Configura el bloque `[plan]` con "
        "`sheet_id` en `.streamlit/secrets.toml` y comparte la Google Sheet con el "
        "service account. Mientras, se muestra el Excel local si está en el repo."
    )
    st.stop()


# --------------------------------------------------------------------------- #
# Formato por métrica (los valores del plan son ratios/€/enteros según la fila)
# --------------------------------------------------------------------------- #
def _formatear(label: str, valor) -> str:
    lbl = (label or "").lower()
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "" if valor is None or str(valor).lower() == "none" else str(valor)
    if "cpl" in lbl:
        return eur(v, 2)
    if "presu" in lbl or "facturaci" in lbl:
        return eur(v, 0)
    if "tasa" in lbl or lbl.strip() == "gp":
        return pct(v, 1)
    return num(v, 0)


def _tabla_bloque(bloque: dict) -> pd.DataFrame:
    filas = []
    for label, valores in bloque["metricas"].items():
        fila = {"Métrica": label}
        for mes, v in zip(bloque["meses"], valores):
            fila[mes.capitalize() if mes != "Total" else "Total"] = _formatear(label, v)
        filas.append(fila)
    return pd.DataFrame(filas)


def _render(bloque: dict, con_titulo: bool = True):
    if con_titulo and bloque["nombre"]:
        nombre = bloque["nombre"].replace("Total (sin documentacion)", "TOTAL (5 programas)")
        st.markdown(f"#### {nombre}")
    df = _tabla_bloque(bloque)
    st.dataframe(
        df, hide_index=True, width="stretch",
        column_config={
            "Métrica": st.column_config.TextColumn("Métrica", width="medium"),
        },
    )


tab_total, tab_prog, tab_plat = st.tabs(
    ["🎯 Total", "🎓 Por programa", "📣 Por plataforma"])

with tab_total:
    st.caption(
        "Objetivo global del trimestre (sin el postgrau de Documentación). "
        "Leads, inversión, CPL, ventas, tasa de conversión, facturación y margen (GP)."
    )
    for b in data.get("TOTAL", []):
        _render(b, con_titulo=False)

with tab_prog:
    st.caption("Planificación tentativa por programa. Cada bloque = un programa.")
    bloques = data.get("Por Programa", [])
    for i, b in enumerate(bloques):
        _render(b)
        if i < len(bloques) - 1:
            st.divider()

with tab_plat:
    st.caption("Planificación por plataforma de captación (Meta Ads y Google Ads).")
    bloques = data.get("Por Plataforma", [])
    for i, b in enumerate(bloques):
        _render(b)
        if i < len(bloques) - 1:
            st.divider()

st.caption(
    "Esta hoja se alimenta de la **Google Sheet de planificación** en vivo: cualquier "
    "cambio que hagas ahí se refleja aquí al recargar (o con «Actualizar ahora»). "
    "Las filas y columnas replican el Excel original."
)
