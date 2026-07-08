"""Página: Google Analytics 4 (tráfico y conversiones por canal)."""
from __future__ import annotations

import streamlit as st

from src.data import loader
from src.ui import components as ui
from src.ui.theme import aplicar_tema, num, pct

st.set_page_config(page_title="Google Analytics · UVic", page_icon="📈", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Google Analytics 4", f"Tráfico y conversiones · últimos {dias} días")

df = datos.ga4
if df.empty:
    st.warning("No hay datos de GA4.")
    st.stop()

tot_sesiones = int(df["sesiones"].sum())
tot_usuarios = int(df["usuarios"].sum())
tot_conv = int(df["conversiones"].sum())
rebote_medio = df["rebote"].mean()

c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Sesiones", num(tot_sesiones))
ui.kpi(c2, "Usuarios", num(tot_usuarios))
ui.kpi(c3, "Conversiones", num(tot_conv),
       f"CVR {pct(tot_conv/tot_sesiones if tot_sesiones else 0,2)}")
ui.kpi(c4, "Rebote medio", pct(rebote_medio))

st.divider()

st.subheader("Sesiones diarias por canal")
serie = df.groupby(["fecha", "canal"], as_index=False)["sesiones"].sum()
ui.linea_temporal(serie, x="fecha", y="sesiones", color="canal",
                  titulo="", y_label="Sesiones")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Sesiones por canal")
    por_canal = df.groupby("canal", as_index=False)["sesiones"].sum().sort_values("sesiones", ascending=False)
    ui.barras(por_canal, x="sesiones", y="canal", color=None, titulo="", orientacion="h")
with col_b:
    st.subheader("Conversiones por canal")
    conv_canal = df.groupby("canal", as_index=False)["conversiones"].sum().sort_values("conversiones", ascending=False)
    ui.donut(conv_canal, nombres="canal", valores="conversiones", titulo="")

st.subheader("Detalle por canal")
detalle = df.groupby("canal", as_index=False).agg(
    sesiones=("sesiones", "sum"),
    usuarios=("usuarios", "sum"),
    conversiones=("conversiones", "sum"),
    rebote=("rebote", "mean"),
    duracion_media=("duracion_media", "mean"),
).sort_values("sesiones", ascending=False)
detalle["cvr"] = detalle["conversiones"] / detalle["sesiones"].replace(0, 1)
st.dataframe(
    detalle, width='stretch', hide_index=True,
    column_config={
        "canal": "Canal",
        "sesiones": st.column_config.NumberColumn("Sesiones", format="%d"),
        "usuarios": st.column_config.NumberColumn("Usuarios", format="%d"),
        "conversiones": st.column_config.NumberColumn("Conv.", format="%d"),
        "cvr": st.column_config.NumberColumn("CVR", format="%.2f%%"),
        "rebote": st.column_config.NumberColumn("Rebote", format="%.1f%%"),
        "duracion_media": st.column_config.NumberColumn("Dur. media (s)", format="%.0f"),
    },
)
st.caption(
    "Nota: GA4 requiere Property ID y Service Account en `secrets.toml`. Conecta "
    "Paid Search / Paid Social con UTMs consistentes para cruzar con Ads y HubSpot."
)
