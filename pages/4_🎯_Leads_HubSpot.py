"""Página: Leads (HubSpot) — leads UVic por programa, CPL, embudo y tasas de conversión."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, eur, num, pct

st.set_page_config(page_title="Leads · HubSpot", page_icon="🎯", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes, datos.detalles)

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
t_leads = metrics.tendencia(metrics.serie_diaria_leads(leads), "leads", "fecha")

c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Leads UVic", num(total), "Contactos con uvic_curso",
       delta=t_leads["delta"], delta_bueno=True)
ui.kpi(c2, "Oportunidades", num(deals_tot),
       f"Lead→Oport. {pct(deals_tot/total if total else 0)}")
ui.kpi(c3, "Matrículas", num(matriculas),
       f"Lead→Matríc. {pct(matriculas/total if total else 0)}",
       estado="ok" if matriculas > 0 else "off")
ui.kpi(c4, "Con programa", pct(con_programa/total if total else 0),
       "Leads con uvic_curso",
       estado="ok" if total and con_programa/total >= 0.9 else "warn")

# --- Observaciones ---------------------------------------------------------- #
cruce = metrics.cruce_inversion_leads(datos.ads, leads, deals)
wins, concerns = [], []
con_leads = cruce[cruce["leads"] > 0] if not cruce.empty else cruce
if not con_leads.empty:
    mejor = con_leads.sort_values("cpl").iloc[0]
    wins.append(f"Programa más eficiente: **{mejor['programa']}** (CPL {eur(mejor['cpl'],2)}).")
    peor = con_leads.sort_values("cpl").iloc[-1]
    if len(con_leads) > 1 and peor["cpl"] > mejor["cpl"] * 1.5:
        concerns.append(f"CPL más caro: **{peor['programa']}** ({eur(peor['cpl'],2)}).")
if total and con_programa / total < 0.95:
    concerns.append(f"Solo el {pct(con_programa/total)} de leads tiene `uvic_curso`: mejora el etiquetado para medir bien el CPL.")
ui.caja_insights(wins, concerns)

st.divider()

col_a, col_b = st.columns([0.5, 0.5])
with col_a:
    st.subheader("Leads por programa")
    por_prog = metrics.resumen_leads_por_programa(leads)
    ui.barras(por_prog.sort_values("leads"), x="leads", y="programa",
              color=None, titulo="", orientacion="h")
with col_b:
    st.subheader("Embudo Pipeline UVIC")
    ui.embudo_chart(metrics.embudo(deals))

st.subheader("Tasas de conversión del embudo")
te = metrics.tasas_embudo(deals)
if not te.empty:
    te2 = te.copy()
    te2["pct"] = (te2["pct"] * 100).round(1)
    te2["conv_paso"] = (te2["conv_paso"] * 100).round(1)
    st.dataframe(
        te2[["etapa", "leads", "pct", "conv_paso"]],
        width='stretch', hide_index=True,
        column_config={
            "etapa": "Etapa",
            "leads": st.column_config.NumberColumn("Deals", format="%d"),
            "pct": st.column_config.NumberColumn("% del total", format="%.1f%%"),
            "conv_paso": st.column_config.NumberColumn("Conv. desde anterior", format="%.1f%%"),
        },
    )

st.divider()

st.subheader("Inversión ↔ leads por programa (CPL, coste/matrícula, ROAS)")
if not cruce.empty:
    tab = cruce[["programa", "coste", "clics", "leads", "cpl",
                 "matriculas", "cp_matricula", "roas"]].copy()
    st.dataframe(
        tab, width='stretch', hide_index=True,
        column_config={
            "programa": "Programa",
            "coste": st.column_config.NumberColumn("Inversión (G+M)", format="%.0f €"),
            "clics": st.column_config.NumberColumn("Clics", format="%d"),
            "leads": st.column_config.NumberColumn("Leads", format="%d"),
            "cpl": st.column_config.NumberColumn("CPL", format="%.2f €"),
            "matriculas": st.column_config.NumberColumn("Matrículas", format="%d"),
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
    "La campaña exacta no se captura (leads OFFLINE → se pierde gclid/fbclid). La asociación "
    "con inversión es **por programa** vía `uvic_curso`. Recuperar el click-id es la palanca #1 "
    "para medir CPL por campaña."
)
