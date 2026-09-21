"""Pruebas de los flujos críticos del CRM: webhook idempotente, compliance, captura, import, opt-in, aislamiento."""
import hashlib
import hmac
import json
import pytest

from app.config import settings
from app.integrations.chatwoot import client as chatwoot_mock
from app.safety import validar_optin_whatsapp


def _firma(body: bytes) -> str:
    return hmac.new(settings.payment_webhook_secret.encode(), body, hashlib.sha256).hexdigest()


# ── Captura de leads ─────────────────────────────────────────

def test_capture_crea_lead_con_optin(api):
    r = api.post("/api/leads/capture", json={
        "sherpa_id": "s1", "nombre": "Juan", "telefono": "+5215500000001",
        "optin_whatsapp": True,
    })
    assert r.status_code == 201
    assert r.json()["etapa_pipeline"] == "Lead"
    assert r.json()["optin_whatsapp"] is True


def test_capture_rechaza_sin_optin(api):
    r = api.post("/api/leads/capture", json={
        "sherpa_id": "s1", "nombre": "Ana", "telefono": "+5215500000002",
        "optin_whatsapp": False,
    })
    assert r.status_code == 422  # el consentimiento es obligatorio


# ── Webhook de pagos: firma + idempotencia (Enmienda 1 CRÍTICA) ────────

def _payload_pago(telefono: str) -> bytes:
    return json.dumps({"telefono": telefono, "tipo": "primera_compra"}).encode()


def test_webhook_procesa_una_sola_vez(api, lead_de_prueba):
    body = _payload_pago(lead_de_prueba["telefono"])
    firma = _firma(body)
    chatwoot_mock.enviados.clear()

    r1 = api.post(
        "/api/payments/webhook-confirmation",
        content=body,
        headers={"X-Sinergix-Signature": firma, "Content-Type": "application/json"},
    )
    assert r1.status_code == 200
    assert r1.json()["accion"] == "sprint_inicializado"

    perfil = api.get(f"/api/leads/{lead_de_prueba['id']}").json()
    assert perfil["etapa_pipeline"] == "Sprint Activo"
    assert perfil["dia_actual_sprint"] == 1
    assert perfil["fase_actual"] == "Reset"
    assert perfil["puntos_adquiridos"] == 100

    # Reintento del procesador (mismo payload) → idempotente
    r2 = api.post(
        "/api/payments/webhook-confirmation",
        content=body,
        headers={"X-Sinergix-Signature": firma, "Content-Type": "application/json"},
    )
    assert r2.status_code == 200
    assert r2.json() == {"status": "duplicate", "ignored": True}

    perfil2 = api.get(f"/api/leads/{lead_de_prueba['id']}").json()
    assert perfil2["puntos_adquiridos"] == 100  # sin doble acreditación

    spr01 = [m for m in chatwoot_mock.enviados if m["plantilla"] == "SPR_01"]
    assert len(spr01) == 1


def test_webhook_rechaza_firma_invalida(api, lead_de_prueba):
    body = _payload_pago(lead_de_prueba["telefono"])
    r = api.post(
        "/api/payments/webhook-confirmation",
        content=body,
        headers={"X-Sinergix-Signature": "firma-falsa", "Content-Type": "application/json"},
    )
    assert r.status_code == 401


def test_pagos_webhook_hmac_idempotencia(api, lead_de_prueba):
    """Enmienda 1: /api/pagos/webhook con firma X-Signature e idempotencia de event_id."""
    payload = json.dumps({
        "event_id": "evt_test_1001",
        "lead_id": lead_de_prueba["id"],
        "tipo_evento": "invitacion",
        "ventana": "2026-Q3"
    }).encode("utf-8")
    
    firma = _firma(payload)

    # 1. Envió con firma inválida debe ser 401
    r_bad = api.post("/api/pagos/webhook", content=payload, headers={"X-Signature": "invalida"})
    assert r_bad.status_code == 401

    # 2. Envío legítimo debe ser 200 y acreditar 1 punto
    r_ok = api.post("/api/pagos/webhook", content=payload, headers={"X-Signature": firma})
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "success"
    assert r_ok.json()["puntos_acreditados"] == 1

    # 3. Reintento duplicado debe responder 200 OK con already_processed y 0 puntos adicionales
    r_dup = api.post("/api/pagos/webhook", content=payload, headers={"X-Signature": firma})
    assert r_dup.status_code == 200
    assert r_dup.json()["status"] == "already_processed"
    assert r_dup.json()["puntos_acreditados"] == 0


# ── Opt-in WhatsApp Guard (Enmienda 3) ──────────────────────────

def test_optin_whatsapp_guard_bloqueo():
    """SafetyEngine bloquea envíos sin opt-in implícito/explícito."""
    lead_sin_optin = {"nombre": "No Optin", "consentimiento_whatsapp": False}
    with pytest.raises(ValueError) as exc:
        validar_optin_whatsapp(lead_sin_optin)
    assert "consentimiento" in str(exc.value)

    lead_con_optin = {"nombre": "Con Optin", "consentimiento_whatsapp": True}
    assert validar_optin_whatsapp(lead_con_optin) is True


# ── Link de pago (flujo comercial) ───────────────────────────

def test_send_to_external_genera_link(api, lead_de_prueba):
    lead_id = lead_de_prueba["id"]
    r = api.post(f"/api/leads/{lead_id}/send-to-external", json={
        "calle": "Av. Siempre Viva", "numero_exterior": "742",
        "colonia": "Centro", "codigo_postal": "64000",
        "ciudad_municipio": "Monterrey", "estado": "Nuevo León",
        "distribuidor_patrocinador_id": "EEA-12345",
        "posicion_red": "derecho",
    })
    assert r.status_code == 200
    assert r.json()["link"]["estado"] == "enviado"

    perfil = api.get(f"/api/leads/{lead_id}").json()
    assert perfil["etapa_pipeline"] == "Datos Enviados"
    assert "checkout" in perfil["link_pago_activo_id"] or perfil["link_pago_activo_id"]


# ── SafetyEngine ─────────────────────────────────────────────

def test_safety_bloquea_lenguaje_prohibido(api):
    from app.safety import validate
    r = validate("Esto cura la diabetes y quema la grasa garantizado")
    assert not r["ok"]
    categorias = {h["categoria"] for h in r["hallazgos"]}
    assert "atribución terapéutica" in categorias
    assert "mención de enfermedad" in categorias
    assert "cura" not in r["texto_seguro"].lower()
    assert "diabetes" not in r["texto_seguro"].lower()


def test_mensaje_saliente_sale_limpio(api, lead_de_prueba):
    from app.salesbot import TEMPLATES
    from app.safety import validate
    for nombre, texto in TEMPLATES.items():
        r = validate(texto.format(nombre="María", link="https://x.test", hrv_actual="52",
                                  adherencia="80", hrv_delta="+6", fc_delta="-3",
                                  sueno_delta="+0.8", fecha_sugerida="mañana",
                                  fecha_dia28="sábado", link_renovacion="https://x.test/r"))
        assert r["ok"], f"Plantilla {nombre} tiene lenguaje prohibido: {r['hallazgos']}"


# ── Importación de contactos de Google ───────────────────────

def test_import_contactos_sin_optin(api):
    from app.db import SessionLocal
    from app.models import Sherpa
    db = SessionLocal()
    sherpa = Sherpa(google_sub="sub_test_1", email="sherpa@test.mx",
                    nombre="Sherpa Test", api_token="token-test-123")
    db.add(sherpa)
    db.commit()
    db.close()

    r_pre = api.post("/api/leads/capture", json={
        "sherpa_id": "s1", "nombre": "Ya Existe", "telefono": "+5215599998888",
        "optin_whatsapp": True,
    })
    assert r_pre.status_code == 201

    headers = {"x-api-token": "token-test-123"}
    r = api.post("/api/leads/import-contacts", headers=headers, json={
        "contactos": [
            {"nombre": "Tío Beto", "telefono": "+5215511111111", "email": ""},
            {"nombre": "vecina Lucy", "telefono": "+5215522222222", "email": "lucy@test.mx"},
            {"nombre": "Ya En Otra Red", "telefono": "+5215599998888", "email": ""},
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["importados"] == 2
    assert data["duplicados_omitidos"] == 1

    r2 = api.post("/api/leads/capture", json={
        "sherpa_id": "s1", "nombre": "Dup", "telefono": "+5215511111111",
        "optin_whatsapp": True,
    })
    assert r2.status_code == 409


def test_wa_link_contacto_manual(api, lead_de_prueba):
    r = api.get(f"/api/leads/{lead_de_prueba['id']}/wa-link", params={
        "texto": "Hola María, tengo algo que te va a interesar"
    })
    assert r.status_code == 200
    telefono_sin_plus = lead_de_prueba["telefono"].lstrip("+")
    assert r.json()["url"].startswith(f"https://wa.me/{telefono_sin_plus}?text=")


# ── Cron nocturno ────────────────────────────────────────────

def test_nightly_avanza_sprint(api, lead_de_prueba):
    body = _payload_pago(lead_de_prueba["telefono"])
    api.post("/api/payments/webhook-confirmation", content=body,
             headers={"X-Sinergix-Signature": _firma(body), "Content-Type": "application/json"})

    r = api.post("/api/sprint/nightly", headers={"X-Cron-Token": ""})
    assert r.status_code == 200
    assert r.json()["procesados"] >= 1

    perfil = api.get(f"/api/leads/{lead_de_prueba['id']}").json()
    assert perfil["fase_actual"] in {"Reset", "Ignicion", "Ingenieria", "Cierre"}


# ── Autenticación de Sherpas ─────────────────────────────────

def test_login_sherpa_api_exito(api):
    r = api.post("/api/login", json={"username": "Test", "password": "Test"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["ok"] is True
    assert data["custid"] == "102"
    assert data["user"]["token"] == "47886D49-0E71-4DA5-84AD-FC3E4A103467"


def test_login_sherpa_api_auth_login_endpoint(api):
    r = api.post("/api/auth/login", json={"user": "Test", "password": "Test"})
    assert r.status_code == 200
    data = r.json()
    assert data["success"] is True
    assert data["custid"] == "102"


def test_login_sherpa_api_incorrecto(api):
    r = api.post("/api/login", json={"username": "UsuarioInexistenteXYZ", "password": "BadPassword123"})
    assert r.status_code in (401, 404)
    detail = r.json()["detail"]
    assert detail in ("Contraseña incorrecta", "Usuario no existente", "CONTRASENA INVALIDA")
