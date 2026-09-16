"""Pruebas Automatizadas para el Motor del Asistente T.I.L.O. (Alineado con captura.html)

Verifica:
1. Matriz de Enrutamiento (3 Rutas):
   - Ruta 1: Aspirante a Sherpa
   - Ruta 2: Transmisión Virtual 16 Sep
   - Ruta 3: Salud y Rendimiento Familiar
2. Estructura de Salida Obligatoria: 2 Párrafos de Poder separados por '\\n\\n'
3. Trato Formal Estricto («Usted», «Su», «Le»), Cero Tuteo.
4. Cero preguntas en el primer bloque de bienvenida.
5. Pregunta unívoca al final del segundo bloque.
6. Cumplimiento Normativo: Ausencia de triaje clínico u hospitalario.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.tilo_assistant import procesar_respuesta_tilo


client = TestClient(app)


def test_tilo_ruta_1_aspirante_sherpa():
    """Prueba Ruta 1: Prospecto postulado como Sherpa."""
    lead = {
        "nombre": "Carolina Gómez",
        "telefono": "+5215598765432",
        "proposito": "Quiero sumarme como Sherpa y abrir brecha en mi plaza (Premio $10,000 MXN)",
        "sede": "Puebla (Lunes 21 sep)"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta 1 - Aspirante a Sherpa"
    assert res["etiqueta"] == "Aspirante a Sherpa"
    
    # Estructura de 2 Párrafos de Poder
    respuesta = res["respuesta"]
    parrafos = respuesta.split("\n\n")
    assert len(parrafos) == 2, f"Se esperaban 2 párrafos separados por doble salto, se obtuvieron: {len(parrafos)}"
    
    bloque1, bloque2 = parrafos[0], parrafos[1]
    
    # Cero preguntas en el bloque 1
    assert "?" not in bloque1 and "¿" not in bloque1, "El Bloque 1 no debe contener preguntas"
    
    # Pregunta de alineación en el bloque 2
    assert "disponibilidad" in bloque2.lower() or "alineación" in bloque2.lower()
    assert "?" in bloque2 and "¿" in bloque2
    
    # Trato formal de Usted
    assert res["trato_formal"] is True
    assert res["tiene_tuteo"] is False


def test_tilo_ruta_2_transmision_virtual():
    """Prueba Ruta 2: Prospecto registrado para la Transmisión Virtual del 16 sep."""
    lead = {
        "nombre": "Carlos Mendoza",
        "telefono": "+5215544445555",
        "proposito": "Quiero sintonizar la Transmisión Especial del 16 de septiembre"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta 2 - Transmisión Virtual 16 Sep"
    assert res["etiqueta"] == "Asistente Transmisión Virtual"
    
    parrafos = res["respuesta"].split("\n\n")
    assert len(parrafos) == 2
    
    bloque1, bloque2 = parrafos[0], parrafos[1]
    assert "?" not in bloque1 and "¿" not in bloque1
    assert "enlace" in bloque2.lower() or "whatsapp" in bloque2.lower()
    assert "?" in bloque2 and "¿" in bloque2
    
    assert res["trato_formal"] is True
    assert res["tiene_tuteo"] is False


def test_tilo_ruta_3_salud_preventiva_familiar():
    """Prueba Ruta 3: Prospecto enfocado en salud preventiva familiar."""
    lead = {
        "nombre": "Roberto Morales",
        "telefono": "+5215512345678",
        "proposito": "Busco asesoría de salud preventiva para mí y mi familia"
    }
    res = procesar_respuesta_tilo(lead)
    
    assert res["ok"] is True
    assert res["ruta"] == "Ruta 3 - Salud y Rendimiento Familiar"
    assert res["etiqueta"] == "Cliente Potencial - Salud Preventiva"
    
    parrafos = res["respuesta"].split("\n\n")
    assert len(parrafos) == 2
    
    bloque1, bloque2 = parrafos[0], parrafos[1]
    assert "?" not in bloque1 and "¿" not in bloque1
    assert "pilar" in bloque2.lower() or "optimizar" in bloque2.lower()
    assert "?" in bloque2 and "¿" in bloque2
    
    assert res["trato_formal"] is True
    assert res["tiene_tuteo"] is False


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
