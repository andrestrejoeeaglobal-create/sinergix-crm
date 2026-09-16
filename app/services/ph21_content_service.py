"""Servicio de Despacho de Contenidos Educativos Especializados del Sprint PH21.

Maneja los contenidos formativos para hitos clave:
  - Día 1: Guía Rápida de Reset Metabólico.
  - Día 21: Módulo de Autofagia y Sellado Tisular.
"""
from datetime import datetime, timezone
from typing import Any, Dict

CONTENIDOS_PH21 = {
    1: {
        "titulo": "Guía Rápida de Reset Metabólico (Día 1)",
        "descripcion": "Bienvenido al Sprint PH21. Inicia tu protocolo con la guía rápida de nutrición celular.",
        "link_material": "https://sinergix.mx/ph21/reset-metabolico-dia1.pdf"
    },
    21: {
        "titulo": "Módulo de Autofagia y Sellado Tisular (Día 21)",
        "descripcion": "Semana 3: Activa los mecanismos profundos de autofagia celular y nutrición protectora.",
        "link_material": "https://sinergix.mx/ph21/autofagia-sellado-dia21.pdf"
    }
}


def despachar_contenido_ph21(db: Any, lead_id: str, dia_hito: int) -> Dict[str, Any]:
    """Envía el contenido educativo correspondiente al hito del Sprint PH21."""
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        raise ValueError(f"Lead {lead_id} no encontrado")

    contenido = CONTENIDOS_PH21.get(dia_hito)
    if not contenido:
        contenido = {
            "titulo": f"Material de Seguimiento Sprint PH21 (Día {dia_hito})",
            "descripcion": f"Contenido educativo de apoyo para la fase del Día {dia_hito}.",
            "link_material": f"https://sinergix.mx/ph21/modulo-dia{dia_hito}.pdf"
        }

    ahora = datetime.now(timezone.utc)
    registro = {
        "lead_id": lead_id,
        "dia_hito": dia_hito,
        "titulo": contenido["titulo"],
        "fecha_despacho": ahora
    }

    db.envios_educativos.insert_one(registro)

    db.leads.update_one(
        {"_id": lead_id},
        {"$set": {"ultimo_contenido_enviado": contenido["titulo"], "actualizado_en": ahora}}
    )

    return {
        "ok": True,
        "lead_id": lead_id,
        "dia_hito": dia_hito,
        "contenido": contenido,
        "mensaje": f"Contenido enviado exitosamente a {lead.get('nombre')}: {contenido['titulo']}"
    }
