"""Adaptador de Integración con Telegram Bot (para bot de Memo).

Maneja mensajes entrantes de Telegram y envío de notificaciones filtradas por SafetyEngine.
"""
import logging
from typing import Any

import httpx

from ..config import settings
from ..safety import validate

log = logging.getLogger("sinergix.telegram")


def enviar_mensaje_telegram(chat_id: str | int, texto: str) -> dict[str, Any]:
    """Envía un mensaje por Telegram pasando primero por SafetyEngine."""
    chequeo = validate(texto)
    texto_seguro = chequeo["texto_seguro"]

    if not settings.telegram_bot_token:
        log.info("[MOCK Telegram] -> chat_id=%s | %.80s", chat_id, texto_seguro)
        return {"ok": True, "modo": "mock", "chat_id": chat_id, "texto": texto_seguro}

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    try:
        resp = httpx.post(url, json={"chat_id": chat_id, "text": texto_seguro}, timeout=10)
        resp.raise_for_status()
        return {"ok": True, "modo": "live", "response": resp.json()}
    except Exception as exc:
        log.error("Error enviando mensaje Telegram: %s", exc)
        return {"ok": False, "error": str(exc)}
