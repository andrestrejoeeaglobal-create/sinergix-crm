"""Pruebas Automatizadas para el Motor del Asistente T.I.L.O.

Verifica:
1. Matriz de bifurcación: Ruta A (Salud) vs Ruta B (Negocio / Sherpa)
2. Estructura de salida obligatoria: 2 Párrafos de Poder separados por '\\n\\n'
3. Trato formal estricto («Usted», «Su», «Le»), sin tuteo.
4. Cero preguntas en el primer bloque de validación.
5. Pregunta unívoca al final del segundo bloque.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.tilo_assistant import procesar_respuesta_tilo


client = TestClient(app)


def test_tilo_ruta_a_salud_metabolismo():
    """Prueba Ruta A: Prospecto enfocado en energía y metabolismo."""
    lead = {
        "nombre": "Roberto Morales",
        "telefono": "+5215512345678",
        "objetivo": "Aumentar Energía y Metabolismo Cellular"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta A - Salud / Metabolismo"
    assert res["etiqueta"] == "Cliente Potencial"
    
    # Estructura de 2 Párrafos de Poder
    respuesta = res["respuesta"]
    parrafos = respuesta.split("\n\n")
    assert len(parrafos) == 2, f"Se esperaban 2 párrafos separados por doble salto, se obtuvieron: {len(parrafos)}"
    
    bloque1, bloque2 = parrafos[0], parrafos[1]
    
    # Cero preguntas en el bloque 1
    assert "?" not in bloque1, "El Bloque 1 no debe contener preguntas"
    assert "¿" not in bloque1, "El Bloque 1 no debe contener preguntas"
    
    # Pregunta unívoca en el bloque 2
    assert "?" in bloque2 and "¿" in bloque2, "El Bloque 2 debe culminar con una pregunta unívoca"
    assert "obstáculo" in bloque2.lower() or "energía" in bloque2.lower()
    
    # Trato formal de Usted
    assert res["trato_formal"] is True
    assert res["tiene_tuteo"] is False


def test_tilo_ruta_b_negocio_sherpa():
    """Prueba Ruta B: Prospecto aspirante a Sherpa / Ingresos."""
    lead = {
        "nombre": "Carolina Gómez",
        "telefono": "+5215598765432",
        "objetivo": "Generar Ingresos Residuales como Sherpa"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta B - Negocio / Sherpa"
    assert res["etiqueta"] == "Aspirante a Sherpa"
    
    # Estructura de 2 Párrafos de Poder
    respuesta = res["respuesta"]
    parrafos = respuesta.split("\n\n")
    assert len(parrafos) == 2, f"Se esperaban 2 párrafos separados por doble salto, se obtuvieron: {len(parrafos)}"
    
    bloque1, bloque2 = parrafos[0], parrafos[1]
    
    # Cero preguntas en el bloque 1
    assert "?" not in bloque1, "El Bloque 1 no debe contener preguntas"
    
    # Pregunta de plaza / municipio en el bloque 2
    assert "plaza" in bloque2.lower() or "ciudad" in bloque2.lower() or "municipio" in bloque2.lower()
    assert "?" in bloque2
    
    # Trato formal de Usted
    assert res["trato_formal"] is True
    assert res["tiene_tuteo"] is False


def test_tilo_qualify_endpoint():
    """Prueba de integración HTTP del endpoint /api/tilo/qualify."""
    r = client.post("/api/tilo/qualify", json={
        "nombre": "Gabriel Silva",
        "telefono": "+5215533334444",
        "objetivo": "Generar Ingresos Residuales como Sherpa"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["etiqueta"] == "Aspirante a Sherpa"
    assert "respuesta" in data
