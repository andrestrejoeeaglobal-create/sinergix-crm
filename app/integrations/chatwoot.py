"""Cliente de Chatwoot. Sin CHATWOOT_URL configurado → modo mock (mensajes en memoria)."""
import logging

import httpx

from ..config import settings

log = logging.getLogger("sinergix.chatwoot")


class ChatwootClient:
    """Envía mensajes/plantillas. En modo mock registra todo en `enviados` (para tests)."""

    def __init__(self) -> None:
        self.mock = not settings.chatwoot_url
        self.enviados: list[dict] = []  # solo modo mock

    def send_text(self, telefono: str, texto: str, plantilla: str | None = None) -> dict:
        """Envía un mensaje a un contacto por teléfono.

        En producción: crea/encuentra contacto+conversación en Chatwoot y publica
        el mensaje saliente (plantilla HSM fuera de ventana 24h).
        En mock: solo lo registra.
        `texto` debe venir YA validado por SafetyEngine.
        """
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

        # Implementación real (F1, tras verificar Meta Business):
        resp = httpx.post(
            f"{settings.chatwoot_url}/api/v1/accounts/{settings.chatwoot_account_id}/conversations",
            headers={"api_access_token": settings.chatwoot_api_key},
            json={
                "source_id": telefono,
                "inbox_id": settings.chatwoot_inbox_id,
                "contact": {"phone": telefono},
                "message": {"content": texto, "message_type": "outgoing"},
            },
            timeout=15,
        )
        resp.raise_for_status()
        registro["chatwoot_response"] = resp.json()
        return registro


# Instancia única en modo mock para que los tests inspeccionen `enviados`
client = ChatwootClient()
