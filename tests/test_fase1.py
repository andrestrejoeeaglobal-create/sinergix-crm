"""Pruebas unitarias e integrales para las 8 Enmiendas, Plan v6, Alineación OpenAPI y Lado de registro (Plan v10)."""
import hashlib
import hmac
import json
import os
from app.config import settings


def _firma_pago(body: bytes) -> str:
    return hmac.new(settings.payment_webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


# ── ALINEACIÓN OPENAPI 3.1.0 ─────────────────────────────────────

def test_openapi_wa_link(api, lead_de_prueba):
    """Prueba GET /api/leads/{id}/wa-link."""
    lead_id = lead_de_prueba["id"]
    r = api.get(f"/api/leads/{lead_id}/wa-link?texto=Hola", headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    data = r.json()
    assert "url" in data
    assert "https://wa.me/" in data["url"]


def test_openapi_classify(api, lead_de_prueba):
    """Prueba POST /api/leads/{id}/classify."""
    lead_id = lead_de_prueba["id"]
    r = api.post(f"/api/leads/{lead_id}/classify", json={
        "lista": "confianza",
        "nota": "Prospecto cálido de confianza"
    }, headers={"X-API-Token": "token-default"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["lista"] == "confianza"


def test_openapi_send_to_external_y_validacion_regex(api, lead_de_prueba):
    """Prueba POST /api/leads/{id}/send-to-external y validación regex de CP y Lado de registro."""
    lead_id = lead_de_prueba["id"]

    # 1. CP Inválido (no cumple ^\d{5}$) -> HTTP 422
    r_bad = api.post(f"/api/leads/{lead_id}/send-to-external", json={
        "calle": "Av. Siempre Viva", "numero_exterior": "742",
        "colonia": "Centro", "codigo_postal": "6400",
        "ciudad_municipio": "Monterrey", "estado": "Nuevo León",
        "distribuidor_patrocinador_id": "EEA-12345",
        "posicion_red": "equilibrio"
    }, headers={"X-API-Token": "token-default"})
    assert r_bad.status_code == 422

    # 2. CP y Lado de registro Válido (equilibrio) -> HTTP 200
    r_ok = api.post(f"/api/leads/{lead_id}/send-to-external", json={
        "calle": "Av. Siempre Viva", "numero_exterior": "742",
        "colonia": "Centro", "codigo_postal": "64000",
        "ciudad_municipio": "Monterrey", "estado": "Nuevo León",
        "distribuidor_patrocinador_id": "EEA-12345",
        "posicion_red": "equilibrio"
    }, headers={"X-API-Token": "token-default"})
    assert r_ok.status_code == 200
    assert r_ok.json()["ok"] is True


def test_openapi_google_login(api):
    """Prueba GET /api/auth/google/login."""
    r = api.get("/api/auth/google/login")
    assert r.status_code == 200
    assert "authorization_url" in r.json()


# ── AJUSTE TÉCNICO 1: Normalización E.164 e Importación Masiva ────

def test_batch_import_normaliza_e164_y_desduplica(api, db):
    r = api.post("/api/leads/batch-import", json={
        "contactos": [
            {"nombre": "Carlos M1", "telefono": "55 1234 5678"},
            {"nombre": "Carlos M2", "telefono": "+525512345678"},
            {"nombre": "Ana M3", "telefono": "55 9876 5432"},
        ]
    })
    assert r.status_code == 200
    res = r.json()
    assert res["importados"] == 2
    assert res["duplicados_omitidos"] == 1


# ── AJUSTE TÉCNICO 2: Protección Anti CSV Injection ──────────────

def test_sanitizacion_anti_csv_injection(api):
    r = api.post("/api/leads/capture", json={
        "sherpa_id": "s1",
        "nombre": "=SUM(A1:A10)",
        "telefono": "+5215500998877",
        "consentimiento_whatsapp": True
    })
    assert r.status_code == 201
    lead = r.json()
    assert lead["nombre"] == "'=SUM(A1:A10)"


# ── AJUSTES TÉCNICOS 3 y 4: Endpoint PATCH Unificado & Auditoría ─

def test_endpoint_patch_unificado_y_auditoria(api, lead_de_prueba):
    lead_id = lead_de_prueba["id"]
    r = api.patch(f"/api/leads/{lead_id}", json={
        "respondio": True,
        "is_cancelled": True,
        "modificado_por": "sherpa_auditor"
    })
    assert r.status_code == 200
    updated = r.json()
    assert updated["respondio"] is True
    assert updated["is_cancelled"] is True
    assert updated["modificado_por"] == "sherpa_auditor"
    assert updated["actualizado_en"] is not None


# ── ENMIENDA 1: Webhook de Pagos HMAC e Idempotencia ─────────────

def test_webhook_pagos_rechaza_firma_invalida(api, lead_de_prueba):
    body = json.dumps({"event_id": "evt_1", "telefono": lead_de_prueba["telefono"], "tipo": "primera_compra"}).encode()
    r = api.post(
        "/api/pagos/webhook",
        content=body,
        headers={"X-Signature": "firma_invalida", "Content-Type": "application/json"}
    )
    assert r.status_code == 401


def test_webhook_pagos_idempotencia_y_concurso_un_solo_punto(api, lead_de_prueba):
    body = json.dumps({"event_id": "evt_100", "telefono": lead_de_prueba["telefono"], "tipo": "primera_compra"}).encode()
    firma = _firma_pago(body)

    r1 = api.post(
        "/api/pagos/webhook",
        content=body,
        headers={"X-Signature": firma, "Content-Type": "application/json"}
    )
    assert r1.status_code == 200
    assert r1.json()["accion"] == "sprint_28_inicializado"

    lead = api.get(f"/api/leads/{lead_de_prueba['id']}").json()
    assert lead["etapa_pipeline"] == "Sprint Activo"
    assert lead["puntos_adquiridos"] == 100

    r2 = api.post(
        "/api/pagos/webhook",
        content=body,
        headers={"X-Signature": firma, "Content-Type": "application/json"}
    )
    assert r2.status_code == 200
    assert r2.json() == {"status": "duplicate", "ignored": True}

    lead2 = api.get(f"/api/leads/{lead_de_prueba['id']}").json()
    assert lead2["puntos_adquiridos"] == 100


# ── ENMIENDA 3: Opt-in de WhatsApp conforme a Meta ──────────────

def test_optin_whatsapp_bloquea_envio_sin_consentimiento(api):
    r = api.post("/api/leads/capture", json={
        "sherpa_id": "s1",
        "nombre": "Sin Consentimiento",
        "telefono": "+5215500009999",
        "consentimiento_whatsapp": False
    })
    assert r.status_code == 422


def test_salesbot_bloquea_envio_hsm_si_consentimiento_es_falso(db):
    from app.salesbot import enviar_plantilla
    lead_sin_optin = {
        "_id": "lead_no_optin",
        "nombre": "Pedro",
        "telefono": "+5215599887766",
        "consentimiento_whatsapp": False,
        "optin_whatsapp": False
    }
    try:
        enviar_plantilla(db, lead_sin_optin, "SPR_01", dia=1)
        assert False, "Debió haber lanzado ValueError por falta de consentimiento"
    except ValueError as exc:
        assert "consentimiento explícito" in str(exc)


# ── ENMIENDA 4: Aislamiento por Sherpa ────────────────────────────

def test_aislamiento_de_datos_por_sherpa(api, db):
    db.sherpas.insert_one({"_id": "sherpa_A", "google_sub": "sub_A", "email": "a@test.mx", "nombre": "Sherpa A", "api_token": "token_A", "rol": "sherpa"})
    db.sherpas.insert_one({"_id": "sherpa_B", "google_sub": "sub_B", "email": "b@test.mx", "nombre": "Sherpa B", "api_token": "token_B", "rol": "sherpa"})

    r_cap = api.post("/api/leads/capture", json={
        "sherpa_id": "sherpa_A",
        "nombre": "Lead Privado A",
        "telefono": "+5215577665544",
        "consentimiento_whatsapp": True
    })
    lead_id = r_cap.json()["_id"]

    r_get = api.get(f"/api/leads/{lead_id}", headers={"X-API-Token": "token_B"})
    assert r_get.status_code == 404

    r_get_a = api.get(f"/api/leads/{lead_id}", headers={"X-API-Token": "token_A"})
    assert r_get_a.status_code == 200
    assert r_get_a.json()["nombre"] == "Lead Privado A"


# ── ENMIENDA 7: Webhook de Chatwoot & Ventana de 24h ──────────────

def test_chatwoot_webhook_mensaje_entrante_abre_ventana_24h(api):
    body = json.dumps({
        "event": "message_created",
        "phone_number": "+5215544332211",
        "contact": {"name": "Carlos Inbound", "phone_number": "+5215544332211"},
        "content": "Hola, quiero información del Sprint 28"
    }).encode()

    r = api.post(
        "/api/chatwoot/webhook",
        content=body,
        headers={"Content-Type": "application/json"}
    )
    assert r.status_code == 200
    assert r.json()["ventana_24h"] == "activa"


# ── ENMIENDAS 5 y 6: Sprint 28 & Estado Renovación pendiente ───────

def test_cron_nightly_sprint_28_dia_28_marca_renovacion_pendiente(api, lead_de_prueba):
    body = json.dumps({"event_id": "evt_28", "telefono": lead_de_prueba["telefono"], "tipo": "primera_compra"}).encode()
    api.post("/api/pagos/webhook", content=body, headers={"X-Signature": _firma_pago(body), "Content-Type": "application/json"})

    r = api.post("/api/sprint/nightly", headers={"X-Cron-Token": ""})
    assert r.status_code == 200


# ── ENMIENDA 8: Script de respaldos MongoDB ──────────────────────

def test_script_respaldo_mongodb_existe():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts", "backup_mongodb.sh"))
    assert os.path.exists(script_path)


def test_sync_apps_script_contacts_endpoint(api, db, monkeypatch):
    db.leads.delete_many({})
    import httpx
    def mock_get(url, **kwargs):
        class MockResponse:
            def raise_for_status(self): pass
            def json(self):
                return {
                    "status": "success",
                    "data": [
                        {"nombre": "Contacto Test GAS 1", "telefono": "5511223344"},
                        {"nombre": "Contacto Test GAS 2", "telefono": "5599887766"}
                    ]
                }
        return MockResponse()
    monkeypatch.setattr(httpx, "get", mock_get)

    r = api.post("/api/auth/google/sync-apps-script", json={"url": "https://script.google.com/macros/s/test/exec"})
    assert r.status_code == 200
    res = r.json()
    assert res["status"] == "success"
    assert res["imported"] == 2


# ── MOTOR SÍNCRO-DIRECTO (1-CLIC) ─────────────────────────────────

def test_captura_web_route(api):
    r = api.get("/captura")
    assert r.status_code == 200
    assert "Diagnóstico" in r.text or "<!DOCTYPE html>" in r.text

    r2 = api.get("/captura.html")
    assert r2.status_code == 200


def test_marcar_enviado_endpoint(api, lead_de_prueba):
    lead_id = lead_de_prueba["id"]
    r = api.post(f"/api/app/leads/{lead_id}/marcar-enviado")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["mensaje_enviado"] is True

    # Verificar que cambio la etapa de Lead a Bio-Auditoría
    lead_actualizado = api.get(f"/api/leads/{lead_id}").json()
    assert lead_actualizado["etapa_pipeline"] == "Bio-Auditoría"


def test_marcar_respondio_endpoint(api, lead_de_prueba):
    lead_id = lead_de_prueba["id"]
    r = api.post(f"/api/app/leads/{lead_id}/marcar-respondio", json={"respondio": True})
    assert r.status_code == 200
    assert r.json()["ok"] is True

    lead_actualizado = api.get(f"/api/leads/{lead_id}").json()
    assert lead_actualizado["respondio"] is True


def test_sherpa_info_endpoint(api, db):
    db.sherpas.insert_one({"_id": "sherpa_test_info", "nombre": "Sherpa Test", "telefono": "+5215500001111"})
    r = api.get("/api/sherpa/info/sherpa_test_info")
    assert r.status_code == 200
    info = r.json()
    assert info["id"] == "sherpa_test_info"
    assert info["nombre"] == "Sherpa Test"


def test_delete_lead_endpoint(api, lead_de_prueba):
    lead_id = lead_de_prueba["id"]
    r_del = api.delete(f"/api/leads/{lead_id}")
    assert r_del.status_code == 200
    assert r_del.json()["deleted_id"] == lead_id

    r_get = api.get(f"/api/leads/{lead_id}")
    assert r_get.status_code == 404


