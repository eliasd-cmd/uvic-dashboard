"""
Vuelca datos REALES (últimos 30 días) de Google Ads y Meta a la caché del
dashboard, para las 5 campañas WeRise. Los totales por campaña son reales
(vía MCP); se reparten de forma uniforme en 30 días para poder dibujar series
diarias (los agregados suman exactamente los totales reales).

Uso:  python scripts/seed_cache_real.py <ruta_json_google_ads>
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

CACHE = Path(__file__).resolve().parents[1] / "data" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)

FIN = date(2026, 7, 7)
DIAS = 30
FECHAS = [FIN - timedelta(days=i) for i in range(DIAS - 1, -1, -1)]

WERISE_GOOGLE = {
    "WeRise_Search_NAC_MBA_Executive",
    "WeRise_Search_NAC_Master_Marqueting_Esportiu",
    "WeRise_Search_NAC_Postgrau_Documental_Social",
    "WeRise_Search_NAC_Postgrau_Comunicacio_Cientifica",
    "WeRise_Search_NAC_Postgrau_Lideratge_IA",
}

# Meta WeRise: totales reales 30d (vía ads_get_ad_entities, cuenta 33542477).
META_WERISE = [
    # (campaña, spend, impresiones, clics, conversiones)
    ("WeRise_EP_Lidera en entorns d'Intel·ligència Artificial", 167.71, 28211, 288, 0),
    ("WeRise_Postgrau_Documental Social", 163.72, 44735, 360, 0),
    ("WeRise_Màster_Gestió i Màrqueting Esportiu", 161.49, 53168, 326, 0),
    ("WeRise_Executive MBA", 154.77, 39773, 197, 0),
    ("WeRise_Postgrau_Comunicació Científica", 154.66, 37815, 248, 0),
]


def expandir(plataforma: str, filas_tot: list[dict]) -> pd.DataFrame:
    """Reparte cada total de campaña en 30 filas diarias (suma exacta)."""
    out = []
    for c in filas_tot:
        # reparto entero con resto al último día; coste como float uniforme
        imp = _split_int(c["impresiones"])
        clk = _split_int(c["clics"])
        conv = _split_int(c["conversiones"])
        coste_dia = round(c["coste"] / DIAS, 4)
        for i, f in enumerate(FECHAS):
            out.append(dict(
                fecha=f, plataforma=plataforma, campana=c["campana"],
                impresiones=imp[i], clics=clk[i], coste=coste_dia, conversiones=conv[i],
            ))
    return pd.DataFrame(out)


def _split_int(total: int) -> list[int]:
    base = total // DIAS
    resto = total - base * DIAS
    arr = [base] * DIAS
    for i in range(resto):  # reparte el resto en los últimos días
        arr[DIAS - 1 - i] += 1
    return arr


def google_reales(path_json: str) -> list[dict]:
    data = json.load(open(path_json))
    filas = []
    for c in data:
        n = c.get("campaña", "")
        if n in WERISE_GOOGLE:
            filas.append(dict(
                campana=n,
                impresiones=int(c["impresiones"]),
                clics=int(c["clics"]),
                coste=float(c["costo_eur"]),
                conversiones=int(round(c["conversiones"])),
            ))
    return filas


def main():
    gjson = sys.argv[1]
    g_tot = google_reales(gjson)
    m_tot = [dict(campana=n, coste=s, impresiones=i, clics=k, conversiones=cv)
             for (n, s, i, k, cv) in META_WERISE]

    g = expandir("Google Ads", g_tot)
    m = expandir("Meta Ads", m_tot)

    g.to_parquet(CACHE / "google_ads.parquet", index=False)
    m.to_parquet(CACHE / "meta_ads.parquet", index=False)

    print(f"Google: {len(g_tot)} campañas WeRise, {g['coste'].sum():.2f}€, {len(g)} filas")
    print(f"Meta:   {len(m_tot)} campañas WeRise, {m['coste'].sum():.2f}€, {len(m)} filas")
    print("Cache guardada en", CACHE)


if __name__ == "__main__":
    main()
