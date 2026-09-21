"""Sinergix Negocio CRM — API FastAPI (Fase 0).

Rutas:
  POST /api/leads/capture              — captura desde landing (opt-in obligatorio)
  GET  /api/leads/{id}                 — perfil
  POST /api/leads/{id}/classify        — Los Cuatro Cincos
  POST /api/leads/{id}/send-to-external — CotizacionAPI → link de pago → WhatsApp
  POST /api/payments/webhook-confirmation — webhook firmado + idempotente
  POST /api/sprint/nightly             — cron nocturno del Sprint PH21
  GET  /health
"""
import hashlib
import hmac
import json
import secrets
from urllib.parse import quote
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db, init_db
from .integrations import biometria, chatwoot, cotizacion
import logging
import httpx

from .integrations.auth_google import (
    authorization_url, exchange_code, listar_contactos, refresh_access_token, userinfo,
)
from .models import ClasificacionCincos, EventoSprint, Lead, LinkPago, Sherpa, WebhookPagoLog
from .salesbot import bloquear_y_alertar, enviar_plantilla
from .schemas import (
    ClasificacionIn, ContactoIn, DatosComerciales, ImportContacts, LeadCapture, LeadOut, SherpaLoginIn,
)
from .sprint import procesar_noche

log = logging.getLogger("sinergix.main")

import os
from fastapi.responses import FileResponse

app = FastAPI(title="Sinergix Negocio CRM", version="0.3.0")


@app.on_event("startup")
def _startup() -> None:
    init_db()


@app.get("/")
def read_root():
    path_escritorio = r"c:\Users\andre\OneDrive\Escritorio\index.html"
    if os.path.exists(path_escritorio):
        return FileResponse(path_escritorio)
    return {"ok": True, "service": "sinergix-crm", "version": "0.3.0"}


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "sinergix-crm", "version": "0.3.0"}


# ── Autenticación API Sherpa (Equipo en Acción) ────────────────

def _ejecutar_login_sherpa(u: str, p: str, db: Session) -> dict:
    if not u or not p:
        raise HTTPException(400, "Usuario y contraseña requeridos")

    username = u.strip()
    password = p.strip()

    # Bypass modo test/desarrollo (resiliencia offline y pruebas automáticas)
    if username.lower() == "test" and password.lower() == "test":
        mock_token = "47886D49-0E71-4DA5-84AD-FC3E4A103467"
        sherpa = db.query(Sherpa).filter_by(google_sub="ea_102").first()
        if not sherpa:
            sherpa = Sherpa(
                google_sub="ea_102",
                email="holadenuevo@gmail.com",
                nombre="EDGAR ARTURO, FRIEVENTH MONDRAGON",
                api_token=mock_token,
                numero_distribuidor="102"
            )
            db.add(sherpa)
            db.commit()
            db.refresh(sherpa)

        user_obj = {
            "token": mock_token,
            "legacy_id": "102",
            "custid": "102",
            "name": sherpa.nombre,
            "sherpa_nombre": sherpa.nombre,
            "email": "holadenuevo@gmail.com",
            "phone": "+527223961746",
            "nickname": "EDG102"
        }

        return {
            "success": True,
            "ok": True,
            "user": user_obj,
            "token": mock_token,
            "sherpa_id": sherpa.id,
            "sherpa_nombre": sherpa.nombre,
            "sherpa_celular": "+527223961746",
            "custid": "102",
            "legacy_id": "102",
            "nickname": "EDG102"
        }

    urls = [
        f"https://equipoenaccion.net/ea_crm_app.asp?action=USERSINGIN&User={quote(username)}&Password={quote(password)}",
        f"https://equipoenaccion.app/ea_lab_login.asp?action=SINGIN&User={quote(username)}&Password={quote(password)}",
    ]

    for url_api in urls:
        try:
            resp = httpx.get(url_api, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                dataset = data.get("dataSet", [])
                if dataset and isinstance(dataset, list) and len(dataset) > 0:
                    first_item = dataset[0]
                    status_val = first_item.get("status")

                    # Diagnósticos deterministas del reporte técnico
                    if status_val == 2 or first_item.get("respuesta") == "CONTRASENA INVALIDA":
                        raise HTTPException(401, "Contraseña incorrecta")
                    if status_val == 3:
                        raise HTTPException(404, "Usuario no existente")

                    if status_val == 0 or "custid" in first_item or first_item.get("code") == "0":
                        custid = str(first_item.get("custid") or first_item.get("legacy_id") or "102")
                        name = (
                            first_item.get("customerName")
                            or first_item.get("name")
                            or first_item.get("firstname")
                            or username
                        )
                        email = first_item.get("mail") or first_item.get("email") or ""
                        phone = first_item.get("phone") or ""
                        token = first_item.get("token") or "47886D49-0E71-4DA5-84AD-FC3E4A103467"
                        nickname = first_item.get("nickname") or ""
                        url_foto = first_item.get("urlFoto") or ""

                        if phone and not phone.startswith("+"):
                            phone = f"+52{phone}"

                        sherpa = db.query(Sherpa).filter(
                            (Sherpa.email == email) | (Sherpa.numero_distribuidor == custid)
                        ).first()

                        if not sherpa:
                            sherpa = Sherpa(
                                google_sub=f"ea_{custid}",
                                email=email,
                                nombre=name,
                                api_token=token if token else secrets.token_urlsafe(32),
                                numero_distribuidor=custid
                            )
                            db.add(sherpa)
                        else:
                            sherpa.nombre = name
                            sherpa.numero_distribuidor = custid
                            if token:
                                sherpa.api_token = token
                        db.commit()
                        db.refresh(sherpa)

                        user_obj = {
                            "token": sherpa.api_token,
                            "legacy_id": custid,
                            "custid": custid,
                            "name": sherpa.nombre,
                            "sherpa_nombre": sherpa.nombre,
                            "email": sherpa.email,
                            "phone": phone,
                            "urlFoto": url_foto,
                            "nickname": nickname
                        }

                        return {
                            "success": True,
                            "ok": True,
                            "user": user_obj,
                            "token": sherpa.api_token,
                            "sherpa_id": sherpa.id,
                            "sherpa_nombre": sherpa.nombre,
                            "sherpa_celular": phone,
                            "custid": custid,
                            "legacy_id": custid,
                            "nickname": nickname
                        }
        except HTTPException:
            raise
        except Exception as exc:
            log.warning("Fallo al conectar con URL %s: %s", url_api, exc)

    raise HTTPException(401, "Contraseña incorrecta")


@app.post("/api/auth/login")
@app.post("/api/login")
def login_sherpa_post(payload: SherpaLoginIn, db: Session = Depends(get_db)):
    u = payload.user or payload.User or payload.username or payload.Username
    p = payload.password or payload.Password
    return _ejecutar_login_sherpa(u, p, db)


@app.get("/api/auth/login")
@app.get("/api/login")
def login_sherpa_get(
    user: str = "",
    password: str = "",
    User: str = "",
    Password: str = "",
    username: str = "",
    db: Session = Depends(get_db),
):
    u = user or User or username
    p = password or Password
    return _ejecutar_login_sherpa(u, p, db)


# ── Autenticación Google (Sherpas) + contactos ────────────────

# states OAuth en memoria (F0; en producción mover a Redis con TTL)
_estados_oauth: dict[str, bool] = {}


@app.get("/api/auth/google/login")
def google_login():
    """Devuelve la URL de consentimiento de Google (contacts incluido)."""
    state = secrets.token_urlsafe(24)
    _estados_oauth[state] = True
    return {"authorization_url": authorization_url(state), "state": state}


@app.get("/api/auth/google/callback")
def google_callback(code: str = "", state: str = "", error: str = "", db: Session = Depends(get_db)):
    if error:
        raise HTTPException(400, f"Autorización denegada por Google: {error}")
    if state not in _estados_oauth:
        raise HTTPException(400, "State OAuth inválido o expirado")
    del _estados_oauth[state]

    tokens = exchange_code(code)
    info = userinfo(tokens["access_token"])

    sherpa = db.query(Sherpa).filter_by(google_sub=info["sub"]).first()
    if not sherpa:
        sherpa = Sherpa(
            google_sub=info["sub"],
            email=info.get("email", ""),
            nombre=info.get("name", ""),
            api_token=secrets.token_urlsafe(32),
        )
    # refresh_token: Google solo lo manda la primera vez — conservar el existente
    sherpa.google_refresh_token = tokens.get("refresh_token") or sherpa.google_refresh_token
    sherpa.google_access_token = tokens.get("access_token")
    db.add(sherpa)
    db.commit()
    db.refresh(sherpa)
    return {
        "sherpa_id": sherpa.id,
        "email": sherpa.email,
        "nombre": sherpa.nombre,
        "api_token": sherpa.api_token,
        "acceso_contactos": sherpa.google_refresh_token is not None,
    }


def _sherpa_por_token(db: Session, x_api_token: str) -> Sherpa:
    sherpa = db.query(Sherpa).filter_by(api_token=x_api_token).first()
    if not sherpa:
        raise HTTPException(401, "Token de Sherpa inválido")
    return sherpa


@app.get("/api/auth/google/contacts")
def google_contacts(
    x_api_token: str = Header(default=""),
    page_token: str = "",
    db: Session = Depends(get_db),
):
    sherpa = _sherpa_por_token(db, x_api_token)
    if not sherpa.google_refresh_token:
        raise HTTPException(409, "Este Sherpa aún no autorizó el acceso a sus contactos")
    access = refresh_access_token(sherpa.google_refresh_token)
    data = listar_contactos(access, page_token=page_token or None)
    return {"sherpa": sherpa.email, **data}


@app.post("/api/leads/import-contacts")
def import_contacts(
    payload: ImportContacts,
    x_api_token: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """Importa contactos de Google al CRM para clasificarlos en Los Cuatro Cincos.

    IMPORTANTE: los contactos importados se crean con optin_whatsapp=False.
    El Salesbot NO les escribirá automáticamente. El Sherpa los contacta manual
    con el guion de su lista vía el enlace wa.me (WhatsApp personal), respetando
    la política de Meta hasta que el lead dé su opt-in.
    """
    sherpa = _sherpa_por_token(db, x_api_token)
    creados, duplicados = 0, 0
    for contacto in payload.contactos:
        if not contacto.telefono:
            continue
        # El teléfono es único GLOBAL (una persona = un perfil, sea de quien sea la red)
        existe = db.query(Lead).filter_by(telefono=contacto.telefono).first()
        if existe:
            duplicados += 1
            continue
        db.add(
            Lead(
                sherpa_id=sherpa.id,
                nombre=contacto.nombre or contacto.telefono,
                telefono=contacto.telefono,
                email=contacto.email or "",
                canal_captacion="importacion_contactos",
                optin_whatsapp=False,
            )
        )
        creados += 1
    db.commit()
    return {
        "importados": creados,
        "duplicados_omitidos": duplicados,
        "nota": "Importados sin opt-in: contacto manual vía /api/leads/{id}/wa-link",
    }


@app.get("/api/leads/{lead_id}/wa-link")
def wa_link(lead_id: str, texto: str = "", db: Session = Depends(get_db)):
    """Enlace wa.me para contacto MANUAL del Sherpa (WhatsApp personal).

    Para leads sin opt-in (contactos importados) — el guion sugerido debe venir
    de Los Cuatro Cincos y estar validado con SafetyEngine.
    """
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")
    url = f"https://wa.me/{lead.telefono.lstrip('+')}"
    if texto:
        url += f"?text={quote(texto)}"
    return {
        "url": url,
        "optin_whatsapp": lead.optin_whatsapp,
        "aviso": (
            "Contacto manual desde el WhatsApp personal del Sherpa. "
            "No envía el CRM ni el Salesbot."
        ),
    }


# ── Captación de leads ───────────────────────────────────────────

@app.post("/api/leads/capture", response_model=LeadOut, status_code=201)
def capture(payload: LeadCapture, db: Session = Depends(get_db)):
    existente = db.query(Lead).filter_by(telefono=payload.telefono).first()
    if existente:
        raise HTTPException(409, "El teléfono ya está registrado en el CRM")

    lead = Lead(
        sherpa_id=payload.sherpa_id,
        nombre=payload.nombre,
        telefono=payload.telefono,
        email=payload.email or "",
        canal_captacion=payload.canal_captacion,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        landing_id=payload.landing_id,
        optin_whatsapp=payload.optin_whatsapp,
        optin_fecha=datetime.now(timezone.utc) if payload.optin_whatsapp else None,
        optin_origen="landing" if payload.canal_captacion == "landing" else payload.canal_captacion,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


# ── Perfil y clasificación ───────────────────────────────────────

@app.get("/api/leads/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: str, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")
    return lead


@app.post("/api/leads/{lead_id}/classify")
def classify(lead_id: str, payload: ClasificacionIn, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")
    reg = ClasificacionCincos(lead_id=lead.id, lista=payload.lista, nota=payload.nota)
    db.add(reg)
    db.commit()
    return {"ok": True, "lista": payload.lista}


# ── Link de pago (CotizacionAPI → WhatsApp) ─────────────────────

@app.post("/api/leads/{lead_id}/send-to-external")
def send_to_external(
    lead_id: str, datos: DatosComerciales, db: Session = Depends(get_db)
):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")
    if not lead.optin_whatsapp:
        raise HTTPException(409, "El lead no tiene opt-in de WhatsApp: no se puede enviar el link")

    key = cotizacion.nuevo_idempotency_key()
    payload_externo = {
        "nombre": lead.nombre,
        "apellido1": lead.apellido1,
        "apellido2": lead.apellido2,
        "telefono": lead.telefono,
        "email": lead.email,
        **datos.model_dump(),
    }
    try:
        respuesta = cotizacion.solicitar_link_pago(payload_externo, key, tipo="primera_compra")
    except Exception as exc:  # sistema externo caído → el Sherpa reintenta luego
        raise HTTPException(502, f"Sistema externo de cotización no disponible: {exc}") from exc

    link = LinkPago(
        lead_id=lead.id,
        tipo="primera_compra",
        checkout_url=respuesta["checkout_url"],
        estado="enviado",
        idempotency_key=key,
    )
    db.add(link)
    db.flush()

    lead.link_pago_activo_id = link.id
    lead.etapa_pipeline = "Datos Enviados"
    lead.calle = datos.calle
    lead.numero_exterior = datos.numero_exterior
    lead.numero_interior = datos.numero_interior
    lead.colonia = datos.colonia
    lead.codigo_postal = datos.codigo_postal
    lead.ciudad_municipio = datos.ciudad_municipio
    lead.estado = datos.estado
    lead.pais = datos.pais
    lead.distribuidor_patrocinador_id = datos.distribuidor_patrocinador_id
    lead.posicion_red = datos.posicion_red
    db.commit()
    db.refresh(lead)

    # Envío del link (texto validado por SafetyEngine antes de salir)
    enviar_plantilla(db, lead, "LINK_PAGO", {"link": link.checkout_url}, dia=0)

    return {"ok": True, "link": {"id": link.id, "checkout_url": link.checkout_url, "estado": link.estado}}


# ── Webhook de pagos (firma HMAC + idempotencia) ────────────────

@app.post("/api/payments/webhook-confirmation")
async def webhook_confirmation(
    request: Request,
    x_sinergix_signature: str = Header(default=""),
    db: Session = Depends(get_db),
):
    raw = await request.body()

    # 1) Firma HMAC-SHA256 del body crudo
    esperada = hmac.new(
        settings.payment_webhook_secret.encode(), raw, hashlib.sha256
    ).hexdigest()
    firma_valida = hmac.compare_digest(esperada, x_sinergix_signature)

    payload_hash = hashlib.sha256(raw).hexdigest()

    # 2) Idempotencia: si el payload ya se procesó, responder sin reprocesar
    if db.query(WebhookPagoLog).filter_by(payload_hash=payload_hash).first():
        return {"status": "duplicate", "ignored": True}

    db.add(WebhookPagoLog(firma_valida=firma_valida, payload_hash=payload_hash))
    db.commit()

    if not firma_valida:
        raise HTTPException(401, "Firma del webhook inválida")

    data = json.loads(raw)
    telefono = data.get("telefono", "")
    tipo = data.get("tipo", "primera_compra")

    lead = db.query(Lead).filter_by(telefono=telefono).first()
    if not lead:
        raise HTTPException(404, "Lead no encontrado para el teléfono del webhook")

    # Marcar el link como pagado
    if lead.link_pago_activo_id:
        link = db.get(LinkPago, lead.link_pago_activo_id)
        if link:
            link.estado = "pagado"
            link.fecha_pagado = datetime.now(timezone.utc)

    # Acreditar puntos (idempotente: solo ocurre una vez por payload)
    lead.puntos_adquiridos += settings.puntos_por_plan

    if tipo == "renovacion":
        lead.etapa_pipeline = "Renovación"
        lead.ciclos_renovados += 1
        lead.dia_actual_sprint = 0
        lead.sprint_reconstrucciones = 0
        enviar_plantilla(db, lead, "DIA_28", {"link_renovacion": ""}, dia=28)
        db.commit()
        return {"status": "processed", "accion": "renovacion_registrada", "lead": lead.id}

    # Primera compra: inicializar Sprint
    lead.etapa_pipeline = "Sprint Activo"
    lead.dia_actual_sprint = 1
    lead.fase_actual = "Reset"
    lead.sprint_inicio = datetime.now(timezone.utc)

    # Cartera de salud en Sinergix Salud (Firestore vía BiometriaAPI)
    biometria.registrar_ascendan(
        lead.id,
        {"nombre": lead.nombre, "telefono": lead.telefono, "sherpa_id": lead.sherpa_id},
    )

    # Baseline inicial (mock hasta que BiometriaAPI real exista)
    resumen = biometria.get_resumen(lead.id, dia=1)
    lead.hrv_baseline = int(resumen.get("hrv", 46))
    lead.ultima_sincronizacion_biometrica = biometria.ahora()

    enviar_plantilla(db, lead, "SPR_01", dia=1)
    db.commit()
    db.refresh(lead)
    return {"status": "processed", "accion": "sprint_inicializado", "lead": lead.id}


# ── Cron nocturno del Sprint ─────────────────────────────────────

@app.post("/api/sprint/nightly")
def nightly(x_cron_token: str = Header(default=""), db: Session = Depends(get_db)):
    if settings.cron_token and x_cron_token != settings.cron_token:
        raise HTTPException(401, "Token de cron inválido")

    activos = db.query(Lead).filter(Lead.etapa_pipeline == "Sprint Activo").all()
    resultado = []
    for lead in activos:
        if not lead.sprint_inicio:
            continue
        inicio = lead.sprint_inicio
        if inicio.tzinfo is None:  # SQLite devuelve naive — normalizar a UTC
            inicio = inicio.replace(tzinfo=timezone.utc)
        dias_calendario = (datetime.now(timezone.utc) - inicio).days + 1
        lead.dia_actual_sprint = dias_calendario

        resumen = biometria.get_resumen(lead.id, dia=dias_calendario)
        estado = procesar_noche(dias_calendario, lead.sprint_reconstrucciones, resumen)

        if estado.reconstruccion:
            lead.sprint_reconstrucciones += 1
            db.add(
                EventoSprint(
                    lead_id=lead.id,
                    dia=dias_calendario,
                    tipo_evento="reconstruccion",
                    payload={"motivo": "sin datos biométricos del día"},
                )
            )
        lead.fase_actual = estado.fase
        lead.adherencia_acumulada = round(
            float(lead.adherencia_acumulada or 0) * 0.7 + estado.adherencia_dia * 0.3, 2
        )
        lead.ultima_sincronizacion_biometrica = biometria.ahora()

        # Hito Día 7: adherencia baja → bloquear bot + escalar a llamada
        if 7 in estado.hitos_disparados and lead.adherencia_acumulada < 60:
            bloquear_y_alertar(db, lead, "adherencia<60% en Día 7 — bot bloqueado", dia=7)
            resultado.append({"lead": lead.id, "evento": "alerta_dia7"})
            continue

        # Recordatorio de sincronización (48 h sin datos)
        if not estado.registrado and dias_calendario % 2 == 0:
            enviar_plantilla(db, lead, "SYNC_RECORDATORIO", dia=dias_calendario)

        # Hitos con plantilla
        for hito_dia, plantilla in {
            7: "SPR_02", 14: "SPR_03", 21: "SPR_04", 25: "SPR_05"
        }.items():
            if hito_dia in estado.hitos_disparados:
                variables = {
                    "hrv_actual": "—",
                    "adherencia": f"{lead.adherencia_acumulada:.0f}",
                    "hrv_delta": "+6",
                    "fc_delta": "-3",
                    "sueno_delta": "+0.8",
                    "fecha_sugerida": "mañana",
                    "fecha_dia28": "este sábado",
                    "link_renovacion": "",
                }
                enviar_plantilla(db, lead, plantilla, variables, dia=hito_dia)
                resultado.append({"lead": lead.id, "hito": hito_dia, "plantilla": plantilla})

        # Día 28 efectivo: generar link de renovación
        if 28 in estado.hitos_disparados:
            key = cotizacion.nuevo_idempotency_key()
            resp = cotizacion.solicitar_link_pago(
                {"telefono": lead.telefono, "nombre": lead.nombre}, key, tipo="renovacion"
            )
            link = LinkPago(
                lead_id=lead.id, tipo="renovacion",
                checkout_url=resp["checkout_url"], estado="enviado", idempotency_key=key,
            )
            db.add(link)
            db.flush()
            lead.link_pago_activo_id = link.id
            enviar_plantilla(db, lead, "DIA_28", {"link_renovacion": link.checkout_url}, dia=28)
            resultado.append({"lead": lead.id, "evento": "link_renovacion_generado"})

        db.commit()

    return {"status": "ok", "procesados": len(activos), "eventos": resultado}
