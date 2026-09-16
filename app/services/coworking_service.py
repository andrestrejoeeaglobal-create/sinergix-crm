"""Servicio de Agendamiento de Bio-Auditorías Presenciales & Sedes de Coworking.

Maneja reservas en centros físicos (Coworking Norte) y cálculo de tarifas de envío regional ($95 MXN a GDL).
"""
import secrets
from datetime import datetime, timezone
from typing import Any, Dict


def reservar_bio_auditoria(
    db: Any,
    lead_id: str,
    coworking_sede: str = "Coworking Norte",
    fecha_hora: datetime | None = None,
    incluye_envio_gdl: bool = False
) -> Dict[str, Any]:
    """Registra una cita presencial de Bio-Auditoría en Coworking Norte."""
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        raise ValueError(f"Lead con ID {lead_id} no encontrado")

    reserva_id = f"aud_{secrets.token_hex(6)}"
    costo_flete = 95.0 if incluye_envio_gdl else 0.0
    ahora = datetime.now(timezone.utc)

    doc = {
        "_id": reserva_id,
        "lead_id": lead_id,
        "coworking_sede": coworking_sede,
        "fecha_hora": fecha_hora or ahora,
        "costo_flete": costo_flete,
        "estado": "confirmada",
        "creado_en": ahora
    }

    db.bio_auditorias.insert_one(doc)

    db.leads.update_one(
        {"_id": lead_id},
        {
            "$set": {
                "cita_bio_auditoria_id": reserva_id,
                "etapa_pipeline": "Bio-Auditoría Agendada",
                "actualizado_en": ahora
            }
        }
    )

    msg = f"Cita de Bio-Auditoría confirmada en {coworking_sede} para {lead.get('nombre')}."
    if incluye_envio_gdl:
        msg += f" Incluye flete especial GDL ($95 MXN)."

    return {
        "id": reserva_id,
        "lead_id": lead_id,
        "coworking_sede": coworking_sede,
        "fecha_hora": fecha_hora or ahora,
        "costo_flete": costo_flete,
        "estado": "confirmada",
        "mensaje_confirmacion": msg
    }
