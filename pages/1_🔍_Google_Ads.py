"""Página: detalle de Google Ads."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, eur, num, pct

st.set_page_config(page_title="Google Ads · UVic", page_icon="🔍", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Google Ads", f"Cuenta {config.GOOGLE_ADS_CUSTOMER_ID} · últimos {dias} días")

df = datos.google
if df.empty:
    st.warning("No hay datos de Google Ads.")
    st.stop()

resumen = metrics.resumen_plataforma(df)
r = resumen.iloc[0] if not resumen.empty else None

c1, c2, c3, c4, c5 = st.columns(5)
ui.kpi(c1, "Inversión", eur(r["coste"]))
ui.kpi(c2, "Impresiones", num(r["impresiones"]))
ui.kpi(c3, "Clics", num(r["clics"]), f"CTR {pct(r['ctr'],2)}")
ui.kpi(c4, "CPC medio", eur(r["cpc"], 2))
ui.kpi(c5, "Conversiones", num(r["conversiones"]),
       estado="off" if r["conversiones"] == 0 else "ok")

if r["conversiones"] == 0:
    st.error(
        "⚠️ **0 conversiones registradas en Google Ads** pese a la inversión. "
        "Coincide con el diagnóstico: el tracking de conversiones no está "
        "atribuyendo. Revisa la etiqueta de conversión y el enlace con las landings."
    )

st.divider()

st.subheader("Inversión y clics diarios")
serie = df.groupby("fecha", as_index=False).agg(coste=("coste", "sum"), clics=("clics", "sum"))
ui.linea_temporal(serie, x="fecha", y="coste", color=None, titulo="Inversión €/día", y_label="€")

st.subheader("Rendimiento por campaña")
camp = metrics.resumen_campana(df)
ui.barras(camp.head(10), x="coste", y="campana", color="programa",
          titulo="Inversión por campaña", orientacion="h")

st.dataframe(
    camp[["campana", "programa", "impresiones", "clics", "ctr", "cpc", "coste", "conversiones"]],
    width='stretch', hide_index=True,
    column_config={
        "campana": "Campaña", "programa": "Programa",
        "impresiones": st.column_config.NumberColumn("Impr.", format="%d"),
        "clics": st.column_config.NumberColumn("Clics", format="%d"),
        "ctr": st.column_config.NumberColumn("CTR", format="%.2f%%"),
        "cpc": st.column_config.NumberColumn("CPC", format="%.2f €"),
        "coste": st.column_config.NumberColumn("Inversión", format="%.0f €"),
        "conversiones": st.column_config.NumberColumn("Conv.", format="%d"),
    },
)
st.caption(
    "Las campañas **WeRise_Search_NAC_** deberían traer el grueso de los leads "
    "cualificados. Si aparecen a 0 impresiones, revisa keywords y aprobación de anuncios."
)
