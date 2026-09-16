"""Módulo de Despacho de Webhooks & Notificaciones Asíncronas (Fase 3).

Maneja la ejecución en segundo plano para mantener tiempos de respuesta de endpoints receptores
por debajo de los 200 ms y despacha notificaciones a Telegram.
"""
import logging
from typing import Any, Dict
from ..integrations import telegram
from .dlq_service import registrar_tarea_fallida

log = logging.getLogger("sinergix.dispatcher")


def despachar_alerta_telegram_background(
    chat_id: str | int,
    mensaje: str,
    db: Any = None,
    payload_contexto: Dict[str, Any] | None = None
) -> None:
    """Función de background worker para enviar mensajes a Telegram sin bloquear el request de la API."""
    try:
        res = telegram.enviar_mensaje_telegram(chat_id, mensaje)
        log.info("Notificación Telegram enviada exitosamente a ChatID=%s: %s", chat_id, res)
    except Exception as exc:
        log.error("Fallo al enviar notificación a Telegram: %s", exc)
        if db is not None:
            registrar_tarea_fallida(
                db=db,
                tipo_tarea="notificacion_telegram",
                payload={"chat_id": chat_id, "mensaje": mensaje, "contexto": payload_contexto or {}},
                error_msg=str(exc)
            )


def procesar_webhook_pago_background(
    db: Any,
    lead_id: str,
    monto: float | int | None,
    tipo: str
) -> None:
    """Procesamiento asíncrono secundario post-confirmación de pago."""
    try:
        log.info("Procesando tareas secundarias de pago para Lead=%s (Tipo=%s)", lead_id, tipo)
        lead = db.leads.find_one({"_id": lead_id})
        if lead and lead.get("referidor_nombre"):
            # Enviar alerta de pago al patrocinador/admin
            msg = f"🎉 ¡Pago Confirmado! {lead['nombre']} ha iniciado su Sprint 28 ({tipo})."
            despachar_alerta_telegram_background("123456789", msg, db=db, payload_contexto={"lead_id": lead_id})
    except Exception as exc:
        log.error("Error en worker de pago background: %s", exc)
        registrar_tarea_fallida(db, "procesar_webhook_pago", {"lead_id": lead_id, "tipo": tipo}, str(exc))
