"""
Conector de HubSpot (CRM API v3/v4) — portal Rise Education (144637943).

Modelo UVic (verificado):
- **Leads UVic** = contactos con la propiedad `uvic_curso` (que mapea a programa).
  La atribución de campaña llega como OFFLINE/INTEGRATION (se pierde el gclid/fbclid),
  así que la asociación lead↔campaña se hace POR PROGRAMA, no por nombre de campaña.
- **Matrícula** = Deal en etapa "Cierre ganado" del Pipeline UVIC (3920516288).

Expone:
- obtener(dias)        -> ResultadoConector con el DataFrame de leads (contactos).
- obtener_deals(dias)  -> ResultadoConector con el DataFrame de deals (Pipeline UVIC).

Orden de resolución en ambos: API real -> caché -> datos de ejemplo.

Credenciales en .streamlit/secrets.toml:
    [hubspot]
    access_token = "pat-eu1-..."
    portal_id = "144637943"
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

import pandas as pd

from src import config
from src.connectors.base import (
    ResultadoConector,
    _leer_secreto,
    guardar_cache,
    leer_cache,
)
from src.data import sample_data

API = "https://api.hubapi.com"

# Mapeo de lifecyclestage de contacto -> etiqueta de estado del lead.
MAPA_LIFECYCLE = {
    "subscriber": "Suscriptor", "lead": "Lead", "marketingqualifiedlead": "MQL",
    "salesqualifiedlead": "SQL", "opportunity": "Oportunidad",
    "customer": "Matriculado", "evangelist": "Prescriptor", "other": "Otro",
}


# --------------------------------------------------------------------------- #
# Leads (contactos con uvic_curso)
# --------------------------------------------------------------------------- #
def obtener(dias: int = 30) -> ResultadoConector:
    creds = _leer_secreto("hubspot")
    if creds and creds.get("access_token"):
        try:
            df = _fetch_leads(creds, dias)
            if df is not None:
                guardar_cache(df, "hubspot_leads")
                return ResultadoConector(df, "api", "HubSpot (uvic_curso)")
        except Exception as e:  # noqa: BLE001
            cache = leer_cache("hubspot_leads")
            if cache is not None:
                return ResultadoConector(cache, "cache", f"API falló ({e}); caché")

    cache = leer_cache("hubspot_leads")
    if cache is not None and not cache.empty:
        return ResultadoConector(cache, "cache", "Caché local")
    return ResultadoConector(sample_data.hubspot_leads(dias), "sample", "Datos de ejemplo")


def obtener_deals(dias: int = 30) -> ResultadoConector:
    creds = _leer_secreto("hubspot")
    if creds and creds.get("access_token"):
        try:
            df = _fetch_deals(creds, dias)
            if df is not None:
                guardar_cache(df, "hubspot_deals")
                return ResultadoConector(df, "api", "HubSpot Pipeline UVIC")
        except Exception as e:  # noqa: BLE001
            cache = leer_cache("hubspot_deals")
            if cache is not None:
                return ResultadoConector(cache, "cache", f"API falló ({e}); caché")

    cache = leer_cache("hubspot_deals")
    if cache is not None and not cache.empty:
        return ResultadoConector(cache, "cache", "Caché local")
    return ResultadoConector(sample_data.hubspot_deals(dias), "sample", "Datos de ejemplo")


# --------------------------------------------------------------------------- #
# Llamadas a la API
# --------------------------------------------------------------------------- #
def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _desde_ms(dias: int) -> int:
    return int((time.time() - dias * 86400) * 1000)


def _a_fecha(iso: str):
    if not iso:
        return None
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc).date()


def _fetch_leads(creds: dict, dias: int) -> pd.DataFrame:
    import requests

    token = creds["access_token"]
    payload = {
        "filterGroups": [{
            "filters": [
                {"propertyName": "uvic_curso", "operator": "HAS_PROPERTY"},
                {"propertyName": "createdate", "operator": "GTE", "value": str(_desde_ms(dias))},
            ]
        }],
        "properties": ["uvic_curso", "uvic_nivel_estudios", "createdate",
                       "lifecyclestage", "hs_lead_status", "hs_analytics_source"],
        "limit": 100,
    }
    filas, after = [], None
    while True:
        if after:
            payload["after"] = after
        r = requests.post(f"{API}/crm/v3/objects/contacts/search",
                          headers=_headers(token), json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        for c in data.get("results", []):
            p = c.get("properties", {})
            curso = p.get("uvic_curso") or ""
            estado = MAPA_LIFECYCLE.get((p.get("lifecyclestage") or "").lower(), "Lead")
            filas.append(dict(
                lead_id=c.get("id"),
                fecha_creacion=_a_fecha(p.get("createdate")),
                fuente=p.get("hs_analytics_source") or "Sin atribuir",
                campana="",  # atribución de campaña perdida (OFFLINE/INTEGRATION)
                programa=config.programa_por_curso(curso),
                nivel=p.get("uvic_nivel_estudios") or "",
                estado=estado,
                es_matricula=(estado == "Matriculado"),
            ))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break
    return pd.DataFrame(filas)


def _fetch_deals(creds: dict, dias: int) -> pd.DataFrame:
    """Deals del Pipeline UVIC + programa (vía contacto asociado y su uvic_curso)."""
    import requests

    token = creds["access_token"]
    payload = {
        "filterGroups": [{
            "filters": [{"propertyName": "pipeline", "operator": "EQ",
                         "value": config.HUBSPOT_PIPELINE_UVIC}]
        }],
        "properties": ["dealstage", "amount", "createdate", "dealname"],
        "limit": 100,
    }
    deals, after = [], None
    while True:
        if after:
            payload["after"] = after
        r = requests.post(f"{API}/crm/v3/objects/deals/search",
                          headers=_headers(token), json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        deals.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

    # Mapa deal -> programa vía contacto asociado (best-effort).
    deal_ids = [d["id"] for d in deals]
    prog_por_deal = _programa_por_deal(token, deal_ids) if deal_ids else {}

    filas = []
    for d in deals:
        p = d.get("properties", {})
        etapa_id = p.get("dealstage") or ""
        filas.append(dict(
            deal_id=d.get("id"),
            fecha_creacion=_a_fecha(p.get("createdate")),
            etapa_id=etapa_id,
            etapa=config.HUBSPOT_ETAPAS_MAP.get(etapa_id, etapa_id),
            programa=prog_por_deal.get(d.get("id"), "Sin asignar"),
            amount=float(p.get("amount") or 0),
            es_ganado=(etapa_id == config.HUBSPOT_STAGE_MATRICULA),
        ))
    return pd.DataFrame(filas)


def _programa_por_deal(token: str, deal_ids: list[str]) -> dict:
    """Asocia cada deal a un programa leyendo el uvic_curso del contacto asociado."""
    import requests

    # 1) deal -> contacto (associations v4 batch)
    try:
        r = requests.post(
            f"{API}/crm/v4/associations/deal/contact/batch/read",
            headers=_headers(token),
            json={"inputs": [{"id": i} for i in deal_ids]}, timeout=60)
        r.raise_for_status()
        res = r.json().get("results", [])
    except Exception:  # noqa: BLE001
        return {}

    deal_to_contact, contact_ids = {}, set()
    for item in res:
        frm = str(item.get("from", {}).get("id"))
        tos = item.get("to", [])
        if tos:
            cid = str(tos[0].get("toObjectId"))
            deal_to_contact[frm] = cid
            contact_ids.add(cid)
    if not contact_ids:
        return {}

    # 2) contacto -> uvic_curso (batch read)
    try:
        r = requests.post(
            f"{API}/crm/v3/objects/contacts/batch/read",
            headers=_headers(token),
            json={"properties": ["uvic_curso"],
                  "inputs": [{"id": c} for c in contact_ids]}, timeout=60)
        r.raise_for_status()
        curso_por_contacto = {
            str(c["id"]): (c.get("properties", {}).get("uvic_curso") or "")
            for c in r.json().get("results", [])
        }
    except Exception:  # noqa: BLE001
        return {}

    return {
        did: config.programa_por_curso(curso_por_contacto.get(cid, ""))
        for did, cid in deal_to_contact.items()
    }
