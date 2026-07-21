"""
Conector de la PLANIFICACIÓN (Google Sheet en vivo).

La planificación trimestral (Jul–Ago–Sep) se mantiene en una Google Sheet con
tres pestañas — TOTAL, Por Programa, Por Plataforma — replicando el Excel de
marketing. El dashboard la lee en vivo (reutiliza el service account de GA4).

Orden de resolución: Google Sheet -> Excel local del repo -> vacío.

Config en .streamlit/secrets.toml:
    [plan]
    sheet_id = "<ID de la Google Sheet>"       # o sheet_url = "https://..."
    # credenciales: reutiliza [ga4].service_account_file (o .service_account)

Cada pestaña es una rejilla de "bloques". Un bloque =
    fila título (nombre del programa/plataforma, año en col.1)
    fila "Escenario | julio | agosto | septiembre | Total"   (cabecera de meses)
    filas de métrica: Leads, MKT Presu., CPL, Ventas Netas totales,
                      Tasa de Conversión, Facturación Neta, GP, Leads diarios
"""
from __future__ import annotations

from src import config
from src.connectors.base import _leer_secreto

# Pestañas esperadas (en orden de aparición en el dashboard).
PESTANAS = ["TOTAL", "Por Programa", "Por Plataforma"]

# Ruta del Excel local (fallback si la Sheet aún no está conectada).
_EXCEL_LOCAL = "data/plan/UVic_Planificacion.xlsx"


# --------------------------------------------------------------------------- #
# Parseo de bloques
# --------------------------------------------------------------------------- #
def _txt(v) -> str:
    return "" if v is None else str(v).strip()


def parsear_bloques(valores: list[list]) -> list[dict]:
    """Convierte una matriz (lista de filas) en una lista de bloques
    {nombre, meses, metricas:{label:[valores...]}}.

    Un bloque empieza en la fila con 'Escenario' en la col.0; su título es la
    fila de texto inmediatamente anterior; sus métricas van hasta el título del
    siguiente bloque (o el fin de la hoja)."""
    # Índices de las filas-cabecera ("Escenario ...").
    cabeceras = [i for i, f in enumerate(valores) if _txt(f[0] if f else "").lower() == "escenario"]
    bloques = []
    for pos, i in enumerate(cabeceras):
        fila = valores[i]
        meses = [_txt(x) for x in fila[1:] if _txt(x) and _txt(x).lower() != "nan"]
        # Título: primera fila con texto hacia arriba.
        nombre = ""
        for j in range(i - 1, -1, -1):
            t = _txt(valores[j][0])
            if t and t.lower() != "nan":
                nombre = t
                break
        # Límite inferior: título del siguiente bloque (cabecera_sig - 1) o fin.
        fin = (cabeceras[pos + 1] - 1) if pos + 1 < len(cabeceras) else len(valores)
        metricas = {}
        for k in range(i + 1, fin):
            lbl = _txt(valores[k][0])
            if not lbl or lbl.lower() == "nan":
                continue
            metricas[lbl] = list(valores[k][1:1 + len(meses)])
        bloques.append(dict(nombre=nombre, meses=meses, metricas=metricas))
    return bloques


# --------------------------------------------------------------------------- #
# Lectura de las fuentes
# --------------------------------------------------------------------------- #
def _desde_google_sheet(creds_plan: dict) -> dict:
    """Lee las 3 pestañas de la Google Sheet. Devuelve {pestaña: [bloques]}."""
    import gspread
    from google.oauth2.service_account import Credentials

    ga4 = _leer_secreto("ga4") or {}
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    if ga4.get("service_account_file"):
        cred = Credentials.from_service_account_file(ga4["service_account_file"], scopes=scopes)
    elif ga4.get("service_account"):
        cred = Credentials.from_service_account_info(dict(ga4["service_account"]), scopes=scopes)
    else:
        raise RuntimeError("No hay credenciales de service account (bloque [ga4]).")

    gc = gspread.authorize(cred)
    sheet_id = creds_plan.get("sheet_id")
    if not sheet_id and creds_plan.get("sheet_url"):
        sh = gc.open_by_url(creds_plan["sheet_url"])
    else:
        sh = gc.open_by_key(sheet_id)

    out = {}
    titulos = {ws.title.strip().lower(): ws for ws in sh.worksheets()}
    for pest in PESTANAS:
        ws = titulos.get(pest.lower())
        if ws is None:
            continue
        # UNFORMATTED_VALUE devuelve números como int/float (sin locale), no texto.
        vals = ws.get_values(value_render_option="UNFORMATTED_VALUE")
        out[pest] = parsear_bloques(vals)
    return out


def _desde_excel_local() -> dict:
    """Fallback: lee el Excel commiteado en el repo."""
    import os

    import pandas as pd

    if not os.path.exists(_EXCEL_LOCAL):
        return {}
    out = {}
    xl = pd.ExcelFile(_EXCEL_LOCAL)
    for pest in PESTANAS:
        if pest not in xl.sheet_names:
            continue
        df = pd.read_excel(_EXCEL_LOCAL, sheet_name=pest, header=None)
        vals = df.where(pd.notnull(df), None).values.tolist()
        out[pest] = parsear_bloques(vals)
    return out


def _a_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def valores_mes(bloque: dict, mes: str) -> dict:
    """Devuelve {metrica_en_minúsculas: valor_float} de un bloque para un mes
    concreto (p.ej. 'julio'). Ignora valores no numéricos."""
    if not bloque or mes not in bloque.get("meses", []):
        return {}
    idx = bloque["meses"].index(mes)
    out = {}
    for label, valores in bloque["metricas"].items():
        if idx < len(valores):
            v = _a_float(valores[idx])
            if v is not None:
                out[label.strip().lower()] = v
    return out


def plan_total_mes(data: dict, mes: str) -> dict:
    """Atajo: valores del bloque TOTAL para el mes dado. Devuelve dict con las
    claves esperadas normalizadas: inversion, leads, cpl, matriculas."""
    bloques = (data or {}).get("TOTAL", [])
    if not bloques:
        return {}
    m = valores_mes(bloques[0], mes)
    return dict(
        inversion=m.get("mkt presu."),
        leads=m.get("leads"),
        cpl=m.get("cpl"),
        matriculas=m.get("ventas netas totales"),
        facturacion=m.get("facturación neta"),
        tasa=m.get("tasa de conversión"),
    )


def obtener_plan():
    """Devuelve (estructura, origen, detalle).

    estructura = {"TOTAL": [bloques], "Por Programa": [...], "Por Plataforma": [...]}
    origen ∈ {"api", "excel", "sample"}."""
    creds_plan = _leer_secreto("plan")
    if creds_plan and (creds_plan.get("sheet_id") or creds_plan.get("sheet_url")):
        try:
            data = _desde_google_sheet(creds_plan)
            if data:
                return data, "api", "Google Sheet en vivo"
        except Exception as e:  # noqa: BLE001
            local = _desde_excel_local()
            if local:
                return local, "excel", f"Sheet falló ({e}); Excel local"
            return {}, "sample", f"Sheet falló ({e})"

    local = _desde_excel_local()
    if local:
        return local, "excel", "Excel local del repo"
    return {}, "sample", "Sin planificación configurada"
