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


def _cliente(creds: dict):
    """Devuelve (client, property_id, filtro) reutilizable. El filtro limita a
    las 5 landings y EXCLUYE las fuentes de test (pixel-doctor, metaCLAUDETEST)."""
    from google.analytics.data_v1beta import BetaAnalyticsDataClient  # type: ignore
    from google.analytics.data_v1beta.types import (  # type: ignore
        Filter, FilterExpression, FilterExpressionList,
    )
    from google.oauth2 import service_account  # type: ignore

    if creds.get("service_account_file"):
        credentials = service_account.Credentials.from_service_account_file(
            creds["service_account_file"])
    else:
        credentials = service_account.Credentials.from_service_account_info(
            dict(creds["service_account"]))
    client = BetaAnalyticsDataClient(credentials=credentials)
    property_id = creds.get("property_id", config.GA4_PROPERTY_ID)

    solo_landings = FilterExpression(filter=Filter(
        field_name="landingPage",
        in_list_filter=Filter.InListFilter(values=config.LANDINGS)))
    excluir_tests = FilterExpression(not_expression=FilterExpression(filter=Filter(
        field_name="sessionSource",
        in_list_filter=Filter.InListFilter(values=config.GA4_FUENTES_EXCLUIR))))
    filtro = FilterExpression(and_group=FilterExpressionList(
        expressions=[solo_landings, excluir_tests]))
    return client, property_id, filtro


def _consultar_api(creds: dict, dias: int) -> pd.DataFrame:
    from google.analytics.data_v1beta.types import (  # type: ignore
        DateRange, Dimension, Metric, RunReportRequest,
    )
    client, property_id, filtro = _cliente(creds)
    request = RunReportRequest(
        property=property_id,
        dimensions=[Dimension(name="date"), Dimension(name="landingPage")],
        metrics=[Metric(name=m) for m in
                 ("sessions", "totalUsers", "screenPageViews", "bounceRate",
                  "averageSessionDuration")],
        date_ranges=[DateRange(start_date=f"{dias}daysAgo", end_date="today")],
        dimension_filter=filtro,
    )
    resp = client.run_report(request)
    filas = []
    for row in resp.rows:
        d = row.dimension_values
        m = row.metric_values
        landing = d[1].value
        filas.append(dict(
            fecha=pd.to_datetime(d[0].value).date(),
            landing=landing,
            programa=config.programa_por_landing(landing),
            sesiones=int(m[0].value or 0),
            usuarios=int(m[1].value or 0),
            vistas=int(float(m[2].value or 0)),
            rebote=round(float(m[3].value or 0), 3),
            duracion_media=round(float(m[4].value or 0), 0),
        ))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Agrupaciones extra de las 5 landings: por fuente/medio y por campaña.
# Incluyen eventos (eventCount) y eventos clave (keyEvents).
# --------------------------------------------------------------------------- #
_MET_EXTRA = ["sessions", "totalUsers", "eventCount", "keyEvents"]


def _report_agrupado(creds: dict, dias: int, dims: list[tuple[str, str]]) -> pd.DataFrame:
    """Ejecuta un informe agrupado por `dims` [(ga4_name, col_salida), ...],
    filtrado a las 5 landings, con sesiones/usuarios/eventos/eventos_clave."""
    from google.analytics.data_v1beta.types import (  # type: ignore
        DateRange, Dimension, Metric, RunReportRequest,
    )
    client, property_id, filtro = _cliente(creds)
    request = RunReportRequest(
        property=property_id,
        dimensions=[Dimension(name=g) for g, _ in dims],
        metrics=[Metric(name=m) for m in _MET_EXTRA],
        date_ranges=[DateRange(start_date=f"{dias}daysAgo", end_date="today")],
        dimension_filter=filtro,
    )
    resp = client.run_report(request)
    filas = []
    for row in resp.rows:
        fila = {col: row.dimension_values[i].value for i, (_, col) in enumerate(dims)}
        m = row.metric_values
        fila.update(
            sesiones=int(m[0].value or 0),
            usuarios=int(m[1].value or 0),
            eventos=int(float(m[2].value or 0)),
            eventos_clave=int(float(m[3].value or 0)),
        )
        filas.append(fila)
    df = pd.DataFrame(filas)
    if not df.empty:
        df = df.sort_values("sesiones", ascending=False)
    return df


def _obtener_agrupado(dias, dims, nombre_cache, fn_sample):
    creds = _leer_secreto("ga4")
    if creds and (creds.get("service_account") or creds.get("service_account_file")):
        try:
            df = _report_agrupado(creds, dias, dims)
            if df is not None and not df.empty:
                guardar_cache(df, nombre_cache)
                return ResultadoConector(df, "api", "GA4 Data API")
        except Exception as e:  # noqa: BLE001
            cache = leer_cache(nombre_cache)
            if cache is not None:
                return ResultadoConector(cache, "cache", f"API falló ({e}); caché")
    cache = leer_cache(nombre_cache)
    if cache is not None and not cache.empty:
        return ResultadoConector(cache, "cache", "Caché local")
    return ResultadoConector(fn_sample(dias), "sample", "Datos de ejemplo")


def obtener_fuente(dias: int = 30) -> ResultadoConector:
    return _obtener_agrupado(
        dias, [("sessionSource", "fuente"), ("sessionMedium", "medio")],
        "ga4_fuente", sample_data.ga4_por_fuente)


def obtener_campana(dias: int = 30) -> ResultadoConector:
    return _obtener_agrupado(
        dias, [("sessionSource", "fuente"), ("sessionCampaignName", "campana")],
        "ga4_campana", sample_data.ga4_por_campana)
