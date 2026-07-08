"""Página: detalle de Meta Ads."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, eur, num, pct

st.set_page_config(page_title="Meta Ads · UVic", page_icon="📱", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Meta Ads", f"Cuenta {config.META_AD_ACCOUNT_ID} · últimos {dias} días")

df = datos.meta
if df.empty:
    st.warning("No hay datos de Meta Ads.")
    st.stop()

resumen = metrics.resumen_plataforma(df)
r = resumen.iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
ui.kpi(c1, "Inversión", eur(r["coste"]))
ui.kpi(c2, "Impresiones", num(r["impresiones"]))
ui.kpi(c3, "Clics", num(r["clics"]), f"CTR {pct(r['ctr'],2)}")
ui.kpi(c4, "CPC medio", eur(r["cpc"], 2))
ui.kpi(c5, "CPM", eur(r["cpm"], 2))

# Leads reales vía HubSpot atribuidos a Meta (la plataforma atribuye 0 por la rotura).
leads_meta = datos.leads[datos.leads["fuente"] == "Paid Social"]
st.warning(
    f"Meta atribuye **{int(r['conversiones'])} conversiones** en la plataforma, "
    f"pero HubSpot registra **{len(leads_meta)} leads** de Paid Social en el periodo. "
    "Es la **rotura de atribución** conocida (Cloud Pages / pérdida de `fbclid`), "
    "no falta de leads. Revisa la página de *Tracking & Atribución*."
)

st.divider()

st.subheader("Inversión y clics diarios")
serie = df.groupby("fecha", as_index=False).agg(coste=("coste", "sum"), clics=("clics", "sum"))
ui.linea_temporal(serie, x="fecha", y="coste", color=None, titulo="Inversión €/día", y_label="€")

st.subheader("Rendimiento por campaña")
camp = metrics.resumen_campana(df)
ui.barras(camp, x="coste", y="campana", color="programa",
          titulo="Inversión por campaña", orientacion="h")

st.dataframe(
    camp[["campana", "programa", "impresiones", "clics", "ctr", "cpc", "coste"]],
    width='stretch', hide_index=True,
    column_config={
        "campana": "Campaña", "programa": "Programa",
        "impresiones": st.column_config.NumberColumn("Impr.", format="%d"),
        "clics": st.column_config.NumberColumn("Clics", format="%d"),
        "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
        "cpc": st.column_config.NumberColumn("CPC", format="%.2f €"),
        "coste": st.column_config.NumberColumn("Inversión", format="%.0f €"),
    },
)
