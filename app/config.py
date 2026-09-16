"""Gestión centralizada de configuraciones y entornos mediante pydantic-settings."""
import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db_name: str = os.getenv("MONGO_DB_NAME", "sinergix_crm")
    payment_webhook_secret: str = os.getenv("PAYMENT_WEBHOOK_SECRET", "")
    chatwoot_webhook_secret: str = os.getenv("CHATWOOT_WEBHOOK_SECRET", "")
    cron_secret_token: str = os.getenv("CRON_SECRET_TOKEN", "")
    cron_token: str = os.getenv("CRON_TOKEN", "")
    api_secret_key: str = os.getenv("API_SECRET_KEY", "")
    default_sherpa_token: str = os.getenv("DEFAULT_SHERPA_TOKEN", "")
    environment: str = os.getenv("ENVIRONMENT", "development")
    port: int = int(os.getenv("PORT", "8000"))
    puntos_por_plan: int = 100

    # Integraciones externas (Chatwoot, Telegram, Cotización, Biometría)
    chatwoot_url: str = os.getenv("CHATWOOT_URL", "")
    chatwoot_access_token: str = os.getenv("CHATWOOT_ACCESS_TOKEN", "")
    chatwoot_account_id: str = os.getenv("CHATWOOT_ACCOUNT_ID", "")
    chatwoot_inbox_id: str = os.getenv("CHATWOOT_INBOX_ID", "")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    cotizacion_url: str = os.getenv("COTIZACION_URL", "")
    cotizacion_token: str = os.getenv("COTIZACION_TOKEN", "")
    cotizacion_api_url: str = os.getenv("COTIZACION_API_URL", "")
    cotizacion_api_token: str = os.getenv("COTIZACION_API_TOKEN", "")

    biometria_url: str = os.getenv("BIOMETRIA_URL", "")
    biometria_token: str = os.getenv("BIOMETRIA_TOKEN", "")

    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    google_apps_script_url: str = os.getenv("GOOGLE_APPS_SCRIPT_URL", "")

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
