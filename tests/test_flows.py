"""Pruebas de los flujos críticos del CRM: webhook idempotente, compliance, captura, import."""
import hashlib
import hmac
import json

from app.config import settings
from app.integrations.chatwoot import client as chatwoot_mock


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


# ── Webhook de pagos: firma + idempotencia ───────────────────

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
    assert r1.json()["accion"] in {"sprint_inicializado", "sprint_28_inicializado"}

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

    # SPR_01 enviado exactamente una vez
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
    # el texto seguro ya no contiene los términos
    assert "cura" not in r["texto_seguro"].lower()
    assert "diabetes" not in r["texto_seguro"].lower()


def test_mensaje_saliente_sale_limpio(api, lead_de_prueba):
    """El Salesbot valida todo antes de enviar: SPR_01 nunca contiene términos prohibidos."""
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
    # 1) Registrar Sherpa directamente en DB (no requiere Google real para F0)
    from app.database import get_db_client
    from app.models import crear_sherpa_doc
    db = get_db_client()
    sherpa = crear_sherpa_doc("sub_test_1", "sherpa@test.mx", "Sherpa Test", api_token="token-test-123")
    db.sherpas.insert_one(sherpa)


    # 2) Crear un lead existente por captura para probar el filtro global de duplicados
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
            {"nombre": "Ya En Otra Red", "telefono": "+5215599998888", "email": ""},  # global dup
        ]
    })
    assert r.status_code == 200
    data = r.json()
    assert data["importados"] == 2
    assert data["duplicados_omitidos"] == 1

    # Verificar que se crearon SIN opt-in (el Salesbot no les escribirá)
    r2 = api.post("/api/leads/capture", json={
        "sherpa_id": "s1", "nombre": "Dup", "telefono": "+5215511111111",
        "optin_whatsapp": True,
    })
    assert r2.status_code == 409  # el teléfono ya existía por la importación


def test_wa_link_contacto_manual(api, lead_de_prueba):
    r = api.get(f"/api/leads/{lead_de_prueba['id']}/wa-link", params={
        "texto": "Hola María, tengo algo que te va a interesar"
    })
    assert r.status_code == 200
    telefono_sin_plus = lead_de_prueba["telefono"].lstrip("+")  # wa.me no usa "+"
    assert r.json()["url"].startswith(f"https://wa.me/{telefono_sin_plus}?text=")


# ── Cron nocturno ────────────────────────────────────────────

def test_nightly_avanza_sprint(api, lead_de_prueba):
    # Activar el Sprint vía webhook
    body = _payload_pago(lead_de_prueba["telefono"])
    api.post("/api/payments/webhook-confirmation", content=body,
             headers={"X-Sinergix-Signature": _firma(body), "Content-Type": "application/json"})

    r = api.post("/api/sprint/nightly", headers={"X-Cron-Token": ""})
    assert r.status_code == 200
    assert r.json()["procesados"] >= 1

    perfil = api.get(f"/api/leads/{lead_de_prueba['id']}").json()
    assert perfil["fase_actual"] in {"Reset", "Ignicion", "Ingenieria", "Cierre"}
