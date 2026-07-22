"""
Conector de Google Ads.

Estrategia de datos (en orden):
  1. API real (google-ads SDK) si hay credenciales en st.secrets["google_ads"].
  2. Caché local (data/cache/google_ads.parquet), que Claude puede rellenar vía MCP.
  3. Datos de ejemplo (sample_data) para que el dashboard sea navegable siempre.

Credenciales esperadas en .streamlit/secrets.toml:
    [google_ads]
    developer_token = "..."
    client_id = "..."
    client_secret = "..."
    refresh_token = "..."
    login_customer_id = "3963262878"
    customer_id = "2970533333"
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
    creds = _leer_secreto("google_ads")
    if creds:
        try:
            df = _consultar_api(creds, desde, hasta)
            if df is not None:
                if not df.empty:
                    guardar_cache(df, "google_ads")
                return ResultadoConector(df, "api", "Google Ads API")
        except Exception as e:  # noqa: BLE001
            # Caemos a caché/sample pero informamos del error.
            cache = leer_cache("google_ads")
            if cache is not None:
                return ResultadoConector(cache, "cache", f"API falló ({e}); uso caché")

    cache = leer_cache("google_ads")
    if cache is not None and not cache.empty:
        return ResultadoConector(cache, "cache", "Caché local")

    dias = (hasta - desde).days + 1
    return ResultadoConector(
        sample_data.google_ads_diario(dias), "sample", "Datos de ejemplo"
    )


def _consultar_api(creds: dict, desde, hasta) -> pd.DataFrame:
    """Consulta real vía google-ads SDK. Se importa dentro de la función para
    no exigir la dependencia si el usuario aún no usa la API."""
    from google.ads.googleads.client import GoogleAdsClient  # type: ignore

    client = GoogleAdsClient.load_from_dict({
        "developer_token": creds["developer_token"],
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "login_customer_id": creds.get("login_customer_id", config.GOOGLE_ADS_LOGIN_CUSTOMER_ID),
        "use_proto_plus": True,
    })
    customer_id = creds.get("customer_id", config.GOOGLE_ADS_CUSTOMER_ID)
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            segments.date,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions
        FROM campaign
        WHERE segments.date BETWEEN '{desde}' AND '{hasta}'
    """
    filas = []
    con_datos = set()
    for batch in ga_service.search_stream(customer_id=customer_id, query=query):
        for row in batch.results:
            nombre = row.campaign.name
            if not config.es_campana_werise(nombre):
                continue  # acotamos al scope WeRise (cualquier campaña 'WeRise…')
            con_datos.add(nombre)
            filas.append(dict(
                fecha=pd.to_datetime(row.segments.date).date(),
                plataforma="Google Ads",
                campana=nombre,
                impresiones=int(row.metrics.impressions),
                clics=int(row.metrics.clicks),
                coste=round(row.metrics.cost_micros / 1_000_000, 2),
                conversiones=int(row.metrics.conversions),
            ))

    # Incluir TODAS las campañas WeRise (aunque estén pausadas o sin gasto en el
    # periodo) con una fila a cero, para que siempre se muestren en el dashboard.
    try:
        q_lista = "SELECT campaign.name FROM campaign WHERE campaign.status != 'REMOVED'"
        for batch in ga_service.search_stream(customer_id=customer_id, query=q_lista):
            for row in batch.results:
                nombre = row.campaign.name
                if config.es_campana_werise(nombre) and nombre not in con_datos:
                    con_datos.add(nombre)
                    filas.append(dict(
                        fecha=pd.to_datetime(hasta).date(),
                        plataforma="Google Ads",
                        campana=nombre,
                        impresiones=0, clics=0, coste=0.0, conversiones=0,
                    ))
    except Exception:  # noqa: BLE001
        pass  # si la consulta de lista falla, mostramos solo las que tienen datos

    return pd.DataFrame(filas)
