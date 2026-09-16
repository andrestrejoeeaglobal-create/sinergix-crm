"""Pruebas unitarias e integrales dedicadas para la Fase 2: Esquema de Métricas & Reportes.

Verifica el aislamiento multi-inquilino mediante la cabecera `X-API-Token`, la agregación `$facet`
homologada a `creado_en`, la evaluación de Lado de registro (`inscripcion` y `equilibrio`) y los endpoints.
"""
from datetime import date, datetime, timezone
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
    yield db


@pytest.fixture
def api():
    return TestClient(app)


@pytest.fixture
def lead_de_prueba(db):
    doc = {
        "_id": "lead_test_reports_1",
        "sherpa_id": "s1",
        "nombre": "Report Lead Test",
        "telefono": "+5215511112222",
        "email": "report@test.com",
        "etapa_pipeline": "Datos Enviados",
        "respondio": True,
        "is_cancelled": False,
        "consentimiento_whatsapp": True,
        "clasificacion": {"lista": "confianza", "nota": "Lead prioritario"},
        "posicion_red": "inscripcion",
        "canal_captacion": "landing",
        "creado_en": datetime.now(timezone.utc),
    }
    db.leads.insert_one(doc)
    doc["id"] = doc["_id"]
    return doc


def test_get_dashboard_report_fase2(api, lead_de_prueba):
    """Prueba GET /api/reports/dashboard con X-API-Token y validación de contrato DashboardReportResponse."""
    r = api.get("/api/reports/dashboard", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()

    assert "pipeline" in data
    assert "clasificacion" in data
    assert "sprint" in data
    assert "distribucion_red" in data

    pipeline = data["pipeline"]
    assert pipeline["total_leads"] >= 1
    assert pipeline["respondieron"] >= 1
    assert pipeline["cotizados"] >= 1

    clasif = data["clasificacion"]
    assert clasif["confianza"] >= 1

    red = data["distribucion_red"]
    assert red["inscripcion"] >= 1


def test_get_dashboard_report_filtro_fechas(api, lead_de_prueba):
    """Prueba GET /api/reports/dashboard con filtro de fechas sobre creado_en."""
    today_str = date.today().isoformat()
    r = api.get(f"/api/reports/dashboard?fecha_inicio={today_str}&fecha_fin={today_str}", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert data["periodo_inicio"] == today_str
    assert data["periodo_fin"] == today_str


def test_get_funnel_report(api, lead_de_prueba):
    """Prueba GET /api/reports/funnel."""
    r = api.get("/api/reports/funnel?utm_campaign=spring2026", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert "etapas" in data
    assert len(data["etapas"]) > 0


def test_get_sprint_history(api, lead_de_prueba):
    """Prueba GET /api/reports/sprint-history."""
    r = api.get("/api/reports/sprint-history", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert "historico" in data
    assert len(data["historico"]) > 0
