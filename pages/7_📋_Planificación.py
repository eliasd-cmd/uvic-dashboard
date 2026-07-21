"""Página: Planificación trimestral (Jul–Ago–Sep) — Google Sheet en vivo.

Replica las 3 pestañas del Excel de marketing: TOTAL, Por Programa y Por
Plataforma. Se lee en vivo de una Google Sheet; si cambias el plan en la hoja,
el dashboard lo refleja al recargar (o con «Actualizar ahora»).
"""
from __future__ import annotations

import calendar
from datetime import date

import pandas as pd
import streamlit as st

from src.connectors import plan as plan_conn
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, badge_origen, eur, num, pct

_MESES = {"Julio": 7, "Agosto": 8, "Septiembre": 9}

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
# SECCIÓN PRINCIPAL — Real vs Plan (pacing y proyección a fin de mes)
# --------------------------------------------------------------------------- #
def _estado_meta(real: float, objetivo: float, mas_es_mejor: bool = True) -> str:
    """Semáforo de cumplimiento respecto a un objetivo."""
    if not objetivo:
        return "off"
    ratio = real / objetivo
    if mas_es_mejor:
        return "ok" if ratio >= 0.9 else ("warn" if ratio >= 0.6 else "off")
    return "ok" if ratio <= 1.0 else ("warn" if ratio <= 1.2 else "off")


st.subheader("Real vs Plan")
hoy = date.today()
mes_actual = {7: "Julio", 8: "Agosto", 9: "Septiembre"}.get(hoy.month, "Julio")
mes_sel = st.radio("Mes a comparar", list(_MESES.keys()),
                   index=list(_MESES).index(mes_actual), horizontal=True)

mes_num = _MESES[mes_sel]
inicio = date(hoy.year, mes_num, 1)
dias_mes = calendar.monthrange(hoy.year, mes_num)[1]
fin_mes = date(hoy.year, mes_num, dias_mes)
fin = min(hoy, fin_mes)

# Fracción del mes transcurrida (0 si es futuro, 1 si ya pasó).
if hoy < inicio:
    fraccion, dias_transc = 0.0, 0
elif hoy >= fin_mes:
    fraccion, dias_transc = 1.0, dias_mes
else:
    dias_transc = (hoy - inicio).days + 1
    fraccion = dias_transc / dias_mes

plan_mes = plan_conn.plan_total_mes(data, mes_sel.lower())

if fraccion == 0:
    st.info(f"**{mes_sel}** aún no ha empezado: aquí verás el avance real contra el plan cuando arranque.")
    real = dict(inversion=0.0, leads_total=0, cpl_neto=0.0, matriculas=0)
else:
    datos_real = loader.cargar_todo(inicio, fin)
    real = metrics.kpis_globales(datos_real.ads, datos_real.leads, datos_real.deals)
    st.caption(
        f"Comparando **{mes_sel}** · {dias_transc} de {dias_mes} días transcurridos "
        f"(**{pct(fraccion)}** del mes). La proyección estima el cierre de mes al ritmo actual."
    )

# Definición de las métricas a comparar.
comparables = [
    dict(titulo="Inversión", real=real["inversion"], plan=plan_mes.get("inversion"),
         fmt=lambda v: eur(v), mas="neutro", acum=True),
    dict(titulo="Leads", real=real["leads_total"], plan=plan_mes.get("leads"),
         fmt=lambda v: num(v), mas="mejor", acum=True),
    dict(titulo="CPL neto", real=real["cpl_neto"], plan=plan_mes.get("cpl"),
         fmt=lambda v: eur(v, 2), mas="menos", acum=False),
    dict(titulo="Matrículas", real=real["matriculas"], plan=plan_mes.get("matriculas"),
         fmt=lambda v: num(v), mas="mejor", acum=True),
]

cols = st.columns(len(comparables))
for col, c in zip(cols, comparables):
    real_v, plan_v, fmt = c["real"], c["plan"], c["fmt"]
    if plan_v is None:
        ui.kpi(col, c["titulo"], fmt(real_v), "Sin dato en el plan")
        continue
    if c["acum"]:
        objetivo_hoy = plan_v * fraccion
        cumpl = (real_v / objetivo_hoy) if objetivo_hoy else 0
        if c["mas"] == "mejor":
            estado = _estado_meta(real_v, objetivo_hoy, mas_es_mejor=True)
            delta = (cumpl - 1) if objetivo_hoy else None
            sub = f"Plan mes {fmt(plan_v)} · {pct(real_v / plan_v) if plan_v else '—'} del plan"
            ui.kpi(col, c["titulo"], fmt(real_v), sub, estado=estado,
                   delta=delta, delta_bueno=True)
        else:  # inversión: pacing neutro (ni bueno ni malo gastar de más/menos)
            estado = "ok" if 0.8 <= cumpl <= 1.2 else "warn"
            sub = f"Plan mes {fmt(plan_v)} · {pct(real_v / plan_v) if plan_v else '—'} consumido"
            ui.kpi(col, c["titulo"], fmt(real_v), sub, estado=estado)
    else:  # CPL: ratio, se compara directo (menos es mejor)
        estado = _estado_meta(real_v, plan_v, mas_es_mejor=False)
        delta = (real_v / plan_v - 1) if (plan_v and real_v) else None
        sub = f"Objetivo plan {fmt(plan_v)}"
        ui.kpi(col, c["titulo"], fmt(real_v) if real_v else "—", sub,
               estado=estado if real_v else None, delta=delta, delta_bueno=False)

# --- Tabla de proyección a fin de mes (la "tendencia") ---------------------- #
if fraccion > 0:
    filas = []
    for c in comparables:
        if c["plan"] is None or not c["acum"]:
            continue
        proy = c["real"] / fraccion if fraccion else 0
        cumpl_proy = proy / c["plan"] if c["plan"] else 0
        filas.append({
            "Métrica": c["titulo"],
            "Real a hoy": c["fmt"](c["real"]),
            "Objetivo a hoy": c["fmt"](c["plan"] * fraccion),
            "Plan del mes": c["fmt"](c["plan"]),
            "Proyección fin de mes": c["fmt"](proy),
            "% del plan (proy.)": pct(cumpl_proy),
        })
    if filas:
        st.markdown("**Proyección a fin de mes** (tendencia al ritmo actual)")
        st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
        st.caption(
            "**Objetivo a hoy** = plan del mes × % transcurrido. **Proyección** = real ÷ % "
            "transcurrido (dónde cerraría el mes si el ritmo se mantiene)."
        )

st.divider()
st.subheader("Detalle del plan")


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
