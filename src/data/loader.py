"""
Orquestador de datos: llama a cada conector con caché de Streamlit y expone
un objeto único `DatosDashboard` que consumen todas las páginas.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st

from src.connectors import ga4, google_ads, hubspot, meta_ads


@dataclass
class DatosDashboard:
    google: pd.DataFrame
    meta: pd.DataFrame
    ga4: pd.DataFrame
    leads: pd.DataFrame
    deals: pd.DataFrame
    origenes: dict  # {"Google Ads": "sample", ...}

    @property
    def ads(self) -> pd.DataFrame:
        """Google + Meta unificados (mismo esquema de columnas)."""
        frames = [d for d in (self.google, self.meta) if not d.empty]
        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    def hay_datos_reales(self) -> bool:
        return any(o in ("api", "cache") for o in self.origenes.values())


@st.cache_data(ttl=1800, show_spinner="Cargando datos de las plataformas…")
def cargar_todo(dias: int = 30) -> DatosDashboard:
    g = google_ads.obtener(dias)
    m = meta_ads.obtener(dias)
    a = ga4.obtener(dias)
    h = hubspot.obtener(dias)
    d = hubspot.obtener_deals(dias)
    return DatosDashboard(
        google=g.df,
        meta=m.df,
        ga4=a.df,
        leads=h.df,
        deals=d.df,
        origenes={
            "Google Ads": g.origen,
            "Meta Ads": m.origen,
            "Google Analytics": a.origen,
            "HubSpot": h.origen,
        },
    )
