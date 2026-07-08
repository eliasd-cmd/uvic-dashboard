"""Página: salud del tracking y de la atribución (diagnóstico Google/Meta/HubSpot)."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, num, pct

st.set_page_config(page_title="Tracking & Atribución · UVic", page_icon="🩺", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Tracking & Atribución", "Salud de la medición end-to-end")

leads = datos.leads
ads = datos.ads

# --- Indicadores de salud ---------------------------------------------------
conv_google = int(datos.google["conversiones"].sum()) if not datos.google.empty else 0
conv_meta = int(datos.meta["conversiones"].sum()) if not datos.meta.empty else 0
leads_total = len(leads)
# La campaña se pierde (OFFLINE); medimos cuántos leads llegan CON click-id de campaña.
atribuidos = int((leads["campana"].astype(str).str.len() > 0).sum()) if "campana" in leads else 0
pct_atrib = atribuidos / leads_total if leads_total else 0

st.subheader("Semáforo de medición")
c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Conversiones Google Ads", num(conv_google),
       "Deberían reflejar leads", estado="off" if conv_google == 0 else "ok")
ui.kpi(c2, "Conversiones Meta Ads", num(conv_meta),
       "Deberían reflejar leads", estado="off" if conv_meta == 0 else "ok")
ui.kpi(c3, "Leads UVic (HubSpot)", num(leads_total),
       "La demanda SÍ existe", estado="ok")
ui.kpi(c4, "Leads con campaña (click-id)", num(atribuidos),
       "Casi 0 → atribución rota", estado="off" if pct_atrib < 0.3 else "ok")

st.divider()

# --- Diagnóstico narrativo --------------------------------------------------
st.subheader("Diagnóstico")
st.markdown(f"""
El patrón es claro y consistente entre plataformas:

- **Hay demanda real**: HubSpot registra **{num(leads_total)} leads** en el periodo.
- **Pero las plataformas atribuyen casi nada**: Google Ads marca **{conv_google}**
  conversiones y Meta **{conv_meta}**. No es falta de leads, es una **rotura de atribución**.
- **Solo {num(atribuidos)} de {num(leads_total)} leads** llegan con campaña identificable (el resto entra OFFLINE vía integración).

**Causa raíz probable**: al enviar el formulario de la landing (Cloud Pages de
Salesforce, dominio `cloud.info-uvic.cat`) se pierden el `gclid`/`fbclid` y las
cookies `_fbc/_fbp`, de modo que el lead no se enlaza con el clic. Agravante en
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
    | Evento clave | `Lead` (dispara en la raíz de la landing) |
    """)

st.divider()

# --- Checklist de acciones --------------------------------------------------
st.subheader("Plan de corrección (checklist)")
acciones = [
    ("Preservar `gclid`/`fbclid` a través del formulario y la redirección a la raíz", "Alta", "Media"),
    ("Capturar UTMs + click IDs en campos ocultos del form de HubSpot", "Alta", "Baja"),
    ("Verificar en Ads Manager que el conjunto usa Cloud Pages Pixel + evento Lead", "Alta", "Baja"),
    ("Activar Conversions API (CAPI) en Meta y enviar `fbc` en el evento Lead", "Alta", "Media"),
    ("Configurar/enlazar la conversión de Google Ads con el lead de HubSpot (offline conversions)", "Alta", "Media"),
    ("Poner el evento Lead también en las páginas de programa (no solo raíz)", "Media", "Baja"),
    ("Validar en Test Events que el Lead llega con `fbc`", "Media", "Baja"),
]
st.dataframe(
    {"Acción": [a[0] for a in acciones],
     "Impacto": [a[1] for a in acciones],
     "Esfuerzo": [a[2] for a in acciones]},
    width='stretch', hide_index=True,
)
st.caption(
    "Prioriza el cuadrante Alto impacto / Bajo esfuerzo: capturar UTMs+clickIDs en el "
    "formulario de HubSpot y verificar el píxel del conjunto de anuncios."
)
