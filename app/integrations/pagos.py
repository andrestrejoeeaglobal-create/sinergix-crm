"""Módulo de Integración de Pagos (ENMIENDA 1 — CRÍTICA).

Validación de firma HMAC-SHA256 (header X-Signature).
Idempotencia por `event_id` y deduplicación de puntos del concurso (1 punto máximo por invitación).
"""
import hashlib
import hmac
import logging
from typing import Any

from ..config import settings

log = logging.getLogger("sinergix.pagos")


def validar_firma_hmac(body_crudo: bytes, firma_recibida: str) -> bool:
    """Valida la firma HMAC-SHA256 del body del webhook con la clave compartida."""
    if not firma_recibida:
        return False
    esperada = hmac.new(
        settings.payment_webhook_secret.encode("utf-8"),
        body_crudo,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(esperada, firma_recibida)


def verificar_idempotencia_y_registrar(
    db: Any,
    event_id: str,
    lead_id: str,
    tipo_evento: str = "pago_invitacion",
    payload_hash: str | None = None,
    ventana: str = "2026-Q3",
    payload: dict | None = None
) -> dict[str, Any]:
    """Verifica si un event_id o invitación de concurso ya fue procesada en MongoDB (ENMIENDA 1).

    Regla del concurso: 1 invitación = máximo 1 punto por lead por ventana temporal,
    sin importar cuántas veces se reenvíe el webhook.
    """
    col = db.eventos_procesados

    # 1. Verificar por event_id único
    if event_id and col.find_one({"event_id": event_id}):
        log.info("Webhook ignorado por event_id duplicado: %s", event_id)
        return {"idempotente": True, "puntos_otorgados": 0, "motivo": "event_id_duplicado"}

    # 2. Verificar por payload_hash único
    if payload_hash and col.find_one({"payload_hash": payload_hash}):
        log.info("Webhook ignorado por payload_hash duplicado: %s", payload_hash)
        return {"idempotente": True, "puntos_otorgados": 0, "motivo": "payload_hash_duplicado"}

    # 3. Deduplicación de concurso: 1 punto máx por lead_id + tipo_evento + ventana
    ya_acreditado = col.find_one({
        "lead_id": lead_id,
        "tipo_evento": tipo_evento,
        "ventana": ventana
    })

    puntos = settings.puntos_por_plan if not ya_acreditado else 0

    # Registrar el nuevo evento procesado en MongoDB
    doc = {
        "_id": hashlib.sha256(f"{event_id}_{payload_hash}_{lead_id}".encode()).hexdigest()[:32],
        "event_id": event_id,
        "lead_id": lead_id,
        "tipo_evento": tipo_evento,
        "payload_hash": payload_hash,
        "ventana": ventana,
        "puntos_acreditados": puntos,
        "payload": payload or {},
        "procesado_en": hmac.new(b"now", b"", hashlib.sha256).hexdigest()
    }
    col.insert_one(doc)

    return {
        "idempotente": False,
        "puntos_otorgados": puntos,
        "ya_tenia_puntos_concurso": bool(ya_acreditado)
    }
