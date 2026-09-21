"""Módulo de Integración de Pagos con Firma HMAC e Idempotencia (Enmienda 1 - CRÍTICA).

Ruta: POST /api/pagos/webhook
- Validación de firma HMAC SHA-256 (Header X-Signature) -> 401 si falla
- Idempotencia por event_id (colección eventos_procesados) -> 200 sin duplicar puntos
- Deduplicación de puntos del concurso por lead_id + tipo_evento + ventana
"""
import hmac
import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Request, HTTPException, status, Header
from pydantic import BaseModel

from ..config import settings
from ..db_mongo import save_evento_procesado

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pagos", tags=["Pagos"])


class WebhookPagoPayload(BaseModel):
    event_id: str
    lead_id: str
    monto: float = 0.0
    tipo_evento: str = "pago_plan"  # pago_plan / invitacion / concurso
    ventana: str = "2026-Q3"
    metadata: Dict[str, Any] = {}


def verificar_firma_hmac(body_bytes: bytes, signature_header: str | None) -> bool:
    """Verifica la firma HMAC-SHA256 del body crudo con payment_webhook_secret."""
    if not signature_header:
        return False
    expected_hmac = hmac.new(
        settings.payment_webhook_secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_hmac.lower(), signature_header.lower())


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook_pago(
    request: Request,
    x_signature: str | None = Header(None, alias="X-Signature")
):
    """Procesa webhooks de pagos con firma HMAC SHA-256 e idempotencia estricta."""
    body_bytes = await request.body()

    # 1. Validación de Firma HMAC
    firma_valida = verificar_firma_hmac(body_bytes, x_signature)
    if not firma_valida:
        logger.warning("Intento de webhook de pagos sin firma válida. Registrando auditoría 401.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma HMAC no válida o ausente en header X-Signature"
        )

    # Parsear payload JSON
    try:
        payload_dict = await request.json()
        payload = WebhookPagoPayload(**payload_dict)
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payload JSON inválido: {err}"
        )

    # 2. Idempotencia y Deduplicación
    evento_data = {
        "event_id": payload.event_id,
        "lead_id": payload.lead_id,
        "tipo_evento": payload.tipo_evento,
        "ventana": payload.ventana,
        "monto": payload.monto,
        "metadata": payload.metadata
    }

    exito_guardado = save_evento_procesado(evento_data)
    if not exito_guardado:
        logger.info(f"Evento {payload.event_id} para lead {payload.lead_id} ya fue procesado previamente. Retornando 200 OK idempotente.")
        return {
            "status": "already_processed",
            "message": "Evento idempotente ignorado sin duplicación de puntos",
            "event_id": payload.event_id,
            "puntos_acreditados": 0
        }

    # 3. Acreditación de puntos (1 punto por evento deduplicado)
    puntos = 1 if payload.tipo_evento == "invitacion" else settings.puntos_por_plan

    return {
        "status": "success",
        "message": "Webhook procesado y acreditado correctamente",
        "event_id": payload.event_id,
        "lead_id": payload.lead_id,
        "puntos_acreditados": puntos
    }
