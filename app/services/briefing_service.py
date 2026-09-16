"""Servicio de Briefing Matutino del Sherpa (8:00 AM) — Live DB / Zero-Data Ready.

Deriva todas las prioridades, tareas y resúmenes conversacionales de la colección `leads` en vivo en MongoDB.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List


def generar_briefing_matutino(db: Any, sherpa_id: str = "admin") -> Dict[str, Any]:
    """Genera el briefing diario a las 8:00 AM para el Sherpa basado 100% en MongoDB en vivo."""
    filtro = {} if sherpa_id == "admin" else {"sherpa_id": sherpa_id}

    ahora = datetime.now(timezone.utc)
    fecha_str = ahora.strftime("%Y-%m-%d")

    sherpa_doc = db.sherpas.find_one({"_id": "s1"}) if sherpa_id == "admin" else db.sherpas.find_one({"_id": sherpa_id})
    sherpa_nombre = sherpa_doc.get("nombre", "Sherpa") if sherpa_doc else "Sherpa Admin"

    # 1. Consultar leads reales en MongoDB
    leads_sin_encuesta = list(db.leads.find({**filtro, "respondio": False, "is_cancelled": {"$ne": True}}))
    leads_adherencia_baja = list(db.leads.find({**filtro, "adherencia_acumulada": {"$lt": 80.0, "$gt": 0.0}, "is_cancelled": {"$ne": True}}))
    leads_por_vencer = list(db.leads.find({**filtro, "dia_actual_sprint": {"$gte": 25}, "is_cancelled": {"$ne": True}}))

    acciones_prioritarias: List[Dict[str, Any]] = []

    # Acciones prioritarias derivadas de datos reales
    for lead in leads_adherencia_baja:
        acciones_prioritarias.append({
            "tipo": "critico",
            "lead_id": lead["_id"],
            "nombre": lead.get("nombre", "Contacto"),
            "mensaje": f"Adherencia crítica ({lead.get('adherencia_acumulada', 0)}%). Requiere llamada de contención urgente.",
            "boton_label": "Llamar por WhatsApp",
            "accion": "contactar"
        })

    for lead in leads_sin_encuesta[:3]:
        acciones_prioritarias.append({
            "tipo": "seguimiento",
            "lead_id": lead["_id"],
            "nombre": lead.get("nombre", "Contacto"),
            "mensaje": "Pendiente de primer contacto / encuesta de perfilado.",
            "boton_label": "Enviar Mensaje",
            "accion": "enviar_encuesta"
        })

    # Resumen conversacional
    total_pendientes = len(leads_sin_encuesta)
    total_criticos = len(leads_adherencia_baja)
    total_por_vencer = len(leads_por_vencer)

    if total_pendientes == 0 and total_criticos == 0 and total_por_vencer == 0:
        resumen_texto = (
            f"¡Buenos días, {sherpa_nombre}! ☀️\n\n"
            "No tienes seguimientos ni tareas pendientes para hoy. Tu base de datos está limpia y lista para la captura de leads."
        )
    else:
        resumen_texto = (
            f"¡Buenos días, {sherpa_nombre}! ☀️\n\n"
            f"Hoy tienes {total_pendientes} prospecto(s) sin encuesta y {total_criticos} cliente(s) en semáforo crítico (<80% adherencia). "
            f"Adicionalmente, {total_por_vencer} cliente(s) están próximos a cerrar su ciclo de 28 días."
        )

    return {
        "sherpa_id": sherpa_id,
        "sherpa_nombre": sherpa_nombre,
        "fecha": fecha_str,
        "resumen_texto": resumen_texto,
        "contactos_seguimiento": total_pendientes,
        "sprints_por_vencer": total_por_vencer,
        "lideres_emergentes": 0,
        "acciones_prioritarias": acciones_prioritarias
    }
