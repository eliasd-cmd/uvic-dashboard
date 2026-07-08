"""
Conector de Google Analytics 4 (Data API v1).

Orden: API real -> caché -> datos de ejemplo.

Credenciales esperadas en .streamlit/secrets.toml:
    [ga4]
    property_id = "properties/123456789"
    # Autenticación por Service Account (JSON como tabla en secrets):
    [ga4.service_account]
    type = "service_account"
    project_id = "..."
    private_key = "..."
    client_email = "..."
    ...
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


def obtener(dias: int = 30) -> ResultadoConector:
    creds = _leer_secreto("ga4")
    # Vale con el JSON del service account inline (service_account) o con la
    # ruta a un archivo JSON (service_account_file).
    if creds and (creds.get("service_account") or creds.get("service_account_file")):
        try:
            df = _consultar_api(creds, dias)
            if df is not None and not df.empty:
                guardar_cache(df, "ga4")
                return ResultadoConector(df, "api", "GA4 Data API")
        except Exception as e:  # noqa: BLE001
            cache = leer_cache("ga4")
            if cache is not None:
                return ResultadoConector(cache, "cache", f"API falló ({e}); uso caché")

    cache = leer_cache("ga4")
    if cache is not None and not cache.empty:
        return ResultadoConector(cache, "cache", "Caché local")

    return ResultadoConector(sample_data.ga4_diario(dias), "sample", "Datos de ejemplo")


def _consultar_api(creds: dict, dias: int) -> pd.DataFrame:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient  # type: ignore
    from google.analytics.data_v1beta.types import (  # type: ignore
        DateRange,
        Dimension,
        Metric,
        RunReportRequest,
    )
    from google.oauth2 import service_account  # type: ignore

    if creds.get("service_account_file"):
        credentials = service_account.Credentials.from_service_account_file(
            creds["service_account_file"]
        )
    else:
        credentials = service_account.Credentials.from_service_account_info(
            dict(creds["service_account"])
        )
    client = BetaAnalyticsDataClient(credentials=credentials)

    property_id = creds.get("property_id", config.GA4_PROPERTY_ID)
    request = RunReportRequest(
        property=property_id,
        dimensions=[Dimension(name="date"), Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="totalUsers"),
            Metric(name="conversions"),
            Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"),
        ],
        date_ranges=[DateRange(start_date=f"{dias}daysAgo", end_date="today")],
    )
    resp = client.run_report(request)
    filas = []
    for row in resp.rows:
        d = row.dimension_values
        m = row.metric_values
        filas.append(dict(
            fecha=pd.to_datetime(d[0].value).date(),
            canal=d[1].value,
            sesiones=int(m[0].value or 0),
            usuarios=int(m[1].value or 0),
            conversiones=int(float(m[2].value or 0)),
            rebote=round(float(m[3].value or 0), 3),
            duracion_media=round(float(m[4].value or 0), 0),
        ))
    return pd.DataFrame(filas)
