"""Motor del Asistente T.I.L.O. — Calificación y Enrutamiento Determinista de Cordada.

Alineación Operativa con captura.html y Gobernanza Normativa (NOM-008-SSA3-2017, NOM-004-SSA3-2012, LFPDPPP):
1. Misión Principal: Concierge de Enlace, Confirmación de Plaza y Bienvenida a la Cordada para la
   CONVOCATORIA NACIONAL 2026 | LA NUEVA ERA DE EQUIPO EN ACCIÓN®.
2. Prohibición de Triaje Hospitalario: Prohibido realizar interrogatorios clínicos, preguntas de alergias,
   patologías, edades o expedientes médicos (cumplimiento NOM-008 y NOM-004).
3. Trato Formal Estricto: Tratamiento en segunda persona formal («Usted», «Su», «Le»). Prohibido el tuteo.
4. Cero Redundancia: No solicitar datos ya capturados en la landing (Nombre, WhatsApp, Sede, Propósito).
5. Matriz de Enrutamiento Determinista (3 Rutas):
   - Ruta 1 (Aspirante a Sherpa): Liderazgo, incentivo $10,000 MXN y despliegue en sede.
   - Ruta 2 (Transmisión Virtual 16 Sep): Reserva de acceso digital y recordatorio.
   - Ruta 3 (Salud y Rendimiento Familiar): Orientación de prevención y vitalidad biológica.
6. Estructura Obligatoria de Salida (2 Párrafos de Poder):
   - Párrafo 1 (Bienvenida, Causa y Contexto): Cero preguntas.
   - Párrafo 2 (Confirmación e Instrucción): Concluye siempre con una sola pregunta unívoca de avance.
   - Párrafos separados exactamente por doble salto de línea `\n\n`.
"""
from typing import Dict, Any


PROMPT_SISTEMA_TILO = """Usted es T.I.L.O., el Concierge de Enlace y Confirmación de Cordada de Equipo en Acción®.
Su función es validar el registro oficial a la Convocatoria Nacional 2026 ("La Nueva Era") y enrutar a los participantes según su propósito sin tuteo ni interrogatorios clínicos.

REGLAS DE GOBERNANZA:
1. Trato de usted: Diríjase siempre en segunda persona formal («Usted», «Su», «Le»).
2. Estructura de 2 Párrafos de Poder:
   - Párrafo 1: Bienvenida, validación de registro, causa y autoridad. Queda estrictamente prohibido incluir preguntas en este primer párrafo.
   - Párrafo 2: Confirmación operativa que concluye siempre con una sola pregunta directa de avance.
   - Los dos párrafos deben estar separados exactamente por un doble salto de línea `\\n\\n`.
3. Cero Triaje Clínico: Queda prohibido solicitar antecedentes médicos, alergias o diagnósticos. La misión es la conversión y asignación de cordada.
4. Matriz de Enrutamiento por Propósito:
   - Aspirante a Sherpa: Valide la postulación de liderazgo para apertura de plaza (Premio $10,000 MXN), confirme la sede seleccionada y solicite confirmación de disponibilidad para la alineación previa.
   - Transmisión Virtual (16 sep): Valide la reserva para el banderazo digital del 16 de septiembre (8:00 PM) y pregunte si desea recibir el enlace de acceso directo en su WhatsApp 15 minutos antes.
   - Salud Preventiva Familiar: Valide la solicitud de orientación en modulación metabólica y vitalidad biológica, y pregunte cuál es el pilar prioritario a optimizar en su hogar.
"""


def procesar_respuesta_tilo(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Genera la respuesta calibrada del Asistente T.I.L.O. basada en la ficha del lead en captura.html."""
    nombre = (lead.get("nombre") or "").strip()
    primer_nombre = nombre.split()[0] if nombre else "Estimado participante"
    
    proposito = (
        lead.get("proposito") or 
        lead.get("objetivo") or 
        lead.get("objetivo_principal") or 
        ""
    ).strip()
    proposito_lower = proposito.lower()
    
    sede = (lead.get("sede") or lead.get("ciudad") or "").strip()
    clasificacion = lead.get("clasificacion")

    es_sherpa = (
        "sherpa" in proposito_lower or 
        "10k" in proposito_lower or 
        "ingresos" in proposito_lower or 
        "negocio" in proposito_lower or 
        clasificacion in ["capacidad", "influencia"]
    )
    
    es_transmision = (
        "transmisión" in proposito_lower or 
        "transmision" in proposito_lower or 
        "16" in proposito_lower or 
        "virtual" in proposito_lower
    )

    if es_sherpa:
        ruta = "Ruta 1 - Aspirante a Sherpa"
        etiqueta = "Aspirante a Sherpa"
        sede_txt = f" en la sede {sede}" if sede else ""
        bloque1 = (
            f"Buenas tardes, {primer_nombre}. Confirmamos la recepción de su registro como Aspirante a Sherpa "
            f"para el despliegue de La Nueva Era de Equipo en Acción®. Reconocemos su liderazgo para abrir brecha "
            f"{sede_txt} e impulsarla con nuestra causa: «No venimos solo a vender; venimos a cambiar la salud de la gente que amamos»."
        )
        bloque2 = (
            f"Para coordinar la logística de la gira nacional y la bolsa de reconocimiento de $10,000 MXN, "
            f"¿cuenta usted con disponibilidad para participar en la sesión de alineación previa al despliegue?"
        )
    elif es_transmision:
        ruta = "Ruta 2 - Transmisión Virtual 16 Sep"
        etiqueta = "Asistente Transmisión Virtual"
        bloque1 = (
            f"Buenas tardes, {primer_nombre}. Le damos la más cordial bienvenida al registro oficial de la Transmisión "
            f"Especial de La Nueva Era, programada para este miércoles 16 de septiembre. Su lugar en la cordada digital "
            f"ha quedado debidamente apartado para conectarse al banderazo nacional."
        )
        bloque2 = (
            f"Con el fin de garantizar su acceso puntual a las 8:00 PM, ¿desea usted que le enviemos el enlace directo "
            f"de la sala virtual a su WhatsApp 15 minutos antes de iniciar?"
        )
    else:
        ruta = "Ruta 3 - Salud y Rendimiento Familiar"
        etiqueta = "Cliente Potencial - Salud Preventiva"
        bloque1 = (
            f"Buenas tardes, {primer_nombre}. Confirmamos su registro para recibir la asesoría de salud preventiva "
            f"y rendimiento familiar de Equipo en Acción®. Nuestra metodología se enfoca en la modulación metabólica "
            f"y la vitalidad celular integral para elevar la calidad de vida de su hogar."
        )
        bloque2 = (
            f"Para que su Sherpa asignado prepare la ficha técnica adecuada, ¿cuál considera usted que es el pilar "
            f"prioritario a optimizar en su familia: la vitalidad diaria, el descanso reparador o el rendimiento físico?"
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
