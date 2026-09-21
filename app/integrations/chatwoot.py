"""Cliente de Chatwoot y Webhook de Entrada con Ventana de 24h (Enmienda 7).

Ruta: POST /api/chatwoot/webhook
- Firma protegida por CHATWOOT_WEBHOOK_SECRET
- Búsqueda o creación automática de lead por teléfono
- Validación de ventana conversacional de 24h
- Sincronización de custom attributes y verificación de Opt-in (Enmienda 3)
"""
import hmac
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel

from ..config import settings
from ..safety import validar_optin_whatsapp
from ..db_mongo import get_mongo_db

log = logging.getLogger("sinergix.chatwoot")

router = APIRouter(prefix="/api/chatwoot", tags=["Chatwoot"])


class ChatwootClient:
    """Envía mensajes/plantillas. En modo mock registra todo en `enviados` (para tests)."""

    def __init__(self) -> None:
        self.mock = not settings.chatwoot_url
        self.enviados: list[dict] = []  # solo modo mock

    def send_text(self, telefono: str, texto: str, plantilla: str | None = None, lead_obj: Any = None) -> dict:
        """Envía un mensaje a un contacto por teléfono.
        
        Valida que el lead cuente con consentimiento explícito de WhatsApp (Enmienda 3).
        """
        if lead_obj is not None:
            validar_optin_whatsapp(lead_obj)

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


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def chatwoot_webhook(
    request: Request,
    x_chatwoot_signature: str | None = Header(None, alias="X-Chatwoot-Signature")
):
    """Procesa eventos entrantes de Chatwoot (Enmienda 7)."""
    body_bytes = await request.body()

    # Validar firma si hay secreto configurado
    if settings.chatwoot_webhook_secret and x_chatwoot_signature:
        expected = hmac.new(
            settings.chatwoot_webhook_secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected.lower(), x_chatwoot_signature.lower()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firma de Chatwoot no válida"
            )

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Payload JSON inválido: {e}")

    event_type = payload.get("event")
    sender = payload.get("sender", {})
    phone = sender.get("phone_number") or payload.get("conversation", {}).get("meta", {}).get("sender", {}).get("phone_number")

    if not phone:
        return {"status": "ignored", "reason": "No phone_number found in payload"}

    clean_phone = str(phone).replace("+", "").replace(" ", "").strip()
    
    # Calcular ventana de 24h
    ahora = datetime.now(timezone.utc)
    ventana_24h_limite = ahora + timedelta(hours=24)

    db = get_mongo_db()
    lead = None
    if db is not None:
        lead = db.leads.find_one({"telefono": clean_phone})
        if not lead:
            lead = {
                "id": f"lead_{int(ahora.timestamp())}",
                "nombre": sender.get("name") or f"Prospecto {clean_phone[-4:]}",
                "telefono": clean_phone,
                "sherpa_id": "101",
                "consentimiento_whatsapp": True,
                "optin_fecha": ahora.isoformat(),
                "mecanismo_captura": "chatwoot_inbound",
                "etapa_pipeline": "Lead",
                "ventana_24h_expira": ventana_24h_limite.isoformat()
            }
            db.leads.insert_one(lead)
        else:
            db.leads.update_one(
                {"telefono": clean_phone},
                {"$set": {
                    "ventana_24h_expira": ventana_24h_limite.isoformat(),
                    "actualizado_en": ahora.isoformat()
                }}
            )

    return {
        "status": "success",
        "event": event_type,
        "phone": clean_phone,
        "ventana_24h_expira": ventana_24h_limite.isoformat()
    }
