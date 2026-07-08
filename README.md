# Dashboard de Marketing — UVic / WeRise

Dashboard en **Streamlit** que unifica **Google Ads, Meta Ads, Google Analytics 4
y HubSpot** para medir la captación de las campañas WeRise de UVic: leads, CPL por
plataforma, CPL neto, asociación de leads a campañas, control de inversión y ROAS.

## Páginas

| Página | Contenido |
|---|---|
| **Resumen Global** (`app.py`) | Inversión, leads, CPL neto, ROAS, matrículas vs objetivo, embudo y tabla por campaña. |
| **🔍 Google Ads** | Inversión, CTR, CPC, conversiones y rendimiento por campaña. |
| **📱 Meta Ads** | Inversión, CPM, CPC y leads reales (vía HubSpot) frente a la atribución de la plataforma. |
| **📈 Google Analytics** | Sesiones, usuarios y conversiones por canal. |
| **🎯 Leads (HubSpot)** | Asociación lead↔campaña, CPL/coste-matrícula, embudo y leads recientes. |
| **🩺 Tracking & Atribución** | Semáforo de medición, diagnóstico de la rotura de atribución y checklist de corrección. |

## Puesta en marcha

```bash
cd /Users/misael/Documents/UVIC/Dashboard
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Se abre en `http://localhost:8501`. **Sin credenciales funciona ya** con datos de
ejemplo realistas (para validar la estructura y las visualizaciones).

## Conectar datos reales

1. Copia `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml`.
2. Rellena **solo** las plataformas que quieras conectar (las demás siguen con ejemplo).
3. Reinicia la app. El sidebar muestra el origen de cada fuente: **En vivo / Caché / Ejemplo**.

### Arquitectura de datos (importante)

Los conectores MCP de Claude (Google/Meta/HubSpot) **no** están disponibles dentro
de una app Streamlit desplegada. Por eso el dashboard usa **sus propias APIs**:

- **Google Ads** → SDK `google-ads` (OAuth refresh token).
- **Meta Ads** → Graph API vía `requests` (token de app/usuario del sistema).
- **GA4** → `google-analytics-data` con Service Account.
- **HubSpot** → CRM API v3 vía `requests` (Private App token).

Orden de resolución de cada conector: **API → caché local → datos de ejemplo**.
La caché (`data/cache/*.parquet`) puede rellenarla Claude vía MCP para tener datos
reales sin configurar todas las APIs.

## Parámetros de negocio

En [`src/config.py`](src/config.py):

- `VALOR_MATRICULA` — **ajústalo al precio real** de la matrícula (input clave del ROAS).
- `OBJETIVO_INVERSION_MENSUAL` = 17.002 € · `OBJETIVO_MATRICULAS` = 57.
- `CPL_OBJETIVO`, `TASA_LEAD_A_MATRICULA` — umbrales del semáforo y del forecast.
- `PROGRAMAS` — mapeo campaña (Google/Meta) → programa académico.

## Estructura

```
Dashboard/
├── app.py                     # Resumen Global
├── pages/                     # 5 páginas de detalle
├── src/
│   ├── config.py              # cuentas, objetivos, mapeo de campañas, tema
│   ├── connectors/            # google_ads, meta_ads, ga4, hubspot, base
│   ├── data/                  # loader, metrics, sample_data
│   └── ui/                    # theme, components
├── data/cache/                # caché de datos (git-ignored)
├── .streamlit/                # config.toml + secrets.toml.example
└── requirements.txt
```

## Despliegue en Streamlit Cloud

Sube el repo (sin `secrets.toml`) y pega las credenciales en **App settings →
Secrets** con el mismo formato del `.example`.
