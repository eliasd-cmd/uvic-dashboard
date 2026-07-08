"""Página: Leads (HubSpot) — leads UVic por programa, CPL y embudo del Pipeline UVIC."""
from __future__ import annotations

import streamlit as st

from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, eur, num, pct

st.set_page_config(page_title="Leads · HubSpot", page_icon="🎯", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Leads · HubSpot", f"Rise Education · leads UVic por programa · últimos {dias} días")

leads = datos.leads
deals = datos.deals
if leads.empty and deals.empty:
    st.warning("No hay datos de HubSpot.")
    st.stop()

total = len(leads)
con_programa = int((leads["programa"] != "Sin asignar").sum()) if total else 0
deals_tot = len(deals)
matriculas = int(deals["es_ganado"].sum()) if not deals.empty else 0

c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Leads UVic", num(total), "Contactos con uvic_curso")
ui.kpi(c2, "Con programa", num(con_programa),
       f"{pct(con_programa/total if total else 0)}",
       estado="ok" if total and con_programa/total >= 0.9 else "warn")
ui.kpi(c3, "Deals Pipeline UVIC", num(deals_tot), "Oportunidades")
ui.kpi(c4, "Matrículas", num(matriculas), "Deals en 'Cierre ganado'",
       estado="ok" if matriculas > 0 else "off")

st.divider()

col_a, col_b = st.columns([0.55, 0.45])
with col_a:
    st.subheader("Leads por programa")
    por_prog = metrics.resumen_leads_por_programa(leads)
    ui.barras(por_prog.sort_values("leads"), x="leads", y="programa",
              color=None, titulo="", orientacion="h")
with col_b:
    st.subheader("Embudo Pipeline UVIC")
    ui.embudo_chart(metrics.embudo(deals))

st.divider()

st.subheader("Inversión ↔ leads por programa (CPL, coste/matrícula, ROAS)")
cruce = metrics.cruce_inversion_leads(datos.ads, leads, deals)
if not cruce.empty:
    st.dataframe(
        cruce[["programa", "coste", "clics", "leads", "matriculas",
               "cpl", "cp_matricula", "roas"]],
        width='stretch', hide_index=True,
        column_config={
            "programa": "Programa",
            "coste": st.column_config.NumberColumn("Inversión (G+M)", format="%.0f €"),
            "clics": st.column_config.NumberColumn("Clics", format="%d"),
            "leads": st.column_config.NumberColumn("Leads", format="%d"),
            "matriculas": st.column_config.NumberColumn("Matrículas", format="%d"),
            "cpl": st.column_config.NumberColumn("CPL", format="%.2f €"),
            "cp_matricula": st.column_config.NumberColumn("Coste/matrícula", format="%.0f €"),
            "roas": st.column_config.NumberColumn("ROAS", format="%.2f×"),
        },
    )

st.subheader("Leads recientes")
cols = [c for c in ["lead_id", "fecha_creacion", "programa", "nivel", "estado", "fuente"]
        if c in leads.columns]
st.dataframe(
    leads.sort_values("fecha_creacion", ascending=False).head(50)[cols],
    width='stretch', hide_index=True,
    column_config={
        "lead_id": "ID", "fecha_creacion": "Creado", "programa": "Programa",
        "nivel": "Nivel estudios", "estado": "Estado", "fuente": "Fuente",
    },
)
st.caption(
    "La campaña exacta no se captura (los leads entran OFFLINE vía integración → se "
    "pierde el gclid/fbclid). La asociación con inversión se hace **por programa** "
    "mediante la propiedad `uvic_curso`. Recuperar el click-id es la palanca #1 para "
    "medir CPL por campaña."
)
