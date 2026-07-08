"""
Genera el REFRESH TOKEN de Google Ads (para dejar el dashboard en vivo).

Requisitos previos:
  1. En Google Cloud Console (mismo proyecto con la Google Ads API habilitada):
     Credenciales → Crear ID de cliente OAuth → tipo "App de escritorio".
     Descarga el JSON (algo como client_secret_xxx.json).
  2. Ejecuta:
        python scripts/google_ads_refresh_token.py ruta/al/client_secret.json
  3. Se abrirá el navegador. Inicia sesión con una cuenta que TENGA acceso a la
     cuenta de Google Ads 2970533333 (rol Explorador/lectura es suficiente) y
     acepta los permisos.
  4. El script imprime el `refresh_token`. Pégalo en .streamlit/secrets.toml
     bajo [google_ads].
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/adwords"]


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/google_ads_refresh_token.py <client_secret.json>")
        sys.exit(1)
    client_secret_file = sys.argv[1]

    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    # Abre el navegador y levanta un servidor local para recibir el código.
    creds = flow.run_local_server(port=0, prompt="consent")

    print("\n" + "=" * 60)
    print("✅ REFRESH TOKEN generado. Cópialo a secrets.toml [google_ads]:")
    print("=" * 60)
    print(f"refresh_token = \"{creds.refresh_token}\"")
    print(f"client_id     = \"{creds.client_id}\"")
    print(f"client_secret = \"{creds.client_secret}\"")
    print("=" * 60)


if __name__ == "__main__":
    main()
