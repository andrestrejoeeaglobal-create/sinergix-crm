"""Pruebas Automatizadas para el Motor del Asistente Sinergix CRM (Gira de Poder 2026)

Verifica:
1. Matriz de Enrutamiento (3 Rutas):
   - Ruta 1: Aspirante a Sherpa
   - Ruta 2: Convocatoria Gira de Campo
   - Ruta 3: Estrategia y Vitalidad Familiar
2. Estructura de Salida Obligatoria: 2 Párrafos/Bloques de Poder separados por '\\n\\n'
3. Trato Obligatorio de «TÚ» («te», «tu», «contigo», etc.), Ausencia Estricta de «Usted» o formalismos.
4. Cero preguntas en el primer bloque de bienvenida.
5. Pregunta unívoca de avance al final del segundo bloque.
6. Cumplimiento Normativo: Ausencia total de lenguaje clínico, metabólico, diagnósticos o consultas médicas.
7. Presencia EXACTA de la fórmula canónica de la bolsa de $10,000 MXN en efectivo.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.tilo_assistant import procesar_respuesta_tilo, FORMULA_CANONICA_BOLSA


client = TestClient(app)

FORMULA_ESPERADA = (
    "🏆 Concurso por Plaza: Bolsa de $10,000 MXN en efectivo. "
    "El equipo que logre los mejores resultados de la jornada (medidos y validados en el CRM) gana y se lleva la bolsa completa."
)


def test_tilo_ruta_1_aspirante_sherpa():
    """Prueba Ruta 1: Prospecto postulado como Sherpa."""
    lead = {
        "nombre": "Carolina Gómez",
        "telefono": "+5215598765432",
        "proposito": "Quiero sumarse como Sherpa y abrir brecha en mi plaza (Premio $10,000 MXN)",
        "sede": "Puebla (Lunes 21 sep)"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta 1 - Aspirante a Sherpa"
    assert res["etiqueta"] == "Aspirante a Sherpa"
    
    # Estructura de 2 Bloques de Poder
    respuesta = res["respuesta"]
    parrafos = respuesta.split("\n\n")
    assert len(parrafos) >= 2, f"Se esperaban bloques separados por doble salto, se obtuvieron: {len(parrafos)}"
    
    bloque1 = parrafos[0]
    
    # Cero preguntas en el bloque 1
    assert "?" not in bloque1 and "¿" not in bloque1, "El Bloque 1 no debe contener preguntas"
    
    # Pregunta de alineación al final
    assert "?" in respuesta and "¿" in respuesta
    
    # Trato informal obligatorio (Tú) y ausencia de usted / palabras médicas
    assert res["tiene_tuteo"] is True
    assert res["trato_formal"] is False
    assert res["tiene_palabras_medicas"] is False
    
    # Verificación de la regla canónica de $10,000 MXN
    assert FORMULA_ESPERADA in respuesta
    assert res["formula_canonica_ok"] is True


def test_tilo_ruta_2_convocatoria_gira():
    """Prueba Ruta 2: Prospecto registrado para la Convocatoria Gira de Campo."""
    lead = {
        "nombre": "Carlos Mendoza",
        "telefono": "+5215544445555",
        "proposito": "Quiero registrarme a la Convocatoria Gira de Campo 21-24 Sep"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta 2 - Convocatoria Gira de Campo"
    assert res["etiqueta"] == "Convocatoria Gira de Campo"
    
    respuesta = res["respuesta"]
    bloque1 = respuesta.split("\n\n")[0]
    assert "?" not in bloque1 and "¿" not in bloque1
    assert "?" in respuesta and "¿" in respuesta
    
    assert res["tiene_tuteo"] is True
    assert res["trato_formal"] is False
    assert res["tiene_palabras_medicas"] is False
    assert FORMULA_ESPERADA in respuesta


def test_tilo_ruta_3_estrategia_vitalidad_familiar():
    """Prueba Ruta 3: Prospecto enfocado en estrategia de bienestar familiar."""
    lead = {
        "nombre": "Roberto Morales",
        "telefono": "+5215512345678",
        "proposito": "Busco integrarme a la estrategia de bienestar para mi familia"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta 3 - Estrategia y Vitalidad Familiar"
    assert res["etiqueta"] == "Cliente Potencial - Bienestar Familiar"
    
    respuesta = res["respuesta"]
    bloque1 = respuesta.split("\n\n")[0]
    assert "?" not in bloque1 and "¿" not in bloque1
    assert "?" in respuesta and "¿" in respuesta
    
    assert res["tiene_tuteo"] is True
    assert res["trato_formal"] is False
    assert res["tiene_palabras_medicas"] is False
    assert FORMULA_ESPERADA in respuesta


def test_tilo_qualify_endpoint():
    """Prueba de integración HTTP del endpoint /api/tilo/qualify."""
    r = client.post("/api/tilo/qualify", json={
        "nombre": "Gabriel Silva",
        "telefono": "+5215533334444",
        "proposito": "Aspirante a Sherpa (Abrir plaza - Premio $10K)",
        "sede": "Izúcar de Matamoros (Martes 22 sep)"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["etiqueta"] == "Aspirante a Sherpa"
    assert "respuesta" in data
    assert FORMULA_ESPERADA in data["respuesta"]
    assert data["tiene_tuteo"] is True
    assert data["trato_formal"] is False
    assert data["tiene_palabras_medicas"] is False


def test_tilo_validacion_estricta_tuteo_sin_medicina_ni_usted():
    """Prueba de seguridad: Valida que ninguna respuesta contenga palabras prohibidas y que contenga tuteo."""
    leads_de_prueba = [
        {"nombre": "Ana Paola", "proposito": "Sherpa 10k"},
        {"nombre": "Luis Jorge", "proposito": "Gira de terreno plaza Huamantla"},
        {"nombre": "María Elena", "proposito": "Asesoría de vitalidad familiar"}
    ]
    palabras_prohibidas = ["usted", "su ", "le ", "clínico", "clinico", "metabólico", "metabolico", "consulta", "síntoma", "sintoma", "patología", "patologia"]

    for lead in leads_de_prueba:
        res = procesar_respuesta_tilo(lead)
        txt = res["respuesta"].lower()
        for p in palabras_prohibidas:
            assert p not in txt, f"La respuesta contenía la palabra prohibida '{p}': {txt}"
        
        # Validar tuteo obligatorio
        assert any(t in txt for t in ["te ", "tu ", "contigo", "saludarte", "darte", "recibirte", "tienes"]), f"La respuesta no contiene tuteo obligatorio: {txt}"
        
        # Validar la inclusión exacta de la regla canónica
        assert FORMULA_CANONICA_BOLSA in res["respuesta"]
