"""Suite de Pruebas Automatizadas para la Fase 4 (Core Conversacional, Retención de Cartera & Red MLM).

Verifica endpoints y lógica de negocio:
  1. GET /api/sherpa/briefing (Briefing Matutino 8:00 AM con prioridades y alertas)
  2. GET /api/reports/cartera-salud (Semáforo de adherencia crítica < 80% y alerta_abandono)
  3. GET /api/reports/radar-multiplicadores (Líderes emergentes con +3 reclutas / 14 días)
  4. GET /api/reports/bono-retiro (Termómetro Bono Retiro $50k y avance de líderes directos)
  5. POST /api/bio-auditorias/book (Cita de Bio-Auditoría en Coworking Norte y flete GDL $95)
  6. POST /api/safety/check-cofepris (SafetyEngine Linter en tiempo real)
  7. POST /api/leads/{id}/send-ph21-content (Despacho de contenidos PH21: Reset Día 1 & Autofagia Día 21)
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from app.database import use_mock_db, get_db_client
from app.main import app


@pytest.fixture(autouse=True)
def setup_mock_db():
    use_mock_db()
    db = get_db_client()
    db.leads.delete_many({})
    db.sherpas.delete_many({})
    db.bio_auditorias.delete_many({})
    db.envios_educativos.delete_many({})
    yield db


@pytest.fixture
def api():
    return TestClient(app)


@pytest.fixture
def lead_fase4(db):
    # Registrar Sherpa emergente con 3 reclutas para test_radar
    sherpa_sub = {
        "_id": "s2_emergente",
        "email": "lider@sinergix.mx",
        "nombre": "Laura González",
        "api_token": "token-s2",
        "rol": "sherpa"
    }
    db.sherpas.insert_one(sherpa_sub)

    for i in range(3):
        db.leads.insert_one({
            "_id": f"lead_sub_{i}",
            "sherpa_id": "s2_emergente",
            "nombre": f"Recluta {i}",
            "telefono": f"+521550000000{i}",
            "etapa_pipeline": "Lead",
            "creado_en": datetime.now(timezone.utc)
        })

    doc = {
        "_id": "lead_fase4_test",
        "sherpa_id": "s1",
        "nombre": "Elena Torres",
        "telefono": "+5215599001122",
        "email": "elena@test.com",
        "etapa_pipeline": "Sprint Activo",
        "dia_actual_sprint": 25,
        "adherencia_acumulada": 75.0,  # Adherencia < 80% (Activa alerta de abandono)
        "respondio": False,
        "is_cancelled": False,
        "consentimiento_whatsapp": True,
        "posicion_red": "inscripcion",
        "creado_en": datetime.now(timezone.utc),
    }
    db.leads.insert_one(doc)
    doc["id"] = doc["_id"]
    return doc


def test_briefing_matutino_generacion(api, lead_fase4):
    """Verifica que el Briefing Matutino retorne resumen conversacional y acciones prioritarias."""
    r = api.get("/api/sherpa/briefing", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert "resumen_texto" in data
    assert "acciones_prioritarias" in data
    assert len(data["acciones_prioritarias"]) >= 1


def test_salud_cartera_alerta_adherencia_baja(api, lead_fase4):
    """Verifica que la adherencia < 80% active alerta_abandono = True en Salud de Cartera."""
    r = api.get("/api/reports/cartera-salud", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert "clientes" in data
    cliente = next((c for c in data["clientes"] if c["lead_id"] == "lead_fase4_test"), None)
    assert cliente is not None
    assert cliente["alerta_abandono"] is True
    assert cliente["nivel_riesgo"] == "alto"


def test_radar_multiplicadores(api, lead_fase4):
    """Verifica la respuesta del Radar de Multiplicadores con regla +3 reclutas."""
    r = api.get("/api/reports/radar-multiplicadores", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert "lideres_emergentes" in data
    assert len(data["lideres_emergentes"]) >= 1


def test_bono_retiro_status(api, lead_fase4):
    """Verifica el retorno del Termómetro del Bono Retiro de $50,000 MXN."""
    r = api.get("/api/reports/bono-retiro", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert data["bono_monto_mxn"] == 50000.0
    assert "lideres_directos" in data
    assert isinstance(data["lideres_directos"], list)


def test_bio_auditoria_booking_coworking(api, lead_fase4):
    """Verifica el agendamiento en Coworking Norte con tarifa de flete GDL $95."""
    r = api.post("/api/bio-auditorias/book", json={
        "lead_id": lead_fase4["id"],
        "coworking_sede": "Coworking Norte",
        "fecha_hora": "2026-09-01T11:00:00Z",
        "incluye_envio_gdl": True,
        "costo_flete_gdl": 95.0
    }, headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert data["coworking_sede"] == "Coworking Norte"
    assert data["costo_flete"] == 95.0
    assert "confirmada" in data["estado"]


def test_safety_engine_linter_cofepris(api):
    """Verifica que el Linter detecte palabras prohibidas por COFEPRIS y ofrezca reemplazos."""
    # 1. Texto con claim prohibido
    r_bad = api.post("/api/safety/check-cofepris", json={
        "texto": "Este producto cura la diabetes y quema la grasa rápidamente"
    })
    assert r_bad.status_code == 200
    data_bad = r_bad.json()
    assert data_bad["es_seguro"] is False
    assert len(data_bad["sugerencias"]) >= 2

    # 2. Texto seguro
    r_ok = api.post("/api/safety/check-cofepris", json={
        "texto": "Esta matriz apoya el bienestar y promueve la composición corporal"
    })
    assert r_ok.status_code == 200
    assert r_ok.json()["es_seguro"] is True


def test_despacho_contenido_ph21(api, lead_fase4):
    """Verifica el envío del contenido educativo de Reset (Día 1) y Autofagia (Día 21)."""
    r1 = api.post(f"/api/leads/{lead_fase4['id']}/send-ph21-content?dia_hito=1", headers={"X-API-Token": "token-default"})
    assert r1.status_code == 200
    assert "Reset" in r1.json()["contenido"]["titulo"]

    r21 = api.post(f"/api/leads/{lead_fase4['id']}/send-ph21-content?dia_hito=21", headers={"X-API-Token": "token-default"})
    assert r21.status_code == 200
    assert "Autofagia" in r21.json()["contenido"]["titulo"]
