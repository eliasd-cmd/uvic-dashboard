"""
Orquestador de datos: llama a cada conector con caché de Streamlit y expone
un objeto único `DatosDashboard` que consumen todas las páginas.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from src import config
from src.connectors import ga4, google_ads, hubspot, meta_ads


@dataclass
class DatosDashboard:
    google: pd.DataFrame
    meta: pd.DataFrame
    ga4: pd.DataFrame
    leads: pd.DataFrame
    deals: pd.DataFrame
    origenes: dict  # {"Google Ads": "sample", ...}
    leads_import: pd.DataFrame = field(default_factory=pd.DataFrame)
    negocios_import: pd.DataFrame = field(default_factory=pd.DataFrame)
    origen_import: str = "sample"
    ga4_fuente: pd.DataFrame = field(default_factory=pd.DataFrame)
    ga4_campana: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def ads(self) -> pd.DataFrame:
        """Google + Meta unificados (mismo esquema de columnas)."""
        frames = [d for d in (self.google, self.meta) if not d.empty]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def hay_datos_reales(self) -> bool:
        return any(o in ("api", "cache") for o in self.origenes.values())


# Caché por fuente con TTL distinto: HubSpot corto (cambia a diario), ads/GA4 largo.
@st.cache_data(ttl=config.CACHE_TTL_ADS, show_spinner="Cargando Google Ads…")
def _cargar_google(dias: int):
    r = google_ads.obtener(dias)
    return r.df, r.origen


@st.cache_data(ttl=config.CACHE_TTL_ADS, show_spinner="Cargando Meta Ads…")
def _cargar_meta(dias: int):
    r = meta_ads.obtener(dias)
    return r.df, r.origen


@st.cache_data(ttl=config.CACHE_TTL_GA4, show_spinner="Cargando GA4…")
def _cargar_ga4(dias: int):
    r = ga4.obtener(dias)
    rf = ga4.obtener_fuente(dias)
    rc = ga4.obtener_campana(dias)
    return r.df, r.origen, rf.df, rc.df


@st.cache_data(ttl=config.CACHE_TTL_HUBSPOT, show_spinner="Cargando HubSpot…")
def _cargar_hubspot(dias: int):
    leads = hubspot.obtener(dias)
    deals = hubspot.obtener_deals(dias)
    return leads.df, leads.origen, deals.df


@st.cache_data(ttl=config.CACHE_TTL_HUBSPOT, show_spinner="Cargando leads importados…")
def _cargar_importados():
    leads_i, negocios_i, origen_i = hubspot.importados()
    return leads_i, negocios_i, origen_i


def cargar_todo(dias: int = 30) -> DatosDashboard:
    g_df, g_o = _cargar_google(dias)
    m_df, m_o = _cargar_meta(dias)
    a_df, a_o, af_df, ac_df = _cargar_ga4(dias)
    l_df, l_o, d_df = _cargar_hubspot(dias)
    li_df, ni_df, oi = _cargar_importados()
    return DatosDashboard(
        google=g_df, meta=m_df, ga4=a_df, leads=l_df, deals=d_df,
        origenes={
            "Google Ads": g_o,
            "Meta Ads": m_o,
            "Google Analytics": a_o,
            "HubSpot": l_o,
        },
        leads_import=li_df, negocios_import=ni_df, origen_import=oi,
        ga4_fuente=af_df, ga4_campana=ac_df,
    )
