"""
Configuración central del Dashboard UVic / WeRise.

Todos los identificadores de cuenta, objetivos de negocio y el mapeo de
campañas viven aquí para que las páginas y los conectores lean de una
única fuente de verdad.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# --------------------------------------------------------------------------- #
# Cuentas de plataforma
# --------------------------------------------------------------------------- #

# Google Ads (EUR). La cuenta con las campañas WeRise es la 2970533333 "UVic".
# Verificado: contiene WeRise_Search_NAC_* + LISA-2026 + BRANDING UVIC-UCC.
# El MCC de login puede ser Nuclio (3963262878) o "UVic MCC - Rise Marketing"
# (9010916591) según con qué credenciales se autentique la API directa.
GOOGLE_ADS_CUSTOMER_ID = "2970533333"
GOOGLE_ADS_LOGIN_CUSTOMER_ID = "3963262878"  # MCC de login (ajustar si procede)

# Meta Ads: cuenta publicitaria UVic-UCC.
META_AD_ACCOUNT_ID = "act_33542477"
META_BUSINESS_ID = "127243537925769"
META_PIXEL_DATASET_ID = "201468227580360"  # "Cloud Pages Pixel" (el bueno)

# Google Analytics 4: "Cloud Pages Salesforce - GA4".
GA4_PROPERTY_ID = "properties/308288730"

# HubSpot: portal objetivo "Rise Education" (144637943). OJO: pendiente de conectar
# vía /mcp — el conector activo apunta a otro portal (143302790). No usar el 143302790
# para datos de UVic salvo confirmación.
HUBSPOT_PORTAL_ID = "144637943"

# --------------------------------------------------------------------------- #
# Objetivos de negocio (Etapa 1 — referencia jun-2026)
# --------------------------------------------------------------------------- #

# Objetivo de referencia: ~17.002 €/mes de inversión -> 57 matrículas.
OBJETIVO_INVERSION_MENSUAL = 17002.0
OBJETIVO_MATRICULAS = 57

# Valor económico medio de una matrícula (EUR) — PVP medio confirmado por UVic/WeRise.
# Input clave para el cálculo de ROAS (ingresos = matrículas × VALOR_MATRICULA).
VALOR_MATRICULA = 2100.0

# CPL objetivo (coste por lead) de referencia para el semáforo. Ajustable.
CPL_OBJETIVO = 45.0

# Tasa de conversión lead -> matrícula esperada (para el forecast del embudo).
TASA_LEAD_A_MATRICULA = 0.06  # 6%

MONEDA = "EUR"
SIMBOLO_MONEDA = "€"


# --------------------------------------------------------------------------- #
# Mapeo de campañas WeRise  ->  programa académico
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Programa:
    """Un programa académico, sus campañas en cada plataforma y su valor en
    HubSpot (propiedad de contacto `uvic_curso`)."""
    nombre: str
    slug: str
    campana_google: str
    campana_meta: str
    uvic_curso: str  # valor de la propiedad uvic_curso en HubSpot


PROGRAMAS: list[Programa] = [
    Programa(
        nombre="MBA Executive",
        slug="mba-executive",
        campana_google="WeRise_Search_NAC_MBA_Executive",
        campana_meta="WeRise_Executive MBA",
        uvic_curso="WeRise_ExecutiveMBA",
    ),
    Programa(
        nombre="Marketing Deportivo",
        slug="marketing-deportivo",
        campana_google="WeRise_Search_NAC_Master_Marqueting_Esportiu",
        campana_meta="WeRise_Màster_Gestió i Màrqueting Esportiu",
        uvic_curso="WeRise_Gestió_Màrqueting_Esportiu",
    ),
    Programa(
        nombre="Documentación Social",
        slug="documentacion-social",
        campana_google="WeRise_Search_NAC_Postgrau_Documental_Social",
        campana_meta="WeRise_Postgrau_Documental Social",
        uvic_curso="WeRise_Documental_Social",
    ),
    Programa(
        nombre="Comunicación Científica",
        slug="comunicacion-cientifica",
        campana_google="WeRise_Search_NAC_Postgrau_Comunicacio_Cientifica",
        campana_meta="WeRise_Postgrau_Comunicació Científica",
        uvic_curso="WeRise_Comunicació_Científica",
    ),
    Programa(
        nombre="Liderazgo IA",
        slug="liderazgo-ia",
        campana_google="WeRise_Search_NAC_Postgrau_Lideratge_IA",
        campana_meta="WeRise_EP_Lidera en entorns d'Intel·ligència Artificial",
        uvic_curso="WeRise_Lidera_en_entorns_IA",
    ),
]


def programa_por_campana(nombre_campana: str) -> str:
    """Devuelve el nombre del programa dado el nombre de campaña (Google o Meta).

    Hace una coincidencia laxa por prefijo para tolerar sufijos y variaciones.
    """
    if not nombre_campana:
        return "Sin asignar"
    n = nombre_campana.strip().lower()
    for p in PROGRAMAS:
        for c in (p.campana_google, p.campana_meta):
            if n.startswith(c.lower()) or c.lower() in n:
                return p.nombre
    return "Otras / Branding"


def programa_por_curso(uvic_curso: str) -> str:
    """Devuelve el nombre del programa dado el valor de `uvic_curso` (HubSpot)."""
    if not uvic_curso:
        return "Sin asignar"
    u = uvic_curso.strip()
    for p in PROGRAMAS:
        if p.uvic_curso == u:
            return p.nombre
    return "Sin asignar"


# --------------------------------------------------------------------------- #
# HubSpot — Pipeline UVIC y etapas del embudo (portal 144637943)
# --------------------------------------------------------------------------- #
HUBSPOT_PIPELINE_UVIC = "3920516288"
HUBSPOT_STAGE_MATRICULA = "5604424920"  # "Cierre ganado"

# Etapas del Pipeline UVIC en orden (id -> etiqueta). El embudo se dibuja así.
HUBSPOT_ETAPAS_UVIC = [
    ("5604424915", "Oportunidad"),
    ("5604424916", "Entrevista concertada"),
    ("5604424917", "Entrevista realizada"),
    ("5604424918", "Envío de inscripción"),
    ("5604424920", "Cierre ganado"),
]
HUBSPOT_ETAPA_PERDIDO = ("5604424921", "Cierre perdido")
HUBSPOT_ETAPAS_MAP = dict(HUBSPOT_ETAPAS_UVIC + [HUBSPOT_ETAPA_PERDIDO])


# --------------------------------------------------------------------------- #
# Paleta y colores por plataforma (consistentes en todo el dashboard)
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Tema:
    # Colores corporativos UVic (extraídos del CSS de uvic.cat): rojo granate.
    primario: str = "#CF0A2C"       # rojo UVic (color de marca principal)
    secundario: str = "#7C061A"     # granate oscuro (acento)
    gris_uvic: str = "#4B4B4B"      # gris corporativo
    texto: str = "#212529"          # texto casi negro
    # Colores de identidad por plataforma (se mantienen para distinguir series).
    color_google: str = "#4285F4"
    color_meta: str = "#0866FF"
    color_ga4: str = "#E8710A"
    color_hubspot: str = "#FF7A59"
    # Semáforo de estado.
    verde_ok: str = "#198754"       # verde de la paleta UVic/bootstrap
    ambar_riesgo: str = "#D97706"
    rojo_off: str = "#CF0A2C"
    # Paleta de gráficos: lidera el granate UVic, luego neutros y acentos.
    paleta: tuple = field(default_factory=lambda: (
        "#CF0A2C", "#4B4B4B", "#7C061A", "#E8710A", "#0866FF", "#198754",
    ))


TEMA = Tema()

COLOR_PLATAFORMA = {
    "Google Ads": TEMA.color_google,
    "Meta Ads": TEMA.color_meta,
    "Google Analytics": TEMA.color_ga4,
    "HubSpot": TEMA.color_hubspot,
}
