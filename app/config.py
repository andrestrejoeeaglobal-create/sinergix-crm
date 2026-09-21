"""Configuración central del CRM Sinergix Negocio (Fase 1 - Sprint 28)."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos: producción PostgreSQL / SQLite + MongoDB local (servidor propio)
    database_url: str = "sqlite:///./crm.db"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "sinergix_crm"

    # Firma HMAC del webhook de pagos (el procesador firma el body crudo con X-Signature)
    payment_webhook_secret: str = "dev-secret-cambiar-en-produccion"

    # Chatwoot Webhook Secret (Enmienda 7)
    chatwoot_webhook_secret: str = "chatwoot-secret-dev"

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

    # BiometriaAPI (Cloud Functions) — vacío = mock
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
