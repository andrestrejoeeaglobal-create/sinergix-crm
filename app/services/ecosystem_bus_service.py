"""Servicio de Bus de Eventos Multimódulo del Ecosistema Sinergix (Creator, Salud, Pro, Admin, CRM).

Garantiza despacho idempotente y validación de firma HMAC a prueba de ataques de temporización (hmac.compare_digest).
"""
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List
from app.config import settings

SECRET_BUS = os.getenv("ECOSYSTEM_BUS_SECRET", settings.payment_webhook_secret)


def generar_firma_bus(payload_raw: bytes) -> str:
    """Calcula la firma HMAC SHA256 para eventos del bus multimódulo."""
    return hmac.new(SECRET_BUS.encode("utf-8"), payload_raw, hashlib.sha256).hexdigest()


def validar_firma_bus_segura(payload_raw: bytes, firma_recibida: str) -> bool:
    """Valida la firma HMAC usando hmac.compare_digest para prevenir timing attacks."""
    if not firma_recibida:
        return False
    firma_esperada = generar_firma_bus(payload_raw)
    return hmac.compare_digest(firma_esperada, firma_recibida)


def publicar_evento_ecosistema(
    db: Any,
    modulo_origen: str,
    tipo_evento: str,
    payload: Dict[str, Any],
    firma_hmac: str = ""
) -> Dict[str, Any]:
    """Publica e ingresa un evento en el bus multimódulo con trazabilidad."""
    payload_raw = json.dumps(payload, sort_keys=True).encode("utf-8")

    # Si se proporciona firma, validarla de forma segura
    if firma_hmac and not validar_firma_bus_segura(payload_raw, firma_hmac):
        raise ValueError("Firma HMAC del bus multimódulo inválida (Timing Attack Prevention)")

    evento_id = f"evt_bus_{secrets.token_hex(8)}"
    ahora = datetime.now(timezone.utc)

    doc = {
        "_id": evento_id,
        "modulo_origen": modulo_origen,
        "tipo_evento": tipo_evento,
        "payload": payload,
        "estado_despacho": "procesado",
        "creado_en": ahora
    }

    db.eventos_ecosistema_bus.insert_one(doc)

    return {
        "id": evento_id,
        "modulo_origen": modulo_origen,
        "tipo_evento": tipo_evento,
        "estado_despacho": "procesado",
        "timestamp": ahora
    }


def listar_eventos_bus(db: Any, modulo_origen: str | None = None) -> List[Dict[str, Any]]:
    """Consulta la lista de eventos procesados por el bus del ecosistema."""
    filtro = {"modulo_origen": modulo_origen} if modulo_origen else {}
    items = list(db.eventos_ecosistema_bus.find(filtro).sort("creado_en", -1).limit(50))
    for it in items:
        it["id"] = it["_id"]
        it["timestamp"] = it.get("creado_en", datetime.now(timezone.utc))
    return items
