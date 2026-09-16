"""Motor del Asistente T.I.L.O. — Calificación y Respuesta Determinista.

Gobernanza y Reglas de Respuesta:
1. Trato formal estricto en segunda persona («Usted», «Su», «Le»). Prohibido el tuteo.
2. Unidimensionalidad estricta: Una sola indicación o pregunta por intervención.
3. Cero redundancia: Omisión de preguntas sobre nombre, celular u objetivo si ya vienen en la ficha.
4. Matriz de Bifurcación Determinista:
   - Ruta A (Salud / Metabolismo): Validar recepción, cuestionar resignación a la fatiga/deterioro cotidiano. Solicitar principal obstáculo diario.
   - Ruta B (Negocio / Sherpa): Validar postulación, reforzar visión de causa y método profesional. Solicitar plaza/ciudad base de operación.
5. Estructura Obligatoria de Salida (2 Párrafos de Poder):
   - Bloque 1 (Validación y Autoridad): Cero preguntas.
   - Bloque 2 (Avance e Instrucción): Pregunta unívoca de avance. Separados por doble salto de línea `\\n\\n`.
"""
from typing import Dict, Any


PROMPT_SISTEMA_TILO = """Usted es T.I.L.O., el Asistente Clínico y de Enlace Estratégico de Equipo en Acción®.
Su función es calificar prospectos y guiar su avance sin redundancias ni tuteo.

REGLAS DE GOBERNANZA:
1. Trato de usted: Diríjase siempre en segunda persona formal («Usted», «Su», «Le»).
2. Estructura de 2 Párrafos de Poder:
   - Párrafo 1: Validación, contexto y autoridad. Queda estrictamente prohibido incluir preguntas en este primer párrafo.
   - Párrafo 2: Instrucción precisa que concluye siempre con una sola pregunta directa de avance.
   - Los dos párrafos deben estar separados exactamente por un doble salto de línea.
3. Bifurcación:
   - Si el objetivo es de Salud/Metabolismo: Valide la recepción, cuestione la fatiga como algo cotidiano y pregunte por el principal obstáculo diario (caída de energía por la tarde, calidad de descanso o digestión).
   - Si el objetivo es de Negocio/Sherpa: Valide la postulación, refuerce la visión de causa y método profesional, y pregunte por la plaza, ciudad o municipio base desde donde operará.
"""


def procesar_respuesta_tilo(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Genera la respuesta calibrada del Asistente T.I.L.O. basada en la ficha del lead."""
    nombre = (lead.get("nombre") or "").strip()
    primer_nombre = nombre.split()[0] if nombre else "Estimado prospecto"
    objetivo = (lead.get("objetivo") or lead.get("objetivo_principal") or "").strip()
    objetivo_lower = objetivo.lower()

    es_ruta_b = (
        "sherpa" in objetivo_lower or 
        "ingresos" in objetivo_lower or 
        "negocio" in objetivo_lower or 
        lead.get("clasificacion") in ["capacidad", "influencia"]
    )

    if es_ruta_b:
        ruta = "Ruta B - Negocio / Sherpa"
        etiqueta = "Aspirante a Sherpa"
        bloque1 = (
            f"Buenas tardes, {primer_nombre}. Confirmamos la recepción de su postulación para integrarse "
            f"como Sherpa en Equipo en Acción®. Nuestra estructura opera bajo un método profesional de liderazgo, "
            f"formación clínica continua y desarrollo de ingresos residuales en equipo."
        )
        bloque2 = (
            f"Para validar la disponibilidad de cupos en la cordada y coordinar la gira de campo, "
            f"¿desde qué plaza, ciudad o municipio base tiene usted proyectado operar?"
        )
    else:
        ruta = "Ruta A - Salud / Metabolismo"
        etiqueta = "Cliente Potencial"
        bloque1 = (
            f"Buenas tardes, {primer_nombre}. Hemos recibido su registro para el diagnóstico de salud "
            f"y rendimiento biológico de Equipo en Acción®. Es fundamental comprender que la fatiga, "
            f"el cansancio vespertino o el deterioro metabólico no son normales ni deben asumirse como inevitables."
        )
        bloque2 = (
            f"Para enfocar correctamente su bio-auditoría inicial, ¿cuál considera usted que es su principal "
            f"obstáculo cotidiano: la caída de energía por la tarde, la calidad de su descanso o la digestión pesada?"
        )

    respuesta_texto = f"{bloque1}\n\n{bloque2}"

    return {
        "ok": True,
        "ruta": ruta,
        "etiqueta": etiqueta,
        "respuesta": respuesta_texto,
        "bloque1": bloque1,
        "bloque2": bloque2,
        "parrafos_count": len(respuesta_texto.split("\n\n")),
        "tiene_tuteo": any(w in respuesta_texto.lower() for w in [" tú ", " te ", " tu ", "tienes", "puedes", "quieres"]),
        "trato_formal": any(w in respuesta_texto.lower() for w in ["usted", "su ", "le "])
    }
