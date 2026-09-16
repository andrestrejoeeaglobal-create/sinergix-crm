"""Servicio de Dead Letter Queue (DLQ) y Resiliencia en MongoDB (Fase 3).

Registra fallos de integración externadas (webhooks, Telegram, APIs externas) en `tareas_fallidas_dlq`
y gestiona reintentos exponenciales (exponential backoff).
"""
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List

log = logging.getLogger("sinergix.dlq")


def registrar_tarea_fallida(
    db: Any,
    tipo_tarea: str,
    payload: Dict[str, Any],
    error_msg: str,
    intento: int = 1,
    max_intentos: int = 3
) -> str:
    """Registra una tarea fallida en la cola de mensajes muertos (DLQ)."""
    dlq_id = f"dlq_{secrets.token_hex(8)}"
    now = datetime.now(timezone.utc)

    doc = {
        "_id": dlq_id,
        "tipo_tarea": tipo_tarea,
        "payload": payload,
        "error_msg": error_msg,
        "intento_actual": intento,
        "max_intentos": max_intentos,
        "estado": "pendiente_reintento" if intento < max_intentos else "exhausto",
        "creado_en": now,
        "actualizado_en": now,
    }

    try:
        db.tareas_fallidas_dlq.insert_one(doc)
        log.warning("Tarea fallida registrada en DLQ ID=%s (Tipo=%s, Error=%s)", dlq_id, tipo_tarea, error_msg)
    except Exception as exc:
        log.error("Error al registrar en DLQ: %s", exc)

    return dlq_id


def obtener_tareas_dlq_pendientes(db: Any) -> List[Dict[str, Any]]:
    """Obtiene la lista de tareas en la DLQ pendientes de reintento."""
    try:
        return list(db.tareas_fallidas_dlq.find({"estado": "pendiente_reintento"}))
    except Exception:
        return []
