"""
Conector de Meta Ads (Marketing API).

Orden: API real -> caché -> datos de ejemplo.

Credenciales esperadas en .streamlit/secrets.toml:
    [meta_ads]
    access_token = "..."
    ad_account_id = "act_33542477"
    api_version = "v21.0"
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.connectors.base import (
    ResultadoConector,
    _leer_secreto,
    guardar_cache,
    leer_cache,
)
from src.data import sample_data


def obtener(desde, hasta) -> ResultadoConector:
    creds = _leer_secreto("meta_ads")
    if creds:
        try:
            df = _consultar_api(creds, desde, hasta)
            if df is not None:
                if not df.empty:
                    guardar_cache(df, "meta_ads")
                return ResultadoConector(df, "api", "Meta Marketing API")
        except Exception as e:  # noqa: BLE001
            cache = leer_cache("meta_ads")
            if cache is not None:
                return ResultadoConector(cache, "cache", f"API falló ({e}); uso caché")

    cache = leer_cache("meta_ads")
    if cache is not None and not cache.empty:
        return ResultadoConector(cache, "cache", "Caché local")

    dias = (hasta - desde).days + 1
    return ResultadoConector(
        sample_data.meta_ads_diario(dias), "sample", "Datos de ejemplo"
    )


def _consultar_api(creds: dict, desde, hasta) -> pd.DataFrame:
    """Insights diarios por campaña vía Graph API (con requests, sin SDK)."""
    import json

    import requests

    version = creds.get("api_version", "v21.0")
    account = creds.get("ad_account_id", config.META_AD_ACCOUNT_ID)
    token = creds["access_token"]

    # Estado (effective_status) de todas las campañas → mapa nombre→estado legible.
    estados = {}
    try:
        rc = requests.get(
            f"https://graph.facebook.com/{version}/{account}/campaigns",
            params={"fields": "name,effective_status", "limit": 500, "access_token": token},
            timeout=60)
        for cp in rc.json().get("data", []):
            estados[cp.get("name", "")] = config.estado_legible(cp.get("effective_status"))
    except Exception:  # noqa: BLE001
        pass

    url = f"https://graph.facebook.com/{version}/{account}/insights"
    params = {
        "level": "campaign",
        "fields": "campaign_name,impressions,clicks,spend,actions",
        "time_increment": 1,
        "time_range": json.dumps({"since": str(desde), "until": str(hasta)}),
        "access_token": token,
        "limit": 500,
    }
    filas = []
    con_datos = set()
    while url:
        resp = requests.get(url, params=params, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        for row in data.get("data", []):
            nombre = row.get("campaign_name", "")
            if not config.es_campana_werise(nombre):
                continue  # acotamos al scope WeRise (cualquier campaña 'WeRise…')
            con_datos.add(nombre)
            # OJO: Meta reporta el MISMO lead bajo dos action_type ("lead" y
            # "offsite_conversion.fb_pixel_lead"). Sumarlos duplica → tomamos el máximo.
            vals = [
                int(float(a.get("value", 0)))
                for a in row.get("actions", [])
                if a.get("action_type") in ("lead", "offsite_conversion.fb_pixel_lead")
            ]
            leads = max(vals) if vals else 0
            filas.append(dict(
                fecha=pd.to_datetime(row["date_start"]).date(),
                plataforma="Meta Ads",
                campana=nombre,
                estado=estados.get(nombre, "Otra"),
                impresiones=int(row.get("impressions", 0)),
                clics=int(row.get("clicks", 0)),
                coste=round(float(row.get("spend", 0)), 2),
                conversiones=leads,
            ))
        url = data.get("paging", {}).get("next")
        params = None  # la URL 'next' ya trae los parámetros

    # Incluir TODAS las campañas WeRise (aunque estén pausadas o sin gasto en el
    # periodo) con una fila a cero, para que siempre se muestren en el dashboard.
    for nombre, est in estados.items():
        if config.es_campana_werise(nombre) and nombre not in con_datos:
            con_datos.add(nombre)
            filas.append(dict(
                fecha=pd.to_datetime(hasta).date(),
                plataforma="Meta Ads",
                campana=nombre,
                estado=est,
                impresiones=0, clics=0, coste=0.0, conversiones=0,
            ))

    return pd.DataFrame(filas)


