"""Suite de Pruebas Automatizadas para la Fase 5 (Telemetría H7, Visión IA, Bus Multimódulo & Simulador Financiero).

Verifica:
  1. POST /api/biometrics/ingest & GET /api/biometrics/lead/{id}/history (Telemetría Banda H7)
  2. POST /api/nutrition/analyze-dish (Visión IA desacoplada sin llamadas externas de red)
  3. POST /api/ecosystem/bus/publish & GET /api/ecosystem/bus/events (Validación HMAC segura contra timing attacks)
  4. GET /api/reports/financial-simulator (Simulador financiero, 4 Sherpas, Matching Bonus 10% y patrimonio 5 años $911K)
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.database import use_mock_db, get_db_client
from app.main import app
from app.services.ecosystem_bus_service import generar_firma_bus
import json


@pytest.fixture(autouse=True)
def setup_mock_db():
    use_mock_db()
    db = get_db_client()
    db.leads.delete_many({})
    db.sherpas.delete_many({})
    db.telemetria_biometrica.delete_many({})
    db.auditorias_platos.delete_many({})
    db.eventos_ecosistema_bus.delete_many({})
    yield db


@pytest.fixture
def api():
    return TestClient(app)


@pytest.fixture
def lead_fase5(db):
    doc = {
        "_id": "lead_fase5_test",
        "sherpa_id": "s1",
        "nombre": "Roberto Gómez",
        "telefono": "+5215588776655",
        "email": "roberto@test.com",
        "etapa_pipeline": "Sprint Activo",
        "dia_actual_sprint": 14,
        "adherencia_acumulada": 90.0,
        "respondio": True,
        "is_cancelled": False,
        "consentimiento_whatsapp": True,
        "posicion_red": "equilibrio",
        "creado_en": datetime.now(timezone.utc),
    }
    db.leads.insert_one(doc)
    doc["id"] = doc["_id"]
    return doc


def test_ingesta_biometrica_h7(api, lead_fase5):
    """Verifica ingesta y consulta de telemetría biométrica IoT de la Banda H7."""
    r = api.post("/api/biometrics/ingest", json={
        "lead_id": lead_fase5["id"],
        "hrv_ms": 55,
        "frecuencia_cardiaca_lpm": 60,
        "temperatura_basal_delta": 0.3,
        "minutos_sueno": 450,
        "calidad_sueno_porcentaje": 90.0,
        "dispositivo_id": "H7_TEST_001"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["hrv_ms"] == 55
    assert data["sueno"]["minutos_totales"] == 450

    r_hist = api.get(f"/api/biometrics/lead/{lead_fase5['id']}/history", headers={"X-API-Token": "token-default"})
    assert r_hist.status_code == 200
    assert len(r_hist.json()) >= 1


def test_analisis_platos_vision_ia_desacoplada(api, lead_fase5):
    """Verifica el análisis de platos por visión por computadora sin llamadas de red externas."""
    r = api.post("/api/nutrition/analyze-dish", json={
        "lead_id": lead_fase5["id"],
        "sprint_dia": 14,
        "imagen_url": "https://sinergix.mx/media/plato_saludable.jpg"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["adherencia_score"] >= 0.8
    assert data["semaforo"] == "verde"
    assert len(data["alimentos_detectados"]) >= 1


def test_bus_eventos_multimodulo_hmac_compare_digest(api):
    """Verifica la publicación de eventos en el bus multimódulo con firma HMAC segura."""
    payload_dict = {"lead_id": "lead_123", "monto": 890.0}
    payload_raw = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
    firma_ok = generar_firma_bus(payload_raw)

    # 1. Evento publicado con firma HMAC válida
    r_ok = api.post("/api/ecosystem/bus/publish", json={
        "modulo_origen": "creator",
        "tipo_evento": "lead.capturado",
        "payload": payload_dict,
        "firma_hmac": firma_ok
    })
    assert r_ok.status_code == 200
    assert r_ok.json()["estado_despacho"] == "procesado"

    # 2. Evento con firma HMAC inválida -> HTTP 401
    r_bad = api.post("/api/ecosystem/bus/publish", json={
        "modulo_origen": "creator",
        "tipo_evento": "lead.capturado",
        "payload": payload_dict,
        "firma_hmac": "firma_falsa_invalid"
    })
    assert r_bad.status_code == 401

    # 3. Consulta de auditoría de eventos
    r_events = api.get("/api/ecosystem/bus/events", headers={"X-API-Token": "token-default"})
    assert r_events.status_code == 200
    assert len(r_events.json()) >= 1


def test_simulador_financiero_matching_bonus_10pct(api, lead_fase5):
    """Verifica el cálculo del simulador financiero, 4 Sherpas, Matching Bonus 10% y patrimonio 5 años $911K."""
    r = api.get("/api/reports/financial-simulator", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert data["mrr_actual"] >= 292.0
    assert data["proyeccion_4_sherpas"] >= 40000.0
    assert data["matching_bonus_10pct"] >= 4000.0
    assert data["patrimonio_5_anos"] == 911000.0
