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
                # Excluir leads antiguos importados (no son de las campañas actuales).
                {"propertyName": "hs_object_source", "operator": "NEQ", "value": "IMPORT"},
            ]
        }],
        "properties": ["uvic_curso", "uvic_nivel_estudios", "createdate",
                       "lifecyclestage", "hs_lead_status", "hs_analytics_source",
                       "hs_object_source", "hs_analytics_source_data_1",
                       "uvic_utm_source", "uvic_utm_medium", "uvic_utm_campaign"],
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
            # Segundo filtro (por si el server-side no lo cazó): descartar importados.
            if p.get("hs_object_source") == "IMPORT" or p.get("hs_analytics_source_data_1") == "IMPORT":
                continue
            # Descartar leads de webinar (uvic_utm_campaign ~ 'webinar'): no son de
            # la captación WeRise; se gestionan en la hoja de Leads Importados.
            if config.es_webinar(p.get("uvic_utm_campaign")):
                continue
            curso = p.get("uvic_curso") or ""
            estado = MAPA_LIFECYCLE.get((p.get("lifecyclestage") or "").lower(), "Lead")
            utm_source = p.get("uvic_utm_source") or ""
            utm_medium = p.get("uvic_utm_medium") or ""
            filas.append(dict(
                lead_id=c.get("id"),
                fecha_creacion=_a_fecha(p.get("createdate")),
                # Fuente derivada de las UTM propias (uvic_utm_*): Meta/Google/Sin UTM.
                fuente=config.plataforma_por_utm(utm_source, utm_medium),
                utm_source=utm_source,
                utm_medium=utm_medium,
                campana=p.get("uvic_utm_campaign") or "",
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
    info_por_deal = _programa_por_deal(token, deal_ids) if deal_ids else {}
    prog_por_deal = {k: v["programa"] for k, v in info_por_deal.items()}

    filas = []
    for d in deals:
        # Excluir deals de leads de webinar (van a la hoja de Leads Importados).
        if info_por_deal.get(d.get("id"), {}).get("webinar"):
            continue
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
    """Asocia cada deal a su contacto y devuelve {deal_id: {programa, webinar}}
    leyendo uvic_curso y uvic_utm_campaign del contacto asociado."""
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

    # 2) contacto -> uvic_curso + uvic_utm_campaign (batch read)
    try:
        r = requests.post(
            f"{API}/crm/v3/objects/contacts/batch/read",
            headers=_headers(token),
            json={"properties": ["uvic_curso", "uvic_utm_campaign"],
                  "inputs": [{"id": c} for c in contact_ids]}, timeout=60)
        r.raise_for_status()
        props_por_contacto = {
            str(c["id"]): c.get("properties", {})
            for c in r.json().get("results", [])
        }
    except Exception:  # noqa: BLE001
        return {}

    out = {}
    for did, cid in deal_to_contact.items():
        p = props_por_contacto.get(cid, {})
        out[did] = dict(
            programa=config.programa_por_curso(p.get("uvic_curso") or ""),
            webinar=config.es_webinar(p.get("uvic_utm_campaign")),
        )
    return out


# --------------------------------------------------------------------------- #
# Leads IMPORTADOS / WEBINAR (control aparte) — contactos uvic_curso con
# fuente = IMPORT o con uvic_utm_campaign de webinar. Sin filtro de fecha:
# se listan TODOS, y los nuevos que cumplan cualquiera de los dos criterios
# caen aquí solos (y quedan fuera del resto del dashboard).
# --------------------------------------------------------------------------- #
def importados():
    """Devuelve (leads_import_df, negocios_import_df, origen)."""
    creds = _leer_secreto("hubspot")
    if creds and creds.get("access_token"):
        try:
            leads, negocios = _fetch_importados(creds)
            guardar_cache(leads, "hubspot_import_leads")
            guardar_cache(negocios, "hubspot_import_negocios")
            return leads, negocios, "api"
        except Exception:  # noqa: BLE001
            lc = leer_cache("hubspot_import_leads")
            if lc is not None:
                dc = leer_cache("hubspot_import_negocios")
                return lc, (dc if dc is not None else pd.DataFrame()), "cache"

    lc = leer_cache("hubspot_import_leads")
    if lc is not None and not lc.empty:
        dc = leer_cache("hubspot_import_negocios")
        return lc, (dc if dc is not None else pd.DataFrame()), "cache"
    return sample_data.import_leads(), sample_data.import_negocios(), "sample"


def _mapa_etapas_deals(token: str) -> dict:
    """Mapa {stage_id: etiqueta} y {pipeline_id: etiqueta} de todos los pipelines."""
    import requests
    stages, pipelines = {}, {}
    try:
        r = requests.get(f"{API}/crm/v3/pipelines/deals", headers=_headers(token), timeout=60)
        r.raise_for_status()
        for p in r.json().get("results", []):
            pipelines[p["id"]] = p.get("label", p["id"])
            for s in p.get("stages", []):
                stages[s["id"]] = s.get("label", s["id"])
    except Exception:  # noqa: BLE001
        pass
    return {"stages": stages, "pipelines": pipelines}


def _fetch_importados(creds: dict):
    import requests
    token = creds["access_token"]
    mapa = _mapa_etapas_deals(token)

    payload = {
        # Dos grupos = OR: importados clásicos O leads de webinar (por UTM campaign).
        "filterGroups": [
            {"filters": [
                {"propertyName": "uvic_curso", "operator": "HAS_PROPERTY"},
                {"propertyName": "hs_object_source", "operator": "EQ", "value": "IMPORT"},
            ]},
            {"filters": [
                {"propertyName": "uvic_curso", "operator": "HAS_PROPERTY"},
                {"propertyName": "uvic_utm_campaign", "operator": "CONTAINS_TOKEN", "value": "webinar"},
            ]},
        ],
        "properties": ["uvic_curso", "uvic_nivel_estudios", "createdate", "lifecyclestage",
                       "hs_lead_status", "firstname", "lastname", "email", "num_associated_deals",
                       "uvic_utm_campaign", "hs_object_source"],
        "limit": 100,
    }
    contactos, after = [], None
    while True:
        if after:
            payload["after"] = after
        r = requests.post(f"{API}/crm/v3/objects/contacts/search",
                          headers=_headers(token), json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        contactos.extend(data.get("results", []))
        after = data.get("paging", {}).get("next", {}).get("after")
        if not after:
            break

    filas = []
    for c in contactos:
        p = c.get("properties", {})
        nombre = f"{p.get('firstname','') or ''} {p.get('lastname','') or ''}".strip()
        filas.append(dict(
            lead_id=c.get("id"),
            nombre=nombre or (p.get("email") or "—"),
            email=p.get("email") or "",
            fecha_creacion=_a_fecha(p.get("createdate")),
            programa=config.programa_por_curso(p.get("uvic_curso") or ""),
            nivel=p.get("uvic_nivel_estudios") or "",
            estado=MAPA_LIFECYCLE.get((p.get("lifecyclestage") or "").lower(), "Lead"),
            lead_status=p.get("hs_lead_status") or "",
            n_negocios=int(p.get("num_associated_deals") or 0),
            campana=p.get("uvic_utm_campaign") or "",
            motivo=("Webinar" if config.es_webinar(p.get("uvic_utm_campaign"))
                    else "Importado"),
        ))
    leads = pd.DataFrame(filas)

    ids = [c["id"] for c in contactos]
    negocios = _negocios_de_contactos(token, ids, mapa)
    return leads, negocios


def _negocios_de_contactos(token: str, contact_ids: list, mapa: dict) -> pd.DataFrame:
    """Negocios (deals) asociados a una lista de contactos, con etapa y pipeline."""
    import requests
    if not contact_ids:
        return pd.DataFrame()

    # contacto -> deals
    deal_to_contact, deal_ids = {}, set()
    try:
        r = requests.post(f"{API}/crm/v4/associations/contact/deal/batch/read",
                          headers=_headers(token),
                          json={"inputs": [{"id": i} for i in contact_ids]}, timeout=60)
        r.raise_for_status()
        for it in r.json().get("results", []):
            frm = str(it.get("from", {}).get("id"))
            for t in it.get("to", []):
                did = str(t.get("toObjectId"))
                deal_ids.add(did)
                deal_to_contact.setdefault(did, frm)
    except Exception:  # noqa: BLE001
        return pd.DataFrame()
    if not deal_ids:
        return pd.DataFrame()

    # deals -> propiedades
    try:
        r = requests.post(f"{API}/crm/v3/objects/deals/batch/read",
                          headers=_headers(token),
                          json={"properties": ["dealname", "dealstage", "pipeline", "amount", "createdate"],
                                "inputs": [{"id": d} for d in deal_ids]}, timeout=60)
        r.raise_for_status()
        res = r.json().get("results", [])
    except Exception:  # noqa: BLE001
        return pd.DataFrame()

    filas = []
    for x in res:
        p = x.get("properties", {})
        filas.append(dict(
            deal_id=x.get("id"),
            contacto=deal_to_contact.get(str(x.get("id"))),
            dealname=p.get("dealname") or "—",
            pipeline=mapa["pipelines"].get(p.get("pipeline"), p.get("pipeline") or "—"),
            etapa=mapa["stages"].get(p.get("dealstage"), p.get("dealstage") or "—"),
            importe=float(p.get("amount") or 0),
            fecha_creacion=_a_fecha(p.get("createdate")),
        ))
    return pd.DataFrame(filas)
