"""Gestión centralizada de configuraciones y entornos mediante pydantic-settings."""
import os
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "sinergix_crm"
    payment_webhook_secret: str = "whsec_sinergix_secret_key_2026_prod"
    chatwoot_webhook_secret: str = ""
    cron_secret_token: str = "cron_secret_token_2026"
    cron_token: str = "cron_secret_token_2026"
    api_secret_key: str = "api_secret_key_sinergix_2026"
    default_sherpa_token: str = "token-default"
    environment: str = "development"
    port: int = 8000
    puntos_por_plan: int = 100

    # Integraciones externas (Chatwoot, Telegram, Cotización, Biometría)
    chatwoot_url: str = ""
    chatwoot_access_token: str = ""
    chatwoot_account_id: str = ""
    chatwoot_inbox_id: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    cotizacion_url: str = ""
    cotizacion_token: str = ""
    cotizacion_api_url: str = ""
    cotizacion_api_token: str = ""

    biometria_url: str = ""
    biometria_token: str = ""

    google_client_id: str = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
    google_client_secret: str = "YOUR_GOOGLE_CLIENT_SECRET"
    google_redirect_uri: str = "http://127.0.0.1:8080/api/auth/google/callback"
    google_apps_script_url: str = "https://script.google.com/macros/s/AKfycbzEuZP1aTnU-HQCjscDv9RDoG0rTF-hJnDSZ-i_T5HiNX0hKN2i_1vkAnB8c8esu1SMbw/exec"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
