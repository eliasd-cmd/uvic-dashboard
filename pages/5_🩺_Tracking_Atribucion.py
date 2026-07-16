"""Página: salud del tracking y de la atribución (diagnóstico + recomendaciones)."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import insights, loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, num, pct

st.set_page_config(page_title="Tracking & Atribución · UVic", page_icon="🩺", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes, datos.detalles)

ui.cabecera("Tracking & Atribución", "Salud de la medición end-to-end")

leads = datos.leads
conv_google = int(datos.google["conversiones"].sum()) if not datos.google.empty else 0
conv_meta = int(datos.meta["conversiones"].sum()) if not datos.meta.empty else 0
leads_total = len(leads)
con_programa = int((leads["programa"] != "Sin asignar").sum()) if leads_total else 0
pct_programa = con_programa / leads_total if leads_total else 0
ratio_atrib = min(1.0, (conv_google + conv_meta) / leads_total) if leads_total else 0

# Puntuación de medición (0-100): mitad etiquetado de programa, mitad atribución de clic.
score = round(100 * (0.5 * pct_programa + 0.5 * ratio_atrib))
estado_score = "ok" if score >= 70 else ("warn" if score >= 40 else "off")

st.subheader("Semáforo de medición")
c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Puntuación de medición", f"{score}/100",
       "Etiquetado + atribución", estado=estado_score)
ui.kpi(c2, "Conversiones Google", num(conv_google),
       "Deberían reflejar leads", estado="off" if conv_google == 0 else "ok")
ui.kpi(c3, "Conversiones Meta", num(conv_meta),
       "Deberían reflejar leads", estado="off" if conv_meta == 0 else "ok")
ui.kpi(c4, "Leads con click-id", num(int(ratio_atrib * leads_total)),
       f"de {num(leads_total)} leads UVic", estado="off" if ratio_atrib < 0.3 else "ok")

st.divider()

st.subheader("Diagnóstico")
st.markdown(f"""
El patrón es claro y consistente entre plataformas:

- **Hay demanda real**: HubSpot registra **{num(leads_total)} leads UVic** en el periodo.
- **Pero las plataformas atribuyen casi nada**: Google Ads marca **{conv_google}** y Meta **{conv_meta}**
  conversiones. No es falta de leads, es una **rotura de atribución**.
- **La campaña exacta se pierde**: los leads entran `OFFLINE / INTEGRATION` (sin `gclid`/`fbclid`).
  Por eso todo el dashboard asocia lead↔inversión **por programa** (vía `uvic_curso`), no por campaña.

**Causa raíz probable**: al enviar el formulario de la landing (Cloud Pages de Salesforce,
`cloud.info-uvic.cat`) se pierden el `gclid`/`fbclid` y las cookies `_fbc/_fbp`. Agravante en
Meta: la **Conversions API (CAPI) nunca se ha disparado**.
""")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Reparto de leads UVic por programa**")
    ui.donut(metrics.leads_por_programa_dist(leads), nombres="programa",
             valores="leads", titulo="")
with col_b:
    st.markdown("**Configuración de referencia**")
    st.markdown(f"""
    | Elemento | Valor |
    |---|---|
    | Píxel Meta (dataset) | `{config.META_PIXEL_DATASET_ID}` (Cloud Pages Pixel) |
    | Cuenta Meta | `{config.META_AD_ACCOUNT_ID}` |
    | Cuenta Google Ads | `{config.GOOGLE_ADS_CUSTOMER_ID}` |
    | Portal HubSpot | `{config.HUBSPOT_PORTAL_ID}` (Rise Education) |
    | Evento clave | `Lead` (dispara en la raíz de la landing) |
    """)

st.divider()

st.subheader("Plan de corrección (priorizado)")
ins = insights.generar(datos)
ui.tabla_recomendaciones(ins["recos"])
st.caption(
    "Prioridad = impacto × esfuerzo. El cuadrante **🔴 Hacer ya** (alto impacto, bajo esfuerzo) "
    "es capturar UTMs + click-IDs en el formulario de HubSpot y ampliar el etiquetado `uvic_curso`."
)
