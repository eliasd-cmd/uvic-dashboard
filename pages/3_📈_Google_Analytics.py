"""Página: Google Analytics 4 — tráfico de las 5 landings WeRise, por programa."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, num, pct

st.set_page_config(page_title="Google Analytics · UVic", page_icon="📈", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Google Analytics 4",
            f"Tráfico de las 5 landings WeRise · últimos {dias} días")

df = datos.ga4
if df.empty:
    st.warning("No hay datos de GA4.")
    st.stop()

tot_ses = int(df["sesiones"].sum())
tot_usr = int(df["usuarios"].sum())
tot_vis = int(df["vistas"].sum()) if "vistas" in df else 0
rebote = df["rebote"].mean() if "rebote" in df else 0
pags_ses = tot_vis / tot_ses if tot_ses else 0
t_ses = metrics.tendencia(df, "sesiones", "fecha")

c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Sesiones", num(tot_ses), delta=t_ses["delta"], delta_bueno=True)
ui.kpi(c2, "Usuarios", num(tot_usr), "Únicos")
ui.kpi(c3, "Páginas / sesión", f"{pags_ses:.2f}", "Profundidad de visita")
ui.kpi(c4, "Rebote medio", pct(rebote), f"Benchmark ≤ {pct(config.BENCH['rebote']['ok'],0)}",
       estado=config.estado_bench("rebote", rebote))

# --- Observaciones ---------------------------------------------------------- #
por_prog = df.groupby("programa", as_index=False).agg(
    sesiones=("sesiones", "sum"), rebote=("rebote", "mean"))
wins, concerns = [], []
if not por_prog.empty:
    top = por_prog.sort_values("sesiones", ascending=False).iloc[0]
    wins.append(f"Landing con más tráfico: **{top['programa']}** ({num(int(top['sesiones']))} sesiones).")
    peor = por_prog.sort_values("rebote", ascending=False).iloc[0]
    if config.estado_bench("rebote", peor["rebote"]) == "off":
        concerns.append(f"Rebote alto en **{peor['programa']}** ({pct(peor['rebote'])}): revisa coherencia anuncio→landing, velocidad y CTA.")
ui.caja_insights(wins, concerns)

st.divider()

st.subheader("Sesiones diarias por programa")
serie = df.groupby(["fecha", "programa"], as_index=False)["sesiones"].sum()
ui.linea_temporal(serie, x="fecha", y="sesiones", color="programa", titulo="", y_label="Sesiones")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Sesiones por programa")
    ui.barras(por_prog.sort_values("sesiones"), x="sesiones", y="programa",
              color=None, titulo="", orientacion="h")
with col_b:
    st.subheader("Reparto de tráfico")
    ui.donut(por_prog, nombres="programa", valores="sesiones", titulo="")

st.subheader("Detalle por landing")
detalle = df.groupby(["programa", "landing"], as_index=False).agg(
    sesiones=("sesiones", "sum"),
    usuarios=("usuarios", "sum"),
    vistas=("vistas", "sum"),
    rebote=("rebote", "mean"),
    duracion_media=("duracion_media", "mean"),
).sort_values("sesiones", ascending=False)
detalle["rebote"] = (detalle["rebote"] * 100).round(1)  # ratio -> %
st.dataframe(
    detalle, width='stretch', hide_index=True,
    column_config={
        "programa": "Programa",
        "landing": "Landing (ruta)",
        "sesiones": st.column_config.NumberColumn("Sesiones", format="%d"),
        "usuarios": st.column_config.NumberColumn("Usuarios", format="%d"),
        "vistas": st.column_config.NumberColumn("Páginas vistas", format="%d"),
        "rebote": st.column_config.NumberColumn("Rebote", format="%.1f%%"),
        "duracion_media": st.column_config.NumberColumn("Dur. media (s)", format="%.0f"),
    },
)
st.caption(
    "Solo tráfico de las 5 landings de programa en `cloud.info-uvic.cat`. "
    "Los leads/conversiones se miden en HubSpot (página *Leads*)."
)

st.divider()

# --- Tráfico por fuente / medio --------------------------------------------- #
st.subheader("Detalle por fuente / medio")
fm = datos.ga4_fuente
if fm.empty:
    st.info("Sin datos de fuente/medio.")
else:
    st.dataframe(
        fm[["fuente", "medio", "sesiones", "usuarios", "eventos", "eventos_clave"]],
        width='stretch', hide_index=True,
        column_config={
            "fuente": "Fuente", "medio": "Medio",
            "sesiones": st.column_config.NumberColumn("Sesiones", format="%d"),
            "usuarios": st.column_config.NumberColumn("Usuarios", format="%d"),
            "eventos": st.column_config.NumberColumn("Eventos", format="%d"),
            "eventos_clave": st.column_config.NumberColumn("Eventos clave", format="%d"),
        },
    )

# --- Tráfico por campaña ---------------------------------------------------- #
st.subheader("Detalle por campaña")
cg = datos.ga4_campana
if cg.empty:
    st.info("Sin datos de campaña.")
else:
    st.dataframe(
        cg[["campana", "sesiones", "usuarios", "eventos", "eventos_clave"]],
        width='stretch', hide_index=True,
        column_config={
            "campana": "Campaña",
            "sesiones": st.column_config.NumberColumn("Sesiones", format="%d"),
            "usuarios": st.column_config.NumberColumn("Usuarios", format="%d"),
            "eventos": st.column_config.NumberColumn("Eventos", format="%d"),
            "eventos_clave": st.column_config.NumberColumn("Eventos clave", format="%d"),
        },
    )
st.caption(
    "**Eventos** = total de interacciones registradas. **Eventos clave** = los marcados "
    "como conversión en GA4. Ambas tablas están filtradas a las 5 landings WeRise."
)
