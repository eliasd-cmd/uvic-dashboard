"""Página: detalle de Meta Ads (social) — con benchmarks, tendencia e insights."""
from __future__ import annotations

import streamlit as st

from src import config
from src.data import loader, metrics
from src.ui import components as ui
from src.ui.theme import aplicar_tema, eur, num, pct

st.set_page_config(page_title="Meta Ads · UVic", page_icon="📱", layout="wide")
aplicar_tema()

dias = ui.selector_periodo(30)
datos = loader.cargar_todo(dias)
ui.aviso_origenes(datos.origenes)

ui.cabecera("Meta Ads", f"Cuenta {config.META_AD_ACCOUNT_ID} · social WeRise · últimos {dias} días")

df = datos.meta
if df.empty:
    st.warning("No hay datos de Meta Ads.")
    st.stop()

r = metrics.resumen_plataforma(df).iloc[0]
t_inv = metrics.tendencia(df, "coste", "fecha")

c1, c2, c3, c4, c5 = st.columns(5)
ui.kpi(c1, "Inversión", eur(r["coste"]), delta=t_inv["delta"], delta_bueno=True)
ui.kpi(c2, "Impresiones", num(r["impresiones"]), "Alcance social")
ui.kpi(c3, "CTR", pct(r["ctr"], 2), f"Benchmark ≥ {pct(config.BENCH['ctr_social']['ok'],1)}",
       estado=config.estado_bench("ctr_social", r["ctr"]))
ui.kpi(c4, "CPC medio", eur(r["cpc"], 2), f"Benchmark ≤ {eur(config.BENCH['cpc_social']['ok'],2)}",
       estado=config.estado_bench("cpc_social", r["cpc"]))
ui.kpi(c5, "CPM", eur(r["cpm"], 2), f"Benchmark ≤ {eur(config.BENCH['cpm_social']['ok'],1)}",
       estado=config.estado_bench("cpm_social", r["cpm"]))

# Leads UVic totales (contexto): Meta no atribuye, se ve por programa en HubSpot.
leads_uvic = len(datos.leads)
st.warning(
    f"Meta atribuye **{int(r['conversiones'])} conversiones** en la plataforma, pero HubSpot "
    f"registra **{num(leads_uvic)} leads UVic** en el periodo. Es la **rotura de atribución** "
    "(Cloud Pages / pérdida de `fbclid`), no falta de demanda. Ver *Tracking & Atribución*."
)

# --- Observaciones automáticas ---------------------------------------------- #
camp = metrics.resumen_campana(df)
wins, concerns = [], []
if not camp.empty:
    mejor = camp.sort_values("ctr", ascending=False).iloc[0]
    wins.append(f"Mejor CTR: **{mejor['programa']}** ({pct(mejor['ctr'],2)}, CPC {eur(mejor['cpc'],2)}).")
    caro = camp.sort_values("cpc", ascending=False).iloc[0]
    if config.estado_bench("cpc_social", caro["cpc"]) == "off":
        concerns.append(f"CPC social alto en **{caro['programa']}** ({eur(caro['cpc'],2)}): posible fatiga de creatividad.")
        concerns.append("Refresca creatividades cada 2 semanas para frenar la fatiga (CPM al alza).")
ui.caja_insights(wins, concerns)

st.divider()

st.subheader("Inversión y clics diarios")
serie = df.groupby("fecha", as_index=False).agg(coste=("coste", "sum"), clics=("clics", "sum"))
ui.linea_temporal(serie, x="fecha", y="coste", color=None, titulo="Inversión €/día", y_label="€")

st.subheader("Rendimiento por campaña")
ui.barras(camp, x="coste", y="campana", color="programa",
          titulo="Inversión por campaña", orientacion="h")
tab = camp[["campana", "programa", "impresiones", "clics", "ctr", "cpc", "coste"]].copy()
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
    },
)
