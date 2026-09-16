"""Pruebas unitarias e integrales dedicadas para la Fase 3: Automatizaciones y Reglas de Negocio Asíncronas.

Cubre:
1. Validación y rechazo de X-Cron-Token en /api/sprint/nightly.
2. Detección de inactividad > 72h en prospectos 'Lead' / 'Sin Encuesta' y marcado de candidato_reactivacion.
3. Despacho asíncrono ultra-rápido de webhooks (<200 ms).
4. Persistencia de fallos en la cola Dead Letter Queue (tareas_fallidas_dlq).
"""
import json
import time
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.database import use_mock_db, get_db_client
from app.main import app
from app.services import dlq_service, nightly_cron, webhook_dispatcher


@pytest.fixture(autouse=True)
def setup_mock_db():
    use_mock_db()
    db = get_db_client()
    db.leads.delete_many({})
    db.sherpas.delete_many({})
    db.tareas_fallidas_dlq.delete_many({})
    yield db


@pytest.fixture
def api():
    return TestClient(app)


def test_nightly_cron_rechaza_sin_token(api):
    """Verifica que /api/sprint/nightly rechace solicitudes con token inválido cuandosettings.cron_token está configurado."""
    old_token = settings.cron_token
    settings.cron_token = "token_secreto_cron"
    try:
        r = api.post("/api/sprint/nightly", headers={"X-Cron-Token": "token_incorrecto"})
        assert r.status_code == 401
    finally:
        settings.cron_token = old_token


def test_nightly_cron_inactividad_72h(db):
    """Verifica que el cron nocturno detecte prospectos con >72h sin interacción y los marque candidato_reactivacion."""
    ahora = datetime.now(timezone.utc)
    hace_80h = ahora - timedelta(hours=80)

    lead_inactivo = {
        "_id": "lead_inactivo_72h",
        "sherpa_id": "s1",
        "nombre": "Pedro Inactivo",
        "telefono": "+5215500001111",
        "etapa_pipeline": "Lead",
        "respondio": False,
        "is_cancelled": False,
        "creado_en": hace_80h,
    }
    db.leads.insert_one(lead_inactivo)

    res = nightly_cron.ejecutar_cron_nocturno(db, x_cron_token="")
    assert res["status"] == "ok"
    assert res["candidatos_reactivacion_72h"] >= 1

    updated = db.leads.find_one({"_id": "lead_inactivo_72h"})
    assert updated["candidato_reactivacion"] is True
    assert updated["alerta_inactividad"] is True


def test_webhook_respuesta_ultra_rapida(api, db):
    """Verifica que los endpoints receptores de webhooks respondan de forma ultra-rápida (<200 ms)."""
    lead_doc = {
        "_id": "lead_webhook_fast",
        "sherpa_id": "s1",
        "nombre": "Ana Fast",
        "telefono": "+5215599998888",
        "etapa_pipeline": "Datos Enviados",
        "consentimiento_whatsapp": True,
        "creado_en": datetime.now(timezone.utc),
    }
    db.leads.insert_one(lead_doc)

    import hmac, hashlib
    raw_body = json.dumps({"event_id": "evt_fast_1", "telefono": "+5215599998888", "tipo": "primera_compra"}).encode()
    firma = hmac.new(settings.payment_webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()

    t_inicio = time.time()
    r = api.post(
        "/api/pagos/webhook",
        content=raw_body,
        headers={"X-Signature": firma, "Content-Type": "application/json"}
    )
    t_duracion_ms = (time.time() - t_inicio) * 1000

    assert r.status_code == 200
    assert t_duracion_ms < 200.0, f"El webhook tardó {t_duracion_ms:.2f} ms (esperado < 200 ms)"


def test_dlq_registro_fallos(db):
    """Verifica la persistencia de tareas fallidas en la colección tareas_fallidas_dlq."""
    dlq_id = dlq_service.registrar_tarea_fallida(
        db=db,
        tipo_tarea="envio_whatsapp_hsm",
        payload={"lead_id": "l1", "plantilla": "SPR_01"},
        error_msg="Timeout de conexión con WhatsApp Cloud API",
        intento=1,
        max_intentos=3
    )
    assert dlq_id.startswith("dlq_")

    tarea = db.tareas_fallidas_dlq.find_one({"_id": dlq_id})
    assert tarea is not None
    assert tarea["tipo_tarea"] == "envio_whatsapp_hsm"
    assert tarea["estado"] == "pendiente_reintento"
