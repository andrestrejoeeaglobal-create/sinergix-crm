"""Fixtures de pruebas: SQLite en archivo temporal + env antes de importar la app."""
import os
import sys
import tempfile

import pytest

# Env ANTES de importar app.* (config se lee al importar)
_TMP = tempfile.mkdtemp(prefix="sinergix_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/crm_test.db"
os.environ["PAYMENT_WEBHOOK_SECRET"] = "secret-de-prueba"
os.environ["PUNTOS_POR_PLAN"] = "100"
os.environ["CHATWOOT_URL"] = ""       # mock
os.environ["COTIZACION_URL"] = ""     # mock
os.environ["BIOMETRIA_URL"] = ""      # mock
os.environ["CRON_TOKEN"] = ""

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient  # noqa: E402
from app.db import init_db  # noqa: E402
from app.main import app  # noqa: E402

init_db()
client = TestClient(app)


@pytest.fixture()
def api():
    return client


_contador_telefonos = iter(range(5520000000, 5529999999))


@pytest.fixture()
def lead_de_prueba(api):
    telefono = f"+52{next(_contador_telefonos)}"
    r = api.post("/api/leads/capture", json={
        "sherpa_id": "sherpa_marco",
        "nombre": "María",
        "telefono": telefono,
        "email": "maria@test.mx",
        "canal_captacion": "landing",
        "utm_source": "instagram",
        "utm_campaign": "reel_autofagia",
        "optin_whatsapp": True,
    })
    assert r.status_code == 201, r.text
    return r.json()
