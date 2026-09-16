"""Modelos y utilidades de estructuras para MongoDB en servidor propio (ENMIENDAS 1 a 8 + Plan v6)."""
import uuid
from datetime import datetime, timezone
from typing import Any


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


def crear_lead_doc(
    sherpa_id: str,
    nombre: str,
    telefono: str,
    email: str = "",
    canal_captacion: str = "landing",
    consentimiento_whatsapp: bool = True,
    mecanismo_captura: str = "formulario_web",
    **extra: Any
) -> dict[str, Any]:
    """Crea un documento de lead para MongoDB conforme a la Enmienda 3 y Plan v6."""
    ahora = _now()
    doc = {
        "_id": _uuid(),
        "sherpa_id": sherpa_id,
        "nombre": nombre,
        "apellido1": extra.get("apellido1", ""),
        "apellido2": extra.get("apellido2", ""),
        "telefono": telefono,
        "email": email,

        # Consentimiento WhatsApp (ENMIENDA 3 - Requisito Meta)
        "consentimiento_whatsapp": consentimiento_whatsapp,
        "fecha_consentimiento": ahora if consentimiento_whatsapp else None,
        "mecanismo_captura": mecanismo_captura,
        "optin_whatsapp": consentimiento_whatsapp,
        "optin_fecha": ahora if consentimiento_whatsapp else None,
        "optin_origen": mecanismo_captura,

        # Seguimiento de Agenda & Encuesta (Plan v6)
        "respondio": extra.get("respondio", False),
        "is_cancelled": extra.get("is_cancelled", False),
        "referidor_nombre": extra.get("referidor_nombre", "Daniel Osorio"),
        "referidor_link": extra.get("referidor_link"),

        # Dirección de envío
        "calle": extra.get("calle", ""),
        "numero_exterior": extra.get("numero_exterior", ""),
        "numero_interior": extra.get("numero_interior"),
        "colonia": extra.get("colonia", ""),
        "codigo_postal": extra.get("codigo_postal", ""),
        "ciudad_municipio": extra.get("ciudad_municipio", ""),
        "estado": extra.get("estado", ""),
        "pais": extra.get("pais", "México"),

        # Red binaria
        "distribuidor_patrocinador_id": extra.get("distribuidor_patrocinador_id", ""),
        "posicion_red": extra.get("posicion_red"),

        # Origen
        "canal_captacion": canal_captacion,
        "utm_source": extra.get("utm_source"),
        "utm_medium": extra.get("utm_medium"),
        "utm_campaign": extra.get("utm_campaign"),
        "landing_id": extra.get("landing_id"),

        # Bio-Auditoría
        "bioauditoria_fecha": None,
        "bioauditoria_resultados": None,

        # Pipeline
        "etapa_pipeline": extra.get("etapa_pipeline", "Lead"),
        "link_pago_activo_id": None,

        # Sprint 28 (ENMIENDA 5)
        "sprint_inicio": None,
        "sprint_reconstrucciones": 0,
        "hrv_baseline": None,
        "adherencia_acumulada": 0.0,
        "fase_actual": None,
        "dia_actual_sprint": 0,
        "ultima_sincronizacion_biometrica": None,

        # Gamificación
        "puntos_adquiridos": 0,
        "estado_bono_activo": None,
        "ciclos_renovados": 0,

        # Clasificación Los Cuatro Cincos
        "clasificacion": extra.get("clasificacion"),

        # Auditoría (Ajuste Técnico 3)
        "creado_en": ahora,
        "actualizado_en": ahora,
        "modificado_por": extra.get("modificado_por", sherpa_id),
    }
    return doc


def crear_sherpa_doc(
    google_sub: str,
    email: str,
    nombre: str,
    api_token: str | None = None,
    rol: str = "sherpa"
) -> dict[str, Any]:
    """Crea un documento de Sherpa con rol para aislamiento (ENMIENDA 4)."""
    ahora = _now()
    return {
        "_id": _uuid(),
        "google_sub": google_sub,
        "email": email,
        "nombre": nombre,
        "rol": rol,  # sherpa / admin / operador
        "api_token": api_token or _uuid(),
        "google_refresh_token": None,
        "google_access_token": None,
        "numero_distribuidor": None,
        "creado_en": ahora,
        "actualizado_en": ahora,
    }


def crear_evento_procesado_doc(
    event_id: str,
    lead_id: str,
    tipo_evento: str,
    payload_hash: str | None = None,
    ventana: str = "2026-Q3",
    payload: dict | None = None
) -> dict[str, Any]:
    """Crea documento de evento procesado para idempotencia y deduplicación de concurso (ENMIENDA 1)."""
    return {
        "_id": _uuid(),
        "event_id": event_id,
        "lead_id": lead_id,
        "tipo_evento": tipo_evento,
        "payload_hash": payload_hash,
        "ventana": ventana,
        "payload": payload or {},
        "procesado_en": _now(),
    }
