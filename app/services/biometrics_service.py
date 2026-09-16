"""Servicio de Ingesta de Telemetría Biométrica IoT (Banda H7).

Registra series temporales de HRV (ms), Frecuencia Cardíaca (lpm), Temperatura Basal y Sueño.
"""
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List


def registrar_telemetria_h7(
    db: Any,
    lead_id: str,
    hrv_ms: int,
    frecuencia_cardiaca_lpm: int,
    temperatura_basal_delta: float,
    minutos_sueno: int,
    calidad_sueno_porcentaje: float,
    dispositivo_id: str = "H7_BAND_DEFAULT"
) -> Dict[str, Any]:
    """Ingresa un registro de telemetría biométrica de la Banda H7."""
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        raise ValueError(f"Lead {lead_id} no encontrado")

    record_id = f"bio_{secrets.token_hex(8)}"
    ahora = datetime.now(timezone.utc)

    sueno_doc = {
        "minutos_totales": minutos_sueno,
        "calidad_porcentaje": calidad_sueno_porcentaje,
        "profundo_min": int(minutos_sueno * 0.25),
        "rem_min": int(minutos_sueno * 0.20),
        "ligero_min": int(minutos_sueno * 0.55)
    }

    doc = {
        "_id": record_id,
        "lead_id": lead_id,
        "timestamp": ahora,
        "hrv_ms": hrv_ms,
        "frecuencia_cardiaca_lpm": frecuencia_cardiaca_lpm,
        "temperatura_basal_delta": temperatura_basal_delta,
        "sueno": sueno_doc,
        "dispositivo_id": dispositivo_id,
        "creado_en": ahora
    }

    db.telemetria_biometrica.insert_one(doc)

    # Actualizar última sincronización en el lead
    db.leads.update_one(
        {"_id": lead_id},
        {"$set": {"ultima_sincronizacion_biometrica": ahora, "actualizado_en": ahora}}
    )

    return {
        "id": record_id,
        "lead_id": lead_id,
        "timestamp": ahora,
        "hrv_ms": hrv_ms,
        "frecuencia_cardiaca_lpm": frecuencia_cardiaca_lpm,
        "temperatura_basal_delta": temperatura_basal_delta,
        "sueno": sueno_doc,
        "dispositivo_id": dispositivo_id
    }


def obtener_historico_biometrico(db: Any, lead_id: str) -> List[Dict[str, Any]]:
    """Obtiene el historial cronológico de biometría H7 para un lead."""
    items = list(db.telemetria_biometrica.find({"lead_id": lead_id}).sort("timestamp", -1))
    for it in items:
        it["id"] = it["_id"]
    return items
