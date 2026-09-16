"""Fixtures de Pytest usando MongoDB mongomock en memoria (ENMIENDA 2)."""
import os
import sys

import pytest

# Env ANTES de importar app.*
os.environ["PAYMENT_WEBHOOK_SECRET"] = "secret-de-prueba"
os.environ["CHATWOOT_WEBHOOK_SECRET"] = "secret-chatwoot-prueba"
os.environ["PUNTOS_POR_PLAN"] = "100"
os.environ["CHATWOOT_URL"] = ""       # mock
os.environ["COTIZACION_URL"] = ""     # mock
os.environ["BIOMETRIA_URL"] = ""      # mock
os.environ["CRON_TOKEN"] = ""

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import use_mock_db, get_db_client  # noqa: E402
use_mock_db()

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


@pytest.fixture()
def api():
    return client


@pytest.fixture()
def db():
    return get_db_client()


_contador_telefonos = iter(range(5520000000, 5529999999))


@pytest.fixture()
def lead_de_prueba(api):
    telefono = f"+52{next(_contador_telefonos)}"
    r = api.post("/api/leads/capture", json={
        "sherpa_id": "s1",
        "nombre": "María",
        "telefono": telefono,
        "email": "maria@test.mx",
        "canal_captacion": "landing",
        "utm_source": "instagram",
        "utm_campaign": "reel_autofagia",
        "consentimiento_whatsapp": True,
        "mecanismo_captura": "formulario_web"
    })
    assert r.status_code == 201, r.text
    return r.json()
