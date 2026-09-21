"""Configuración central del CRM Sinergix Negocio (Fase 0)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos: producción PostgreSQL; local/tests SQLite
    database_url: str = "sqlite:///./crm.db"

    # Firma HMAC del webhook de pagos (el procesador firma el body crudo)
    payment_webhook_secret: str = "dev-secret-cambiar-en-produccion"

    # Puntos por plan vendido (valor oficial lo definirá el sistema externo)
    puntos_por_plan: int = 100

    # Token opcional del cron nocturno (header X-Cron-Token)
    cron_token: str = ""

    # Chatwoot — vacío = modo mock (mensajes en memoria, no salen)
    chatwoot_url: str = ""
    chatwoot_api_key: str = ""
    chatwoot_account_id: int = 1
    chatwoot_inbox_id: int = 1

    # Sistema externo de cotización (SQL Server vía adaptador) — vacío = mock
    cotizacion_url: str = ""
    cotizacion_token: str = ""

    # BiometriaAPI (Cloud Functions Firebase) — vacío = mock
    biometria_url: str = ""
    biometria_token: str = ""

    # Google OAuth (Sherpas) + People API (contactos)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
