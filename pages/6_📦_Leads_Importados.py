"""Página: Leads IMPORTADOS y de WEBINAR — control aparte, fuera de captación.

Aquí caen: (1) leads antiguos importados (fuente de registro = IMPORT) y
(2) leads de webinar (uvic_utm_campaign contiene 'webinar').
NO cuentan en el resto del dashboard (no son captación de las campañas WeRise).
Cualquier lead nuevo que cumpla uno de los dos criterios aparece aquí solo.
"""
from __future__ import annotations

import streamlit as st

from src.data import loader
from src.ui import components as ui
from src.ui.theme import aplicar_tema, badge_origen, eur, num, pct

st.set_page_config(page_title="Leads Importados · UVic", page_icon="📦", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes, datos.detalles)

ui.cabecera("Leads Importados y de Webinar",
            "Control aparte · importados (fuente = IMPORT) y leads de webinar (UTM campaign), fuera del cómputo de campañas")

li = datos.leads_import
ni = datos.negocios_import

st.markdown(
    f"Origen de estos datos: {badge_origen(datos.origen_import)}", unsafe_allow_html=True)

if li.empty:
    st.info("No hay leads importados detectados. 👍")
    st.stop()

# --- KPIs -------------------------------------------------------------------- #
total = len(li)
n_webinar = int((li["motivo"] == "Webinar").sum()) if "motivo" in li else 0
n_import = total - n_webinar
con_negocio = int((li["n_negocios"] > 0).sum()) if "n_negocios" in li else 0
n_negocios = len(ni)
en_curso = int((~li["estado"].isin(["Descartado", "Matriculado"])).sum()) if "estado" in li else 0

c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Leads fuera de captación", num(total),
       f"{num(n_import)} importados · {num(n_webinar)} webinar")
ui.kpi(c2, "Con negocio asociado", num(con_negocio), f"{pct(con_negocio/total if total else 0)}")
ui.kpi(c3, "Negocios totales", num(n_negocios), "Deals de estos leads")
ui.kpi(c4, "En curso", num(en_curso), "Ni descartados ni matriculados")

st.caption(
    "⚠️ Estos leads **no** se incluyen en el Resumen, Google/Meta/GA4 ni en la página de Leads: "
    "los importados no provienen de las campañas actuales y los de webinar son captación aparte. "
    "Esta hoja es solo para gestionarlos por separado."
)

st.divider()

# --- Distribuciones ---------------------------------------------------------- #
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Importados por programa")
    por_prog = li.groupby("programa", as_index=False)["lead_id"].count().rename(
        columns={"lead_id": "leads"})
    ui.barras(por_prog.sort_values("leads"), x="leads", y="programa",
              color=None, titulo="", orientacion="h")
with col_b:
    if "motivo" in li.columns and li["motivo"].nunique() > 1:
        st.subheader("Por motivo")
        por_mot = li.groupby("motivo", as_index=False)["lead_id"].count().rename(
            columns={"lead_id": "leads"})
        ui.donut(por_mot, nombres="motivo", valores="leads", titulo="")
    else:
        st.subheader("Por estado")
        por_est = li.groupby("estado", as_index=False)["lead_id"].count().rename(
            columns={"lead_id": "leads"})
        ui.donut(por_est, nombres="estado", valores="leads", titulo="")

st.divider()

# --- Tabla de leads ---------------------------------------------------------- #
st.subheader(f"Leads importados y de webinar ({total})")
if "motivo" in li.columns:
    sel_m = st.multiselect("Filtrar por motivo", sorted(li["motivo"].unique()),
                           placeholder="Todos los motivos")
    li_f = li[li["motivo"].isin(sel_m)] if sel_m else li
else:
    li_f = li
cols = [c for c in ["nombre", "email", "fecha_creacion", "motivo", "campana",
                    "programa", "nivel", "estado", "lead_status", "n_negocios"]
        if c in li_f.columns]
st.dataframe(
    li_f.sort_values("fecha_creacion", ascending=False)[cols],
    width='stretch', hide_index=True,
    column_config={
        "nombre": "Nombre", "email": "Email", "fecha_creacion": "Creado",
        "motivo": "Motivo", "campana": "Campaña UTM",
        "programa": "Programa", "nivel": "Nivel estudios",
        "estado": "Estado (ciclo de vida)", "lead_status": "Estado del lead",
        "n_negocios": st.column_config.NumberColumn("Nº negocios", format="%d"),
    },
)

# --- Tabla de negocios ------------------------------------------------------- #
if not ni.empty:
    st.subheader(f"Negocios de estos leads ({len(ni)})")
    ni2 = ni.copy()
    if "contacto" in ni2 and "lead_id" in li:
        nombres = li.set_index("lead_id")["nombre"].to_dict()
        ni2["lead"] = ni2["contacto"].map(nombres).fillna(ni2["contacto"])
    st.dataframe(
        ni2[[c for c in ["dealname", "lead", "pipeline", "etapa", "importe", "fecha_creacion"]
             if c in ni2.columns]],
        width='stretch', hide_index=True,
        column_config={
            "dealname": "Negocio", "lead": "Lead", "pipeline": "Pipeline",
            "etapa": "Etapa", "importe": st.column_config.NumberColumn("Importe", format="%.0f €"),
            "fecha_creacion": "Creado",
        },
    )
else:
    st.caption("Ninguno de los leads importados tiene negocios asociados.")

st.caption(
    "Esta hoja se actualiza sola: cualquier contacto con `uvic_curso` cuya **fuente de registro "
    "sea IMPORT** o cuya **`uvic_utm_campaign` contenga 'webinar'** aparece aquí y queda fuera "
    "del resto del dashboard (leads y negocios)."
)
