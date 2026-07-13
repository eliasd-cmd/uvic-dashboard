"""
Generador de datos de ejemplo (mock) coherentes con la realidad conocida de
UVic/WeRise a jul-2026. Se usa como *fallback* cuando un conector no tiene
credenciales configuradas, para que el dashboard sea navegable desde el minuto
cero. Los datos son deterministas (semilla fija) para no cambiar en cada carga.
"""
from __future__ import annotations

import hashlib
from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.config import PROGRAMAS


def _rng(nombre: str) -> np.random.Generator:
    """RNG determinista derivado de un nombre (evita aleatoriedad por sesión)."""
    semilla = int(hashlib.md5(nombre.encode()).hexdigest()[:8], 16)
    return np.random.default_rng(semilla)


def _rango_fechas(dias: int) -> list[date]:
    fin = date(2026, 7, 7)
    return [fin - timedelta(days=i) for i in range(dias - 1, -1, -1)]


# --------------------------------------------------------------------------- #
# Google Ads
# --------------------------------------------------------------------------- #
def google_ads_diario(dias: int = 30) -> pd.DataFrame:
    fechas = _rango_fechas(dias)
    filas = []
    # Perfiles por campaña coherentes con el diagnóstico (WeRise Search casi sin
    # impresiones; el gasto se concentra en Display/branding).
    perfiles = {
        "WeRise_Search_NAC_MBA_Executive": dict(impr=90, ctr=0.05, cpc=1.4, cvr=0.04),
        "WeRise_Search_NAC_Master_Marqueting_Esportiu": dict(impr=40, ctr=0.04, cpc=1.2, cvr=0.03),
        "WeRise_Search_NAC_Postgrau_Documental_Social": dict(impr=25, ctr=0.04, cpc=1.1, cvr=0.03),
        "WeRise_Search_NAC_Postgrau_Comunicacio_Cientifica": dict(impr=30, ctr=0.05, cpc=1.0, cvr=0.03),
        "WeRise_Search_NAC_Postgrau_Lideratge_IA": dict(impr=20, ctr=0.04, cpc=1.3, cvr=0.02),
        "BRANDING UVIC-UCC": dict(impr=560, ctr=0.36, cpc=0.30, cvr=0.0),
        "LISA - 2026": dict(impr=115000, ctr=0.0003, cpc=8.71, cvr=0.0),
    }
    for campana, pf in perfiles.items():
        r = _rng("gads" + campana)
        for f in fechas:
            impr = max(0, int(r.normal(pf["impr"], pf["impr"] * 0.25)))
            clics = int(impr * pf["ctr"] * r.uniform(0.8, 1.2))
            coste = round(clics * pf["cpc"] * r.uniform(0.85, 1.15), 2)
            conv = int(clics * pf["cvr"] * r.uniform(0.5, 1.5))
            filas.append(dict(
                fecha=f, plataforma="Google Ads", campana=campana,
                impresiones=impr, clics=clics, coste=coste, conversiones=conv,
            ))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Meta Ads
# --------------------------------------------------------------------------- #
def meta_ads_diario(dias: int = 30) -> pd.DataFrame:
    fechas = _rango_fechas(dias)
    filas = []
    perfiles = {
        "WeRise_Executive MBA": dict(impr=3800, ctr=0.009, cpc=0.70, cvr=0.05),
        "WeRise_Màster Gestió i Màrqueting Esportiu": dict(impr=3200, ctr=0.008, cpc=0.65, cvr=0.05),
        "WeRise_Postgrau_Documental Social": dict(impr=2600, ctr=0.008, cpc=0.60, cvr=0.04),
        "WeRise_Postgrau_Comunicació Científica": dict(impr=3000, ctr=0.0102, cpc=0.49, cvr=0.06),
        "WeRise_EP_Lidera en entorns d'IA": dict(impr=2400, ctr=0.007, cpc=1.23, cvr=0.04),
    }
    for campana, pf in perfiles.items():
        r = _rng("meta" + campana)
        for f in fechas:
            impr = max(0, int(r.normal(pf["impr"], pf["impr"] * 0.2)))
            clics = int(impr * pf["ctr"] * r.uniform(0.8, 1.2))
            coste = round(clics * pf["cpc"] * r.uniform(0.85, 1.15), 2)
            # Meta atribuye 0 conversiones por la rotura conocida; el "lead real"
            # se ve en HubSpot. Guardamos conv_plataforma ~ 0 y leads en HubSpot.
            conv = 0
            filas.append(dict(
                fecha=f, plataforma="Meta Ads", campana=campana,
                impresiones=impr, clics=clics, coste=coste, conversiones=conv,
            ))
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------- #
# Google Analytics 4
# --------------------------------------------------------------------------- #
def ga4_diario(dias: int = 30) -> pd.DataFrame:
    """Tráfico de ejemplo de las 5 landings WeRise (por programa)."""
    from src.config import LANDING_PROGRAMA

    fechas = _rango_fechas(dias)
    filas = []
    for landing, programa in LANDING_PROGRAMA.items():
        r = _rng("ga4" + landing)
        base = r.uniform(25, 90)
        for f in fechas:
            sesiones = max(0, int(r.normal(base, base * 0.3)))
            usuarios = int(sesiones * r.uniform(0.75, 0.95))
            vistas = int(sesiones * r.uniform(1.1, 1.6))
            filas.append(dict(
                fecha=f, landing=landing, programa=programa,
                sesiones=sesiones, usuarios=usuarios, vistas=vistas,
                rebote=round(r.uniform(0.35, 0.70), 3),
                duracion_media=round(r.uniform(30, 150), 0),
            ))
    return pd.DataFrame(filas)


def ga4_por_fuente(dias: int = 30) -> pd.DataFrame:
    """Tráfico de ejemplo por fuente/medio de las 5 landings."""
    r = _rng("ga4-fuente")
    fuentes = [("meta", "ads"), ("google", "cpc"), ("fb", "ads"), ("ig", "ads"),
               ("(direct)", "(none)"), ("google", "organic")]
    filas = []
    for f, m in fuentes:
        ses = int(r.uniform(20, 400))
        filas.append(dict(fuente=f, medio=m, sesiones=ses,
                          usuarios=int(ses * r.uniform(0.8, 0.98)),
                          eventos=int(ses * r.uniform(3, 4)),
                          eventos_clave=int(ses * r.uniform(0.02, 0.05))))
    return pd.DataFrame(filas).sort_values("sesiones", ascending=False)


def ga4_por_campana(dias: int = 30) -> pd.DataFrame:
    """Tráfico de ejemplo por campaña de las 5 landings."""
    r = _rng("ga4-campana")
    filas = []
    for p in PROGRAMAS:
        for camp in (p.campana_meta, p.campana_google):
            ses = int(r.uniform(20, 250))
            filas.append(dict(campana=camp, sesiones=ses,
                              usuarios=int(ses * r.uniform(0.8, 0.98)),
                              eventos=int(ses * r.uniform(3, 4)),
                              eventos_clave=int(ses * r.uniform(0.0, 0.05))))
    return pd.DataFrame(filas).sort_values("sesiones", ascending=False)


# --------------------------------------------------------------------------- #
# HubSpot — leads (contactos) con atribución a campaña
# --------------------------------------------------------------------------- #
def hubspot_leads(dias: int = 30) -> pd.DataFrame:
    """Leads UVic de ejemplo = contactos con `uvic_curso` (mapeados a programa).

    La atribución de campaña llega OFFLINE (se pierde), así que `campana` va vacía
    y la asociación es por programa. Estado del ciclo de vida del contacto.
    """
    fechas = _rango_fechas(dias)
    r = _rng("hubspot-leads")
    filas = []
    estados = ["Lead", "MQL", "SQL", "Oportunidad", "Matriculado", "Descartado"]
    prob_estado = [0.34, 0.20, 0.14, 0.20, 0.04, 0.08]
    programas = [p.nombre for p in PROGRAMAS]

    lead_id = 1000
    for f in fechas:
        n_dia = int(r.normal(18, 5))
        for _ in range(max(0, n_dia)):
            programa = programas[r.choice(len(programas))]
            estado = estados[r.choice(len(estados), p=prob_estado)]
            lead_id += 1
            filas.append(dict(
                lead_id=f"C{lead_id}", fecha_creacion=f,
                fuente="OFFLINE", campana="", programa=programa,
                nivel="Master", estado=estado,
                es_matricula=(estado == "Matriculado"),
            ))
    return pd.DataFrame(filas)


def import_leads(dias: int = 30) -> pd.DataFrame:
    """Leads importados de ejemplo (control aparte)."""
    fechas = _rango_fechas(dias)
    r = _rng("import-leads")
    estados = ["Lead", "MQL", "SQL", "Oportunidad", "Descartado"]
    programas = [p.nombre for p in PROGRAMAS]
    filas = []
    for i in range(40):
        filas.append(dict(
            lead_id=f"I{9000+i}",
            nombre=f"Lead importado {i+1}",
            email=f"importado{i+1}@ejemplo.com",
            fecha_creacion=fechas[r.integers(0, len(fechas))],
            programa=programas[r.integers(0, len(programas))],
            nivel="Master",
            estado=estados[r.integers(0, len(estados))],
            lead_status="",
            n_negocios=int(r.integers(0, 2)),
        ))
    return pd.DataFrame(filas)


def import_negocios(dias: int = 30) -> pd.DataFrame:
    """Negocios de ejemplo de leads importados."""
    fechas = _rango_fechas(dias)
    r = _rng("import-negocios")
    filas = []
    for i in range(8):
        filas.append(dict(
            deal_id=f"ID{7000+i}",
            contacto=f"I{9000+i}",
            dealname=f"Negocio importado {i+1}",
            pipeline="Pipeline de ventas",
            etapa=["Cita programada", "Nuevo lead", "En estudio"][r.integers(0, 3)],
            importe=0.0,
            fecha_creacion=fechas[r.integers(0, len(fechas))],
        ))
    return pd.DataFrame(filas)


def hubspot_deals(dias: int = 30) -> pd.DataFrame:
    """Deals de ejemplo del Pipeline UVIC, con etapa y programa."""
    from src.config import HUBSPOT_ETAPAS_UVIC

    fechas = _rango_fechas(dias)
    r = _rng("hubspot-deals")
    etapas = HUBSPOT_ETAPAS_UVIC  # [(id, label), ...] en orden de embudo
    prob = [0.55, 0.18, 0.12, 0.08, 0.07]
    programas = [p.nombre for p in PROGRAMAS]
    filas = []
    deal_id = 5000
    for f in fechas:
        n_dia = int(r.normal(2, 1))
        for _ in range(max(0, n_dia)):
            i = r.choice(len(etapas), p=prob)
            etapa_id, etapa = etapas[i]
            deal_id += 1
            filas.append(dict(
                deal_id=f"D{deal_id}", fecha_creacion=f,
                etapa_id=etapa_id, etapa=etapa,
                programa=programas[r.choice(len(programas))],
                amount=0.0, es_ganado=(etapa == "Cierre ganado"),
            ))
    return pd.DataFrame(filas)
