"""
Motor de insights y recomendaciones automáticas (alineado con la skill
performance-report: "What worked", "What needs improvement", "Recommendations").

Genera, a partir de los datos reales, tres listas:
  - wins:      logros / cosas que funcionan (verde)
  - concerns:  problemas / lo que hay que mejorar (rojo)
  - recos:     recomendaciones priorizadas [{texto, impacto, esfuerzo}]
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.data import metrics
from src.ui.theme import eur, num, pct


def generar(datos) -> dict:
    wins: list[str] = []
    concerns: list[str] = []
    recos: list[dict] = []

    k = metrics.kpis_globales(datos.ads, datos.leads, datos.deals)
    cruce = metrics.cruce_inversion_leads(datos.ads, datos.leads, datos.deals)

    conv_google = int(datos.google["conversiones"].sum()) if not datos.google.empty else 0
    conv_meta = int(datos.meta["conversiones"].sum()) if not datos.meta.empty else 0

    # --- Rotura de atribución (concern + recos) ---------------------------- #
    if k["leads_total"] > 0 and (conv_google + conv_meta) <= 1:
        concerns.append(
            f"**Atribución rota**: HubSpot registra **{num(k['leads_total'])} leads** pero "
            f"las plataformas atribuyen {conv_google + conv_meta} conversiones. "
            "No se puede medir el CPL por campaña ni optimizar por resultados."
        )
        recos.append(dict(
            texto="Capturar `gclid`/`fbclid` + UTMs en campos ocultos del formulario de HubSpot",
            impacto="Alto", esfuerzo="Bajo"))
        recos.append(dict(
            texto="Activar la Conversions API (CAPI) de Meta enviando el evento Lead con `fbc`",
            impacto="Alto", esfuerzo="Medio"))
        recos.append(dict(
            texto="Configurar conversiones offline de Google Ads desde el lead de HubSpot",
            impacto="Alto", esfuerzo="Medio"))

    # --- CPL neto vs rango objetivo (replanificación jul-2026: 50-70 €) ---- #
    if k["cpl_neto"] > 0:
        est = config.estado_bench("cpl", k["cpl_neto"])
        rango = f"{num(config.CPL_OBJETIVO_MIN)}–{num(config.CPL_OBJETIVO_MAX)} €"
        if est == "ok":
            wins.append(f"**CPL neto {eur(k['cpl_neto'],2)}** dentro del rango objetivo ({rango}).")
        else:
            concerns.append(
                f"**CPL neto {eur(k['cpl_neto'],2)}** por encima del rango objetivo ({rango})."
            )

    # --- Captura de UTM (calidad de la atribución por campaña) ------------- #
    if not datos.leads.empty and "fuente" in datos.leads.columns:
        con_utm = int((datos.leads["fuente"] != "Sin UTM").sum())
        pct_utm = con_utm / len(datos.leads)
        if pct_utm < 0.8:
            concerns.append(
                f"Solo el **{pct(pct_utm)}** de los leads llega con UTM ({con_utm} de "
                f"{len(datos.leads)}): la atribución por campaña está incompleta."
            )
            recos.append(dict(
                texto="Asegurar que TODOS los leads pasan UTMs (`uvic_utm_*`) de la landing al CRM",
                impacto="Alto", esfuerzo="Medio"))

    # --- Mejor y peor programa por CPL ------------------------------------ #
    if not cruce.empty:
        con_leads = cruce[cruce["leads"] > 0]
        if not con_leads.empty:
            mejor = con_leads.sort_values("cpl").iloc[0]
            peor = con_leads.sort_values("cpl").iloc[-1]
            wins.append(
                f"**{mejor['programa']}** es el programa más eficiente: "
                f"CPL {eur(mejor['cpl'],2)} ({int(mejor['leads'])} leads, {eur(mejor['coste'])} inv.)."
            )
            recos.append(dict(
                texto=f"Escalar presupuesto en **{mejor['programa']}** (mejor CPL) manteniendo el CPC",
                impacto="Alto", esfuerzo="Bajo"))
            if len(con_leads) > 1 and peor["cpl"] > mejor["cpl"] * 1.5:
                concerns.append(
                    f"**{peor['programa']}** tiene el CPL más alto ({eur(peor['cpl'],2)}), "
                    f"{peor['cpl']/mejor['cpl']:.1f}× el mejor programa."
                )

        # CTR/CPC fuera de benchmark por programa (paid search)
        for _, r in cruce.iterrows():
            if r["ctr"] and config.estado_bench("ctr_search", r["ctr"]) == "off":
                concerns.append(
                    f"CTR bajo en **{r['programa']}** ({pct(r['ctr'],2)}): revisa anuncios y keywords."
                )
                recos.append(dict(
                    texto=f"Renovar creatividades/keywords de **{r['programa']}** (CTR {pct(r['ctr'],2)})",
                    impacto="Medio", esfuerzo="Medio"))
                break

    # --- Pace de inversión ------------------------------------------------- #
    pace = k["inversion"] / config.OBJETIVO_INVERSION_MENSUAL if config.OBJETIVO_INVERSION_MENSUAL else 0
    if pace < 0.4:
        concerns.append(
            f"Inversión al **{pct(pace)}** del objetivo mensual ({eur(k['inversion'])} de "
            f"{eur(config.OBJETIVO_INVERSION_MENSUAL)}): ritmo bajo para alcanzar {config.OBJETIVO_MATRICULAS} matrículas."
        )
        recos.append(dict(
            texto="Aumentar el ritmo de inversión en los programas con CPL bajo hacia el objetivo mensual",
            impacto="Alto", esfuerzo="Bajo"))

    # --- Embudo: mayor caída ---------------------------------------------- #
    te = metrics.tasas_embudo(datos.deals)
    if not te.empty and len(te) > 1:
        peor_paso = te.iloc[1:].sort_values("conv_paso").iloc[0]
        if peor_paso["conv_paso"] < 0.5:
            idx = te.index[te["etapa"] == peor_paso["etapa"]][0]
            etapa_prev = te.iloc[idx - 1]["etapa"]
            concerns.append(
                f"Mayor fuga del embudo: **{etapa_prev} → {peor_paso['etapa']}** "
                f"(solo pasa el {pct(peor_paso['conv_paso'])})."
            )

    # --- GA4: rebote alto por landing ------------------------------------- #
    if not datos.ga4.empty and "rebote" in datos.ga4:
        reb = datos.ga4.groupby("programa", as_index=False)["rebote"].mean()
        altos = reb[reb["rebote"] > config.BENCH["rebote"]["warn"]]
        if not altos.empty:
            peor_l = altos.sort_values("rebote", ascending=False).iloc[0]
            concerns.append(
                f"Rebote alto en la landing de **{peor_l['programa']}** ({pct(peor_l['rebote'])}): "
                "revisa mensaje, velocidad y coherencia anuncio→landing."
            )
            recos.append(dict(
                texto=f"Optimizar la landing de **{peor_l['programa']}** (rebote {pct(peor_l['rebote'])})",
                impacto="Medio", esfuerzo="Medio"))

    # --- % leads con programa --------------------------------------------- #
    if k["leads_total"] > 0 and k["pct_programa"] < 0.95:
        concerns.append(
            f"Solo el **{pct(k['pct_programa'])}** de los leads tiene programa asignado (`uvic_curso`)."
        )

    if not wins:
        wins.append("Datos conectados en vivo (Google Ads + HubSpot): base de medición operativa.")

    return dict(wins=wins, concerns=concerns, recos=recos)
