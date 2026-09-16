"""Servicio de Cron Nocturno y Mantenimiento de Leads (Fase 3).

Maneja el incremento de días del Sprint 28, la detección de inactividad de 72 horas en prospectos
sin encuesta y la deshabilitación o reactivación de estados.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from ..config import settings
from ..salesbot import bloquear_y_alertar, enviar_plantilla
from ..sprint import procesar_noche

log = logging.getLogger("sinergix.cron")


def ejecutar_cron_nocturno(db: Any, x_cron_token: str = "") -> Dict[str, Any]:
    """Ejecuta el proceso nocturno desatendido.
    
    1. Revalida el token X-Cron-Token.
    2. Recalibra los leads en Sprint Activo (dia_actual_sprint + 1).
    3. Detecta leads en estado 'Lead' o 'Sin Encuesta' con > 72h sin respuesta y marca `candidato_reactivacion: True`.
    """
    if settings.cron_token and x_cron_token != settings.cron_token:
        raise PermissionError("Token de cron nocturno inválido o no provisto")

    ahora = datetime.now(timezone.utc)
    hace_72h = ahora - timedelta(hours=72)

    # 1. Recalibración Sprint 28 Activos
    activos = list(db.leads.find({"etapa_pipeline": "Sprint Activo"}))
    eventos_sprint = []

    for lead in activos:
        inicio = lead.get("sprint_inicio")
        if not inicio:
            continue
        if isinstance(inicio, str):
            inicio = datetime.fromisoformat(inicio)
        if inicio.tzinfo is None:
            inicio = inicio.replace(tzinfo=timezone.utc)

        dias_calendario = (ahora - inicio).days + 1
        estado = procesar_noche(dias_calendario, lead.get("sprint_reconstrucciones", 0), {})

        updates = {
            "dia_actual_sprint": dias_calendario,
            "fase_actual": estado.fase,
            "actualizado_en": ahora,
        }

        if estado.es_renovacion_pendiente or dias_calendario >= 28:
            updates["etapa_pipeline"] = "Renovación pendiente"
            bloquear_y_alertar(db, lead, "Sprint 28 completado: Renovación pendiente", dia=28)
            eventos_sprint.append({"lead_id": lead["_id"], "evento": "renovacion_pendiente"})

        db.leads.update_one({"_id": lead["_id"]}, {"$set": updates})

    # 2. Detección de Inactividad de 72h en Prospectos Sin Encuesta
    inactivos_query = {
        "respondio": {"$ne": True},
        "is_cancelled": {"$ne": True},
        "etapa_pipeline": {"$in": ["Lead", "Bio-Auditoría"]},
    }
    prospectos = list(db.leads.find(inactivos_query))
    reactivaciones = 0

    for lead in prospectos:
        creado = lead.get("creado_en")
        if not creado:
            continue
        if isinstance(creado, str):
            creado = datetime.fromisoformat(creado)
        if creado.tzinfo is None:
            creado = creado.replace(tzinfo=timezone.utc)

        if creado <= hace_72h and not lead.get("candidato_reactivacion"):
            db.leads.update_one(
                {"_id": lead["_id"]},
                {
                    "$set": {
                        "candidato_reactivacion": True,
                        "alerta_inactividad": True,
                        "fecha_alerta_inactividad": ahora,
                        "actualizado_en": ahora,
                    }
                }
            )
            reactivaciones += 1
            log.info("Lead %s marcado como candidato a reactivación (inactivo > 72h).", lead["_id"])

    return {
        "status": "ok",
        "procesados": len(activos),
        "procesados_sprint": len(activos),
        "eventos": eventos_sprint,
        "eventos_sprint": eventos_sprint,
        "candidatos_reactivacion_72h": reactivaciones,
        "timestamp": ahora.isoformat(),
    }
