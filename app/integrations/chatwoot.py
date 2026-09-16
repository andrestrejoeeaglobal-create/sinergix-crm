"""Cliente y utilidades de integración con Chatwoot (ENMIENDA 7).

Sin CHATWOOT_URL configurado → modo mock (mensajes en memoria).
Soporta validación de firma HMAC con `CHATWOOT_WEBHOOK_SECRET` y sincronización de custom attributes.
"""
import hashlib
import hmac
import logging
from typing import Any

import httpx

from ..config import settings

log = logging.getLogger("sinergix.chatwoot")


def validar_firma_chatwoot(body_crudo: bytes, firma_recibida: str) -> bool:
    """Valida la firma del webhook entrante de Chatwoot."""
    if not settings.chatwoot_webhook_secret or not firma_recibida:
        return True  # Si no hay secret configurado en dev, permite el paso
    esperada = hmac.new(
        settings.chatwoot_webhook_secret.encode("utf-8"),
        body_crudo,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(esperada, firma_recibida)


class ChatwootClient:
    """Envía mensajes/plantillas y actualiza atributos. En modo mock registra todo en `enviados`."""

    def __init__(self) -> None:
        self.mock = not settings.chatwoot_url
        self.enviados: list[dict] = []  # solo modo mock

    def send_text(self, telefono: str, texto: str, plantilla: str | None = None) -> dict:
        """Envía un mensaje a un contacto por teléfono."""
        registro = {
            "telefono": telefono,
            "texto": texto,
            "plantilla": plantilla,
            "modo": "mock" if self.mock else "live",
        }
        if self.mock:
            self.enviados.append(registro)
            log.info("[MOCK Chatwoot] → %s | plantilla=%s | %.80s", telefono, plantilla, texto)
            return {"ok": True, "mock": True, **registro}

        try:
            resp = httpx.post(
                f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations",
                headers={"api_access_token": settings.chatwoot_api_key},
                json={
                    "source_id": telefono,
                    "inbox_id": settings.chatwoot_inbox_id,
                    "contact": {"phone_number": telefono},
                    "message": {"content": texto, "message_type": "outgoing"},
                },
                timeout=15,
            )
            resp.raise_for_status()
            registro["chatwoot_response"] = resp.json()
            return registro
        except Exception as exc:
            log.error("Error enviando mensaje a Chatwoot: %s", exc)
            return {"ok": False, "error": str(exc), **registro}

    def sync_custom_attributes(self, telefono: str, atributos: dict[str, Any]) -> dict[str, Any]:
        """Sincroniza custom attributes en el contacto de Chatwoot."""
        if self.mock:
            log.info("[MOCK Chatwoot] Sync custom attributes para %s: %s", telefono, atributos)
            return {"ok": True, "mock": True, "atributos": atributos}

        try:
            # Buscar contacto por teléfono
            url_search = f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/contacts/search"
            headers = {"api_access_token": settings.chatwoot_api_key}
            resp_s = httpx.get(url_search, params={"q": telefono}, headers=headers, timeout=10)
            if resp_s.status_code == 200 and resp_s.json().get("payload"):
                contact_id = resp_s.json()["payload"][0]["id"]
                url_update = f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/contacts/{contact_id}"
                httpx.put(url_update, json={"custom_attributes": atributos}, headers=headers, timeout=10)
            return {"ok": True, "atributos": atributos}
        except Exception as exc:
            log.error("Error sincronizando custom attributes con Chatwoot: %s", exc)
            return {"ok": False, "error": str(exc)}


client = ChatwootClient()
