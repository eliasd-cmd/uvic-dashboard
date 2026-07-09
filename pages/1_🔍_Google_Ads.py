"""Página: detalle de Google Ads (búsqueda) — con benchmarks, tendencia e insights."""
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

ui.cabecera("Google Ads", f"Cuenta {config.GOOGLE_ADS_CUSTOMER_ID} · búsqueda WeRise · últimos {dias} días")

df = datos.google
if df.empty:
    st.warning("No hay datos de Google Ads.")
    st.stop()

r = metrics.resumen_plataforma(df).iloc[0]
t_inv = metrics.tendencia(df, "coste", "fecha")
cpa = r["coste"] / r["conversiones"] if r["conversiones"] else 0

c1, c2, c3, c4, c5 = st.columns(5)
ui.kpi(c1, "Inversión", eur(r["coste"]), delta=t_inv["delta"], delta_bueno=True)
ui.kpi(c2, "Impresiones", num(r["impresiones"]), "Alcance de búsqueda")
ui.kpi(c3, "CTR", pct(r["ctr"], 2), f"Benchmark ≥ {pct(config.BENCH['ctr_search']['ok'],0)}",
       estado=config.estado_bench("ctr_search", r["ctr"]))
ui.kpi(c4, "CPC medio", eur(r["cpc"], 2), f"Benchmark ≤ {eur(config.BENCH['cpc_search']['ok'],1)}",
       estado=config.estado_bench("cpc_search", r["cpc"]))
ui.kpi(c5, "Conversiones", num(r["conversiones"]),
       "Tracking roto" if r["conversiones"] == 0 else f"CPA {eur(cpa)}",
       estado="off" if r["conversiones"] == 0 else "ok")

# --- Observaciones automáticas ---------------------------------------------- #
camp = metrics.resumen_campana(df)
wins, concerns = [], []
if r["conversiones"] <= 1:
    concerns.append(
        f"**{int(r['conversiones'])} conversiones** registradas pese a {eur(r['coste'])} de gasto: "
        "el tracking no atribuye. Los leads reales están en HubSpot (página *Leads*)."
    )
if not camp.empty:
    mejor = camp.sort_values("ctr", ascending=False).iloc[0]
    wins.append(f"Mejor CTR: **{mejor['programa']}** ({pct(mejor['ctr'],2)}, CPC {eur(mejor['cpc'],2)}).")
    caro = camp.sort_values("cpc", ascending=False).iloc[0]
    if config.estado_bench("cpc_search", caro["cpc"]) == "off":
        concerns.append(f"CPC alto en **{caro['programa']}** ({eur(caro['cpc'],2)}): revisa puja y Quality Score.")
ui.caja_insights(wins, concerns)

st.divider()

st.subheader("Inversión y clics diarios")
serie = df.groupby("fecha", as_index=False).agg(coste=("coste", "sum"), clics=("clics", "sum"))
ui.linea_temporal(serie, x="fecha", y="coste", color=None, titulo="Inversión €/día", y_label="€")

st.subheader("Rendimiento por campaña")
ui.barras(camp.head(10), x="coste", y="campana", color="programa",
          titulo="Inversión por campaña", orientacion="h")
tab = camp[["campana", "programa", "impresiones", "clics", "ctr", "cpc", "coste", "conversiones"]].copy()
tab["ctr"] = (tab["ctr"] * 100).round(2)  # ratio -> %
st.dataframe(
    tab, width='stretch', hide_index=True,
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
    "Las 5 campañas `WeRise_Search_NAC_` traen el grueso de leads cualificados. "
    "El CPL real por programa está en la página *Leads (HubSpot)*."
)
