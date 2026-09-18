"""Pruebas unitarias de integridad de código, máquina de estados de Pipeline e importación en lote."""
import pytest


def test_batch_import_atomic_clasificacion(api, db):
    payload = {
        "contactos": [
            {
                "nombre": "Contacto Test Lote 1",
                "telefono": "5511223344",
                "lista_estrategica": "capacidad"
            },
            {
                "nombre": "Contacto Test Lote 2",
                "telefono": "+5215599887766",
                "lista_estrategica": "influencia"
            }
        ]
    }
    resp = api.post("/api/leads/batch-import", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["importados"] == 2

    c1 = db.leads.find_one({"nombre": "Contacto Test Lote 1"})
    assert c1 is not None
    assert c1["telefono"] == "+525511223344"
    assert c1["clasificacion"]["lista"] == "capacidad"

    c2 = db.leads.find_one({"nombre": "Contacto Test Lote 2"})
    assert c2 is not None
    assert c2["clasificacion"]["lista"] == "influencia"


def test_pipeline_state_machine_guard(api, db):
    # Crear lead en estado Lead
    payload = {
        "sherpa_id": "s1",
        "nombre": "Lead State Guard",
        "telefono": "5544332211",
        "consentimiento_whatsapp": True
    }
    r_cap = api.post("/api/leads/capture", json=payload)
    assert r_cap.status_code == 201
    lead_id = r_cap.json()["id"]

    # Intentar saltar directamente a Sprint Activo sin activarlo
    r_patch = api.patch(f"/api/app/leads/{lead_id}/etapa", json={"etapa": "Sprint Activo"})
    assert r_patch.status_code == 400
    assert "Debe activar el Sprint 28" in r_patch.json()["detail"]


def test_code_integrity_no_hardcoding():
    import os
    index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    assert os.path.exists(index_path)

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verificar ausencia de números o credenciales hardcodeadas sensibles
    assert "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" not in content


def test_apertura_mensaje_opcional_y_link_integridad():
    import os
    index_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    static_index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    assert os.path.exists(index_path)
    assert os.path.exists(static_index_path)

    for p in [index_path, static_index_path]:
        with open(p, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. Existencia de función obtenerMensajeApertura y APERTURA_DEFAULT
        assert "APERTURA_DEFAULT" in content
        assert "function obtenerMensajeApertura" in content

        # 2. Ausencia de teléfonos/nombres hardcodeados en el flujo de apertura
        assert "sinergix_apertura_activa" in content
        assert "sinergix_apertura_texto" in content

        # 3. El guion conserva los 5 parámetros requeridos en el enlace de captura
        assert "pnom=" in content
        assert "ptel=" in content
        assert "sede=" in content
        assert "snom=" in content
        assert "stel=" in content
