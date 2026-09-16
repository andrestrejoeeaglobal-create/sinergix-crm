"""Salesbot — orquesta plantillas + SafetyEngine + Chatwoot (Sprint 28 y EcoSinergix).

Toda plantilla pasa por SafetyEngine ANTES de salir (regla dura de compliance).
Regla dura de Meta (ENMIENDA 3): NINGÚN mensaje sale si `consentimiento_whatsapp = False`.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from .integrations.chatwoot import client as chatwoot
from .safety import validate

TEMPLATES = {
    "SPR_01": (
        "¡{nombre}, bienvenido al Sprint 28! Hoy comienzan 28 días. Tu protocolo: "
        "MultiSinergix en ayunas y AminoSinergix antes de dormir. Usa tu EcoSinergix "
        "24/7 y registra tus comidas con foto. ¿Todo listo?"
    ),
    "SPR_02": (
        "{nombre}, completaste la Semana 1 — tu cuerpo ya pasó el Reset Metabólico. "
        "Tus números: HRV {hrv_actual} ms, adherencia {adherencia}%. Agendemos tu "
        "consulta de la Semana 2, ¿te sirve {fecha_sugerida}?"
    ),
    "SPR_03": (
        "{nombre}, mitad del Sprint 28. Comparativa real Día 1 → Día 14: HRV {hrv_delta} ms, "
        "FC en reposo {fc_delta} lpm, sueño profundo {sueno_delta} h. Nada de opiniones: "
        "biometría. Recuerda tu AminoSinergix nocturno."
    ),
    "SPR_04": (
        "{nombre}, última semana: fase de Ingeniería Tisular. Mientras duermes, el "
        "AminoSinergix apoya la reparación de tus tejidos. ¿Has notado cambios en tu "
        "energía o digestión esta semana?"
    ),
    "SPR_05": (
        "{nombre}, últimos 3 días del Sprint 28. Tu Re-Auditoría presencial es el {fecha_dia28}: "
        "composición corporal, fuerza y comparativa completa. ¿Confirmamos? Después "
        "renovamos tu ciclo para seguir sumando."
    ),
    "DIA_28": (
        "¡Felicidades {nombre}, completaste los 28 días! Tus resultados de la Re-Auditoría "
        "ya están en tu app. Tu estado es Renovación pendiente. ¿Renovamos tu siguiente ciclo? {link_renovacion}"
    ),
    "CIE_03": (
        "¡{nombre}! ¿Cómo sigues? Muchos notan que al pausar el AminoSinergix el sueño "
        "profundo baja en 2-3 semanas. Si quieres retomar, tengo algo para clientes que "
        "regresan. ¿Te interesa? {link_renovacion}"
    ),
    "SYNC_RECORDATORIO": (
        "{nombre}, recordatorio amable: sincroniza tu EcoSinergix hoy para que tus "
        "métricas del Sprint 28 sigan al día. Tu ritmo, tus decisiones."
    ),
    "LINK_PAGO": (
        "¡{nombre}! Aquí está tu enlace de pago personalizado: {link}. Tus datos ya "
        "vienen listos — solo confirma y paga con tarjeta."
    ),
}


def enviar_plantilla(
    db: Any, lead: dict[str, Any], plantilla: str, variables: dict | None = None, dia: int = 0
) -> dict:
    """Valida opt-in Meta, aplica SafetyEngine y envía. Devuelve el resultado y registra el evento."""
    # ENMIENDA 3: Verificación obligatoria de Opt-In WhatsApp conforme a reglas Meta
    tiene_consentimiento = lead.get("consentimiento_whatsapp") or lead.get("optin_whatsapp", False)
    if not tiene_consentimiento:
        raise ValueError(f"Mensaje bloqueado: El lead '{lead.get('nombre')}' ({lead.get('telefono')}) NO tiene consentimiento explícito de WhatsApp.")

    texto_base = TEMPLATES.get(plantilla, "¡Hola {nombre}!")
    texto = texto_base.format(**{**{"nombre": lead.get("nombre", "")}, **(variables or {})})
    chequeo = validate(texto)
    texto_final = chequeo["texto_seguro"]

    resultado_envio = chatwoot.send_text(lead.get("telefono", ""), texto_final, plantilla=plantilla)

    evento = {
        "_id": uuid.uuid4().hex,
        "lead_id": lead.get("_id") or lead.get("id"),
        "dia": dia,
        "tipo_evento": "mensaje",
        "plantilla": plantilla,
        "payload": {
            "variables": variables or {},
            "safety_ok": chequeo["ok"],
            "hallazgos": chequeo["hallazgos"],
            "modo": resultado_envio.get("modo", "mock"),
        },
        "atendido_por_sherpa": False,
        "creado_en": datetime.now(timezone.utc),
    }
    if hasattr(db, "eventos_sprint"):
        db.eventos_sprint.insert_one(evento)

    return {"ok": True, "safety": chequeo, "envio": resultado_envio}


def bloquear_y_alertar(db: Any, lead: dict[str, Any], motivo: str, dia: int) -> None:
    """Registra alerta crítica con SLA de llamada del Sherpa (p. ej. Día 7 / Día 25)."""
    evento = {
        "_id": uuid.uuid4().hex,
        "lead_id": lead.get("_id") or lead.get("id"),
        "dia": dia,
        "tipo_evento": "alerta",
        "payload": {"motivo": motivo, "sla": "llamada_directa"},
        "atendido_por_sherpa": False,
        "creado_en": datetime.now(timezone.utc),
    }
    if hasattr(db, "eventos_sprint"):
        db.eventos_sprint.insert_one(evento)
