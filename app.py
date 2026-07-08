"""
Dashboard de Marketing — UVic / WeRise
Página principal: Resumen Global (inversión, leads, CPL, ROAS y objetivo de matrículas).

Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, eur, num, pct

st.set_page_config(
    page_title="UVic · Dashboard Marketing",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
aplicar_tema()

# --------------------------------------------------------------------------- #
# Datos
# --------------------------------------------------------------------------- #
dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

k = metrics.kpis_globales(datos.ads, datos.leads, datos.deals)

# --------------------------------------------------------------------------- #
# Cabecera
# --------------------------------------------------------------------------- #
ui.cabecera(
    "Resumen Global",
    f"Últimos {dias} días · Objetivo Etapa 1: {config.OBJETIVO_MATRICULAS} matrículas "
    f"con ~{eur(config.OBJETIVO_INVERSION_MENSUAL)}/mes",
)

# --------------------------------------------------------------------------- #
# Fila 1 de KPIs — inversión y eficiencia
# --------------------------------------------------------------------------- #
c1, c2, c3, c4 = st.columns(4)
pace = k["inversion"] / config.OBJETIVO_INVERSION_MENSUAL if config.OBJETIVO_INVERSION_MENSUAL else 0
ui.kpi(c1, "Inversión total", eur(k["inversion"]),
       f"{pct(pace)} del objetivo mensual",
       estado="ok" if pace <= 1.05 else "warn")
ui.kpi(c2, "Leads UVic (HubSpot)", num(k["leads_total"]),
       f"Contactos con programa (uvic_curso)")
ui.kpi(c3, "CPL neto", eur(k["cpl_neto"], 2),
       f"Objetivo ≤ {eur(config.CPL_OBJETIVO, 0)}",
       estado="ok" if 0 < k["cpl_neto"] <= config.CPL_OBJETIVO else "warn")
ui.kpi(c4, "ROAS", f"{num(k['roas'],2)}×",
       f"Ingresos est.: {eur(k['ingresos'])}",
       estado="ok" if k["roas"] >= 3 else ("warn" if k["roas"] >= 1 else "off"))

st.write("")

# --------------------------------------------------------------------------- #
# Fila 2 de KPIs — matrículas y atribución
# --------------------------------------------------------------------------- #
c5, c6, c7, c8 = st.columns(4)
pace_mat = k["matriculas"] / config.OBJETIVO_MATRICULAS if config.OBJETIVO_MATRICULAS else 0
ui.kpi(c5, "Matrículas", f"{num(k['matriculas'])} / {config.OBJETIVO_MATRICULAS}",
       f"{pct(pace_mat)} del objetivo",
       estado="ok" if pace_mat >= 0.9 else ("warn" if pace_mat >= 0.5 else "off"))
ui.kpi(c6, "Coste por matrícula", eur(k["cp_matricula"]),
       "Inversión / matrículas")
ui.kpi(c7, "Deals Pipeline UVIC", num(k["deals_totales"]),
       "Oportunidades en curso")
ui.kpi(c8, "Forecast matrículas", num(k["matriculas_forecast"], 1),
       f"Con tasa {pct(config.TASA_LEAD_A_MATRICULA)} sobre leads")

st.divider()

# --------------------------------------------------------------------------- #
# Gráficos principales
# --------------------------------------------------------------------------- #
col_izq, col_der = st.columns([0.58, 0.42])

with col_izq:
    st.subheader("Inversión diaria por plataforma")
    ui.linea_temporal(
        metrics.serie_diaria_inversion(datos.ads),
        x="fecha", y="coste", color="plataforma",
        titulo="", y_label="€/día",
    )

with col_der:
    st.subheader("Reparto de inversión")
    resumen = metrics.resumen_plataforma(datos.ads)
    if not resumen.empty:
        ui.donut(resumen, nombres="plataforma", valores="coste", titulo="")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Embudo Pipeline UVIC (deals)")
    st.caption("Oportunidad → Entrevista → Envío inscripción → Cierre ganado (= matrícula).")
    ui.embudo_chart(metrics.embudo(datos.deals))
with col_b:
    st.subheader("Leads UVic por programa")
    st.caption(
        "Atribución de campaña perdida (leads llegan OFFLINE); se asocian por "
        "programa vía la propiedad `uvic_curso`."
    )
    ui.donut(metrics.leads_por_programa_dist(datos.leads),
             nombres="programa", valores="leads", titulo="")

st.divider()

# --------------------------------------------------------------------------- #
# Tabla resumen por campaña (inversión + leads + ROAS)
# --------------------------------------------------------------------------- #
st.subheader("Rendimiento por programa")
cruce = metrics.cruce_inversion_leads(datos.ads, datos.leads, datos.deals)
if not cruce.empty:
    tabla = cruce[[
        "programa", "coste", "clics", "leads", "matriculas",
        "cpl", "cp_matricula", "roas",
    ]].copy()
    st.dataframe(
        tabla,
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
    st.caption(
        "**Inversión (G+M)** = Google Ads + Meta de las campañas de ese programa. "
        "**CPL** = inversión del programa / leads (uvic_curso) de ese programa. "
        "La campaña exacta no se puede aislar (atribución OFFLINE); por eso todo es por programa."
    )

st.caption(
    "Navega por las páginas de la izquierda para el detalle de Google Ads, "
    "Meta Ads, Google Analytics, Leads (HubSpot) y salud del tracking."
)
