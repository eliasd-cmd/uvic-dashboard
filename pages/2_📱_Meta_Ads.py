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
ui.aviso_origenes(datos.origenes, datos.detalles)

ui.cabecera("Meta Ads", f"Cuenta {config.META_AD_ACCOUNT_ID} · social WeRise · últimos {dias} días")

df = datos.meta
if df.empty:
    st.warning("No hay datos de Meta Ads.")
    st.stop()

r = metrics.resumen_plataforma(df).iloc[0]
t_inv = metrics.tendencia(df, "coste", "fecha")
resultados = int(r["conversiones"])                       # leads web atribuidos por Meta
tasa_resultados = resultados / r["clics"] if r["clics"] else 0
coste_resultado = r["coste"] / resultados if resultados else 0

# CPL real: eventos clave de GA4 llegados desde fuentes Meta (meta/fb/ig/an).
_FUENTES_META = {"meta", "fb", "ig", "an", "facebook", "instagram"}
ev_meta = 0
gf = datos.ga4_fuente
if not gf.empty and "fuente" in gf.columns and "eventos_clave" in gf.columns:
    ev_meta = int(gf[gf["fuente"].str.lower().isin(_FUENTES_META)]["eventos_clave"].sum())
cpl_real = r["coste"] / ev_meta if ev_meta else 0

st.subheader("Volumen y coste")
c1, c2, c3, c4 = st.columns(4)
ui.kpi(c1, "Inversión", eur(r["coste"]), delta=t_inv["delta"], delta_bueno=True)
ui.kpi(c2, "Impresiones", num(r["impresiones"]), "Alcance social")
ui.kpi(c3, "Clics", num(r["clics"]), f"CTR {pct(r['ctr'],2)}",
       estado=config.estado_bench("ctr_social", r["ctr"]))
ui.kpi(c4, "CPM", eur(r["cpm"], 2), f"Benchmark ≤ {eur(config.BENCH['cpm_social']['ok'],1)}",
       estado=config.estado_bench("cpm_social", r["cpm"]))

st.subheader("Eficiencia y resultado")
c5, c6, c7, c8 = st.columns(4)
ui.kpi(c5, "CPC medio", eur(r["cpc"], 2), f"Benchmark ≤ {eur(config.BENCH['cpc_social']['ok'],2)}",
       estado=config.estado_bench("cpc_social", r["cpc"]))
ui.kpi(c6, "Resultados (leads web)", num(resultados),
       f"Tasa {pct(tasa_resultados,2)} sobre clics",
       estado="ok" if resultados > 0 else "off")
ui.kpi(c7, "Coste/resultado", eur(coste_resultado, 2) if resultados else "—",
       "Inversión / resultados Meta",
       estado=config.estado_bench("cpl", coste_resultado) if resultados else "off")
ui.kpi(c8, "CPL real (GA4)", eur(cpl_real, 2) if ev_meta else "—",
       f"{num(ev_meta)} eventos clave · fuentes Meta",
       estado=config.estado_bench("cpl", cpl_real) if ev_meta else None)

if resultados == 0:
    st.warning(
        f"Meta no está atribuyendo conversiones pese a que HubSpot registra "
        f"**{num(len(datos.leads))} leads UVic**. Revisa la página *Tracking & Atribución*."
    )
else:
    st.caption(
        f"Meta atribuye **{num(resultados)}** leads web · GA4 registra **{num(ev_meta)}** eventos clave "
        f"de fuentes Meta · HubSpot tiene **{num(len(datos.leads))}** leads UVic (todas las fuentes, "
        "asociados por programa)."
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
