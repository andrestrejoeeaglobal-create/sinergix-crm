"""Motor del Asistente Sinergix CRM — Gira de Poder 2026.

Alineación Operativa con captura.html y Gobernanza de Prospección:
1. Misión Principal: Concierge de Enlace, Confirmación de Plaza y Bienvenida a la Cordada para la
   GIRA DE PODER 2026 DE EQUIPO EN ACCIÓN®.
2. Tono y Trato Obligatorio: Trato directo de «TÚ» (cálido, cercano, motivador, de igual a igual).
   Estrictamente prohibido el «Usted» y cualquier referencia a síntomas, patologías, consultas o temas médicos.
3. Logística de 4 Plazas:
   - Puebla: 21 sep
   - Izúcar de Matamoros: 22 sep
   - Tecamachalco: 23 sep
   - Huamantla: 24 sep
4. Regla Canónica del Concurso:
   «🏆 Concurso por Plaza: Bolsa de $10,000 MXN en efectivo. El equipo que logre los mejores resultados de la jornada (medidos y validados en el CRM) gana y se lleva la bolsa completa.»
5. Requisitos de Acceso: $500 MXN (100% reembolsables en producto) o 5 cajas compradas a tu nombre.
6. Estructura Obligatoria de Salida (2 Bloques):
   - Bloque 1 (Bienvenida y Contexto): Cero preguntas.
   - Bloque 2 (Bolsa Canónica y Cierre): Concluye siempre con una sola pregunta unívoca de avance.
   - Bloques separados exactamente por doble salto de línea `\n\n`.
"""
from typing import Dict, Any

FORMULA_CANONICA_BOLSA = (
    "🏆 Concurso por Plaza: Bolsa de $10,000 MXN en efectivo. "
    "El equipo que logre los mejores resultados de la jornada (medidos y validados en el CRM) gana y se lleva la bolsa completa."
)

PROMPT_SISTEMA_TILO = f"""Eres T.I.L.O., el Asistente del Sinergix CRM y Concierge de Enlace de Equipo en Acción® para la Gira de Poder 2026.

REGLAS DE TONO Y OPERACIÓN:
1. Trato Obligatorio de «TÚ»: Háblale al usuario en segunda persona informal (cálido, cercano, motivador, de igual a igual: «tú», «te», «tu», «contigo»). Queda estrictamente prohibido el «Usted», «Su», «Le» o cualquier formalidad distante.
2. Cero Términos Médicos o Clínicos: Queda prohibido cualquier referencia a síntomas, patologías, consultas, expedientes, triaje o términos médicos («clínico», «metabólico», «consulta»). La misión es 100% de prospección, liderazgo y despliegue en campo.
3. Logística de la Gira (4 Plazas):
   - Puebla: Lunes 21 de septiembre
   - Izúcar de Matamoros: Martes 22 de septiembre
   - Tecamachalco: Miércoles 23 de septiembre
   - Huamantla: Jueves 24 de septiembre
4. Regla Canónica del Concurso:
   «{FORMULA_CANONICA_BOLSA}»
5. Requisitos de Acceso: $500 MXN (100% reembolsables en producto) o 5 cajas compradas a tu nombre.
6. Estructura de Salida Obligatoria (2 Bloques):
   - Bloque 1: Bienvenida motivadora, contexto de la gira y causa. Queda estrictamente prohibido incluir preguntas en el primer bloque.
   - Bloque 2: Regla canónica de la bolsa de $10,000 MXN, condiciones de acceso y concluye SIEMPRE con una sola pregunta unívoca de avance.
   - Separados exactamente por doble salto de línea `\\n\\n`.
"""


def procesar_respuesta_tilo(lead: Dict[str, Any]) -> Dict[str, Any]:
    """Genera la respuesta calibrada del Asistente Sinergix CRM basada en la ficha del lead en captura.html."""
    nombre = (lead.get("nombre") or "").strip()
    primer_nombre = nombre.split()[0] if nombre else "Líder"

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
    
    es_gira = (
        "gira" in proposito_lower or 
        "terreno" in proposito_lower or 
        "convocatoria" in proposito_lower or
        "plaza" in proposito_lower or
        "16" in proposito_lower or
        "virtual" in proposito_lower
    )

    if es_sherpa:
        ruta = "Ruta 1 - Aspirante a Sherpa"
        etiqueta = "Aspirante a Sherpa"
        sede_txt = f" en la sede {sede}" if sede else ""
        bloque1 = (
            f"¡Hola, {primer_nombre}! Qué gusto saludarte. Confirmamos tu registro como Sherpa "
            f"para el despliegue de la Gira de Poder 2026 de Equipo en Acción®. Reconocemos tu liderazgo "
            f"para abrir brecha{sede_txt} e impulsarla con nuestra causa: «No venimos solo a vender; venimos a transformar la salud de quienes amamos»."
        )
        bloque2 = (
            f"{FORMULA_CANONICA_BOLSA}\n\n"
            f"El acceso son $500 MXN (100% reembolsables en producto) o 5 cajas compradas a tu nombre. "
            f"¿Tienes disponibilidad para conectarte a la alineación previa con tu equipo?"
        )
    elif es_gira:
        ruta = "Ruta 2 - Convocatoria Gira de Campo"
        etiqueta = "Convocatoria Gira de Campo"
        bloque1 = (
            f"¡Hola, {primer_nombre}! Te damos la más cálida bienvenida al registro oficial de la Gira de Poder 2026. "
            f"Tu lugar en la cordada ha quedado apartado para acompañarnos en el despliegue de terreno en las 4 plazas: "
            f"Puebla (21 sep), Izúcar de Matamoros (22 sep), Tecamachalco (23 sep) y Huamantla (24 sep)."
        )
        bloque2 = (
            f"{FORMULA_CANONICA_BOLSA}\n\n"
            f"Recuerda que el acceso son $500 MXN o 5 cajas compradas a tu nombre. "
            f"¿Deseas que te enviemos por WhatsApp la ubicación exacta de la oficina en tu plaza?"
        )
    else:
        ruta = "Ruta 3 - Estrategia y Vitalidad Familiar"
        etiqueta = "Cliente Potencial - Bienestar Familiar"
        bloque1 = (
            f"¡Hola, {primer_nombre}! Qué alegría saludarte. Confirmamos tu registro para integrarte a la estrategia de "
            f"bienestar y vitalidad familiar de Equipo en Acción®. Nos moveremos en la Gira de Poder 2026 a través de las 4 plazas: "
            f"Puebla (21 sep), Izúcar (22 sep), Tecamachalco (23 sep) y Huamantla (24 sep)."
        )
        bloque2 = (
            f"{FORMULA_CANONICA_BOLSA}\n\n"
            f"El acceso son $500 MXN o 5 cajas compradas a tu nombre. "
            f"¿Cuál de las 4 plazas te queda más cerca para recibirte a ti y a tu familia?"
        )

    respuesta_texto = f"{bloque1}\n\n{bloque2}"

    palabras_medicas_prohibidas = ["clínico", "clinico", "metabólico", "metabolico", "consulta", "síntoma", "sintoma", "patología", "patologia", "paciente", "triaje"]
    palabras_formal_prohibidas = ["usted", " su ", " le ", " diríjase ", " considere "]

    respuesta_lower = respuesta_texto.lower()

    return {
        "ok": True,
        "ruta": ruta,
        "etiqueta": etiqueta,
        "respuesta": respuesta_texto,
        "bloque1": bloque1,
        "bloque2": bloque2,
        "parrafos_count": len(respuesta_texto.split("\n\n")),
        "tiene_tuteo": any(w in respuesta_lower for w in [" tú ", " te ", " tu ", "tienes", "puedes", "quieres", "contigo", "saludarte", "darte", "recibirte"]),
        "trato_formal": any(w in respuesta_lower for w in palabras_formal_prohibidas),
        "tiene_palabras_medicas": any(w in respuesta_lower for w in palabras_medicas_prohibidas),
        "formula_canonica_ok": FORMULA_CANONICA_BOLSA in respuesta_texto
    }
