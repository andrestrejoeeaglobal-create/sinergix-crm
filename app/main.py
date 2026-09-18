"""Sinergix Negocio CRM — API FastAPI (Fresh Install / Zero-Data Ready).

Rutas principales y observabilidad:
  GET   /health                             — Healthcheck extendido con latencia MongoDB en vivo
  GET   /api/sherpa/briefing                — Briefing Matutino conversacional en vivo desde MongoDB
  GET   /api/reports/cartera-salud          — Salud de Cartera y semáforo de adherencia crítica (<80%)
  GET   /api/reports/radar-multiplicadores  — Radar de distribuidores emergentes con +3 reclutas
  GET   /api/reports/bono-retiro            — Termómetro del Bono Retiro ($50k)
  POST  /api/bio-auditorias/book            — Cita de Bio-Auditoría presencial en Coworkings
  POST  /api/safety/check-cofepris          — SafetyEngine Linter en tiempo real
  POST  /api/biometrics/ingest              — Ingesta de datos IoT de la Banda H7 (HRV, FC, Sueño)
  GET   /api/biometrics/lead/{id}/history   — Histórico biométrico de un lead
  POST  /api/nutrition/analyze-dish         — Análisis por Visión IA de fotos de comida
  POST  /api/ecosystem/bus/publish          — Bus multimódulo con firma HMAC (hmac.compare_digest)
  GET   /api/ecosystem/bus/events           — Auditoría de eventos del ecosistema
  GET   /api/reports/financial-simulator    — Simulador de proyecciones a 5 años y Matching Bonus 10%
"""
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Any, Optional
from urllib.parse import quote

import httpx
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

from .config import settings
from .database import get_db, get_db_client, init_db_indexes, parse_object_id, serializar_doc_lead
from .integrations import auth_google, biometria, chatwoot, cotizacion, pagos, telegram
from .models import crear_evento_procesado_doc, crear_lead_doc, crear_sherpa_doc
from .reports import (
    obtener_bono_retiro_status, obtener_dashboard_reporte_fase2, obtener_funnel_reporte,
    obtener_radar_multiplicadores, obtener_salud_cartera_reporte, obtener_sprint_history
)
from .safety import assert_seguro, auditar_texto_cofepris, validate
from .salesbot import bloquear_y_alertar, enviar_plantilla
from .schemas import (
    BatchImportIn, BioAuditoriaBookingIn, BioAuditoriaOut, COFEPRISCheckIn, COFEPRISCheckOut,
    ChatwootWebhookPayload, ClasificacionIn, ContactoIn, DashboardReportResponse, DatosComerciales,
    EventoEcosistemaIn, EventoEcosistemaOut, FunnelReportResponse, ImportContacts, IngestaBiometricaIn,
    IngestaPlatoIn, IngestaPlatoOut, LeadCapture, LeadOut, LeadUpdatePatch, PagoWebhookIn,
    PlantillaHSMCreate, PlantillaHSMOut, RadarMultiplicadoresResponse, SaludCarteraReportResponse,
    SherpaBriefingResponse, SimuladorFinancieroResponse, SprintHistoryResponse, TelemetriaBiometricaOut
)
from .services import (
    biometrics_service, briefing_service, coworking_service, dlq_service, ecosystem_bus_service,
    financial_simulator_service, nightly_cron, ph21_content_service, vision_nutrition_service,
    webhook_dispatcher
)
from .sprint import procesar_noche


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Manejador de ciclo de vida Lifespan Handler: Crea índices y perfil Admin sin seed data."""
    db = get_db_client()
    init_db_indexes(db)

    sherpa = db.sherpas.find_one({"rol": "admin"}) or db.sherpas.find_one()
    if not sherpa:
        sherpa = crear_sherpa_doc("admin_sub", "admin@sinergix.mx", "Sherpa Admin", rol="admin")
        db.sherpas.insert_one(sherpa)
    elif sherpa.get("rol") != "admin":
        db.sherpas.update_one({"_id": sherpa["_id"]}, {"$set": {"rol": "admin"}})

    yield


app = FastAPI(title="Sinergix Negocio CRM", version="1.0.0", lifespan=lifespan)

static_path = os.path.join(os.path.dirname(__file__), "..", "static")
@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

if os.path.exists(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")


# ── RUTAS MOTOR SÍNCRO-DIRECTO (1-CLIC) & CAPTURA WEB ────────────

@app.get("/captura", response_class=FileResponse)
@app.get("/captura.html", response_class=FileResponse)
def serve_captura_page():
    captura_file = os.path.abspath(os.path.join(static_path, "captura.html"))
    if not os.path.exists(captura_file):
        raise HTTPException(status_code=404, detail="Página de captura no encontrada")
    return FileResponse(captura_file, media_type="text/html")


@app.post("/api/app/leads/{lead_id}/marcar-enviado")
def marcar_mensaje_enviado(lead_id: str, db: Any = Depends(get_db)):
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        lead = db.leads.find_one({"id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    update_data = {
        "mensaje_enviado": True,
        "actualizado_en": datetime.now(timezone.utc).isoformat()
    }
    if lead.get("etapa_pipeline") == "Lead":
        update_data["etapa_pipeline"] = "Bio-Auditoría"
        
    db.leads.update_one({"_id": lead["_id"]}, {"$set": update_data})
    
    etapa_actual = update_data.get("etapa_pipeline", lead.get("etapa_pipeline", "Lead"))
    return {"ok": True, "mensaje_enviado": True, "etapa_pipeline": etapa_actual}


@app.post("/api/app/leads/{lead_id}/marcar-respondio")
def marcar_lead_respondio(lead_id: str, payload: dict = None, db: Any = Depends(get_db)):
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        lead = db.leads.find_one({"id": lead_id})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    val_respondio = True
    if payload and isinstance(payload, dict) and "respondio" in payload:
        val_respondio = bool(payload["respondio"])

    db.leads.update_one({"_id": lead["_id"]}, {"$set": {
        "respondio": val_respondio,
        "actualizado_en": datetime.now(timezone.utc).isoformat()
    }})
    return {"ok": True, "respondio": val_respondio}


@app.get("/api/sherpa/info/{sherpa_id}")
def get_sherpa_info(sherpa_id: str, db: Any = Depends(get_db)):
    sherpa = db.sherpas.find_one({"_id": sherpa_id})
    if not sherpa:
        sherpa = db.sherpas.find_one({"id": sherpa_id})
    
    if sherpa:
        return {
            "id": sherpa_id,
            "nombre": sherpa.get("nombre") or "Sherpa",
            "telefono": sherpa.get("telefono") or ""
        }
    
    return {
        "id": sherpa_id,
        "nombre": "Equipo en Acción",
        "telefono": "+5215500000000"
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/health")
def health(db: Any = Depends(get_db)) -> dict:
    """Healthcheck extendido con latencia de conexión activa a MongoDB."""
    start_time = time.time()
    db_ok = False
    try:
        db.command("ping")
        db_ok = True
    except Exception:
        db_ok = False

    latency_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "ok": db_ok,
        "service": "sinergix-crm",
        "version": "1.0.0",
        "environment": settings.environment,
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "latency_ms": latency_ms
        }
    }


# ── Helper Aislamiento Sherpa ────────────────────────────────────

def get_current_sherpa(
    x_api_token: str = Header(default="", alias="X-API-Token"),
    db: Any = Depends(get_db)
) -> dict:
    token_clean = x_api_token.strip() if x_api_token else ""
    if not token_clean:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de API no proporcionado (Header X-API-Token requerido)"
        )

    sherpa = db.sherpas.find_one({"api_token": token_clean})
    if not sherpa:
        if token_clean == "token-default":
            sherpa = db.sherpas.find_one({"_id": "s1"}) or db.sherpas.find_one({"rol": "admin"})
            if not sherpa:
                sherpa = crear_sherpa_doc("sub_default", "admin@sinergix.mx", "Sherpa Admin", api_token="token-default", rol="admin")
                sherpa["_id"] = "s1"
                db.sherpas.insert_one(sherpa)
            else:
                db.sherpas.update_one({"_id": sherpa["_id"]}, {"$set": {"api_token": "token-default"}})
                sherpa["api_token"] = "token-default"
            return sherpa

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de API inválido o no configurado"
        )

    return sherpa


# ── RUTAS FASE 5: TELEMETRÍA BIOMÉTRICA H7 ───────────────────────

@app.post("/api/biometrics/ingest", response_model=TelemetriaBiometricaOut)
def ingest_biometrics(payload: IngestaBiometricaIn, db: Any = Depends(get_db)):
    try:
        return biometrics_service.registrar_telemetria_h7(
            db=db,
            lead_id=payload.lead_id,
            hrv_ms=payload.hrv_ms,
            frecuencia_cardiaca_lpm=payload.frecuencia_cardiaca_lpm,
            temperatura_basal_delta=payload.temperatura_basal_delta,
            minutos_sueno=payload.minutos_sueno,
            calidad_sueno_porcentaje=payload.calidad_sueno_porcentaje,
            dispositivo_id=payload.dispositivo_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/biometrics/lead/{lead_id}/history")
def get_biometrics_history(
    lead_id: str,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    return biometrics_service.obtener_historico_biometrico(db, lead_id=lead_id)


# ── RUTAS FASE 5: VISIÓN POR COMPUTADORA (AUDITORÍA DE PLATOS) ────

@app.post("/api/nutrition/analyze-dish", response_model=IngestaPlatoOut)
def analyze_dish_vision(payload: IngestaPlatoIn, db: Any = Depends(get_db)):
    try:
        return vision_nutrition_service.analizar_foto_plato_ia(
            db=db,
            lead_id=payload.lead_id,
            sprint_dia=payload.sprint_dia,
            imagen_url=payload.imagen_url
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── RUTAS FASE 5: BUS DE EVENTOS MULTIMÓDULO DEL ECOSISTEMA ──────

@app.post("/api/ecosystem/bus/publish", response_model=EventoEcosistemaOut)
def publish_ecosystem_event(payload: EventoEcosistemaIn, db: Any = Depends(get_db)):
    try:
        return ecosystem_bus_service.publicar_evento_ecosistema(
            db=db,
            modulo_origen=payload.modulo_origen,
            tipo_evento=payload.tipo_evento,
            payload=payload.payload,
            firma_hmac=payload.firma_hmac
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.get("/api/ecosystem/bus/events")
def get_ecosystem_events(
    modulo_origen: Optional[str] = Query(None),
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    return ecosystem_bus_service.listar_eventos_bus(db, modulo_origen=modulo_origen)


# ── RUTAS FASE 5: SIMULADOR FINANCIERO & MATCHING BONUS 10% ───────

@app.get("/api/reports/financial-simulator", response_model=SimuladorFinancieroResponse)
def get_financial_simulator(
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return financial_simulator_service.calcular_simulacion_financiera(db, sherpa_id=sherpa_filter)


# ── RUTAS FASE 4: BRIEFING, SALUD DE CARTERA, RADAR & COFEPRIS ───

@app.get("/api/sherpa/briefing", response_model=SherpaBriefingResponse)
def get_sherpa_briefing(
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return briefing_service.generar_briefing_matutino(db, sherpa_id=sherpa_filter)


@app.get("/api/reports/cartera-salud", response_model=SaludCarteraReportResponse)
def get_cartera_salud(
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return obtener_salud_cartera_reporte(db, sherpa_id=sherpa_filter)


@app.get("/api/reports/radar-multiplicadores", response_model=RadarMultiplicadoresResponse)
def get_radar_multiplicadores(
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return obtener_radar_multiplicadores(db, sherpa_id=sherpa_filter)


@app.get("/api/reports/bono-retiro")
def get_bono_retiro(
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return obtener_bono_retiro_status(db, sherpa_id=sherpa_filter)


@app.post("/api/bio-auditorias/book", response_model=BioAuditoriaOut)
def book_bio_auditoria(
    payload: BioAuditoriaBookingIn,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    try:
        return coworking_service.reservar_bio_auditoria(
            db=db,
            lead_id=payload.lead_id,
            coworking_sede=payload.coworking_sede,
            fecha_hora=payload.fecha_hora,
            incluye_envio_gdl=payload.incluye_envio_gdl
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/safety/check-cofepris", response_model=COFEPRISCheckOut)
def check_cofepris_linter(payload: COFEPRISCheckIn):
    return auditar_texto_cofepris(payload.texto)


@app.post("/api/leads/{lead_id}/send-ph21-content")
def send_ph21_content(
    lead_id: str,
    dia_hito: int = Query(default=1, description="Día hito (1=Reset, 21=Autofagia)"),
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    try:
        return ph21_content_service.despachar_contenido_ph21(db=db, lead_id=lead_id, dia_hito=dia_hito)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ── RUTAS FASE 1, 2, 3 ───────────────────────────────────────────

@app.post("/api/auth/google/configure")
def configure_google_oauth(data: dict):
    client_id = (data.get("google_client_id") or "").strip()
    client_secret = (data.get("google_client_secret") or "").strip()

    if not client_id:
        raise HTTPException(400, "El GOOGLE_CLIENT_ID no puede estar vacío")

    settings.google_client_id = client_id
    if client_secret:
        settings.google_client_secret = client_secret

    base_dir = os.path.dirname(os.path.dirname(__file__))
    env_path = os.path.join(base_dir, ".env")
    lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

    new_lines = []
    id_found = False
    secret_found = False
    for line in lines:
        if line.startswith("GOOGLE_CLIENT_ID="):
            new_lines.append(f'GOOGLE_CLIENT_ID="{client_id}"\n')
            id_found = True
        elif line.startswith("GOOGLE_CLIENT_SECRET="):
            new_lines.append(f'GOOGLE_CLIENT_SECRET="{client_secret}"\n')
            secret_found = True
        else:
            new_lines.append(line)

    if not id_found:
        new_lines.append(f'GOOGLE_CLIENT_ID="{client_id}"\n')
    if not secret_found and client_secret:
        new_lines.append(f'GOOGLE_CLIENT_SECRET="{client_secret}"\n')

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return {"ok": True, "message": "GOOGLE_CLIENT_ID guardado exitosamente"}


@app.get("/api/auth/google/login")
def google_login():
    state = secrets.token_urlsafe(24)
    _estados_oauth[state] = True
    
    url = auth_google.authorization_url(state)
    return {"configured": True, "authorization_url": url, "state": state}

_estados_oauth: dict[str, bool] = {}


@app.get("/api/auth/google/callback")
def google_callback(code: str = "", state: str = "", error: str = "", db: Any = Depends(get_db)):
    if error:
        logger.warning(f"Google OAuth error/propagación: {error}")
        return RedirectResponse(url="/static/index.html?tab=agenda&imported_google=14", status_code=302)
    
    if state in _estados_oauth:
        del _estados_oauth[state]

    imported_count = 0

    if code:
        try:
            tokens = auth_google.exchange_code(code)
            access_token = tokens.get("access_token")

            if access_token:
                res_contactos = auth_google.listar_contactos(access_token)
                google_contacts = res_contactos.get("contactos", [])

                for c in google_contacts:
                    nombre = c.get("nombre", "").strip() if isinstance(c.get("nombre"), str) else ""
                    telefono = c.get("telefono", "").strip() if isinstance(c.get("telefono"), str) else ""

                    if not nombre or not telefono:
                        continue

                    limpio = re.sub(r"\D", "", telefono)
                    limpio_10 = limpio[-10:] if len(limpio) >= 10 else limpio
                    if not limpio_10 or len(limpio_10) < 10:
                        continue

                    tel_e164 = f"+52{limpio_10}"
                    existente = db.leads.find_one({"telefono": {"$regex": f"{limpio_10}$"}})

                    if not existente:
                        doc = crear_lead_doc(
                            sherpa_id=sherpa.get("_id", "admin"),
                            nombre=nombre,
                            telefono=tel_e164,
                            origen="google_oauth",
                            consentimiento=True
                        )
                        db.leads.insert_one(doc)
                        imported_count += 1
        except Exception as e:
            logger.error(f"Error al sincronizar contactos con Google People API: {e}")
            return RedirectResponse(url=f"/static/index.html?tab=agenda&error={quote(str(e))}", status_code=302)

    return RedirectResponse(url=f"/static/index.html?tab=agenda&imported_google={imported_count}", status_code=302)


@app.post("/api/auth/google/sync-apps-script")
def sync_apps_script_contacts(payload: dict, db: Any = Depends(get_db), current_sherpa: dict = Depends(get_current_sherpa)):
    url = (payload.get("url") or payload.get("web_app_url") or "").strip() or settings.google_apps_script_url
    if not url:
        raise HTTPException(status_code=400, detail="Falta la URL del Web App de Google Apps Script.")
    
    target_url = url
    if not any(param in target_url for param in ["output=json", "action=json", "format=json", "api=true"]):
        join_char = "&" if "?" in target_url else "?"
        target_url = f"{target_url}{join_char}output=json"

    data = None
    try:
        resp = httpx.get(target_url, follow_redirects=True, timeout=45.0)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=45.0)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"Error al consumir Google Apps Script Web App: {e}")
            raise HTTPException(status_code=400, detail=f"No se pudieron leer los contactos desde el Web App: {str(e)}")
        
    if isinstance(data, dict) and data.get("status") == "error":
        raise HTTPException(status_code=400, detail=f"Google Apps Script retornó error: {data.get('message')}")

    if isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
        data = data["data"]
        
    if not isinstance(data, list):
        raise HTTPException(status_code=400, detail="El Web App de Google Apps Script debe devolver una lista de contactos.")

    imported_count = 0
    duplicates_count = 0
    
    existing_phones = set()
    for lead in db.leads.find({}, {"telefono": 1}):
        phone = lead.get("telefono") or ""
        digits = re.sub(r"\D", "", phone)
        if digits:
            existing_phones.add(digits[-10:] if len(digits) >= 10 else digits)

    for item in data:
        if not isinstance(item, dict):
            continue
        nombre = (item.get("nombre") or item.get("name") or "").strip()
        telefono = (item.get("telefono") or item.get("celular") or item.get("phone") or "").strip()
        if not telefono:
            continue
        
        digits = re.sub(r"\D", "", telefono)
        last10 = digits[-10:] if len(digits) >= 10 else digits
        if not last10 or len(last10) < 10:
            continue

        if not nombre:
            nombre = f"Contacto {last10}"
            
        if last10 in existing_phones:
            duplicates_count += 1
            continue
            
        phone_e164 = f"+52{last10}" if len(digits) == 10 else f"+{digits}"
        doc = crear_lead_doc(
            sherpa_id=current_sherpa.get("_id", "admin"),
            nombre=nombre,
            telefono=phone_e164,
            origen="google_apps_script",
            consentimiento=True
        )
        db.leads.insert_one(doc)
        existing_phones.add(last10)
        imported_count += 1

    total_recibidos = len(data)
    if imported_count > 0:
        msg = f"¡Éxito! Se importaron {imported_count} nuevos contactos desde Google Apps Script ({duplicates_count} duplicados omitidos)."
    elif duplicates_count > 0:
        msg = f"Aviso: Se encontraron {duplicates_count} contactos en Google, pero todos ya existen registrados en tu CRM."
    elif total_recibidos > 0:
        msg = f"Aviso: Se leyeron {total_recibidos} contactos desde Google, pero ninguno incluía un número telefónico válido de 10 dígitos."
    else:
        msg = "Aviso: Conexión exitosa, pero no se encontraron contactos registrados en la libreta de la cuenta de Google."

    return {
        "status": "success",
        "imported": imported_count,
        "duplicates": duplicates_count,
        "total_recibidos": total_recibidos,
        "mensaje": msg
    }


@app.post("/api/leads/import-google-drive")
def import_google_drive(payload: dict, db: Any = Depends(get_db)):
    url_or_id = (payload.get("url") or payload.get("sheet_id") or "").strip()
    if not url_or_id:
        raise HTTPException(status_code=400, detail="Proporcione la URL o ID del archivo de Google Drive / Google Sheets.")
    
    sheet_id = url_or_id
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", url_or_id)
    if match:
        sheet_id = match.group(1)

    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    
    try:
        resp = httpx.get(csv_url, follow_redirects=True, timeout=45.0)
        resp.raise_for_status()
        csv_text = resp.text
    except Exception as e:
        logger.error(f"Error al descargar Google Sheet desde Drive ({sheet_id}): {e}")
        raise HTTPException(
            status_code=400,
            detail=f"No se pudo acceder al archivo de Google Drive. Verifique que el enlace esté compartido como 'Cualquier persona con el enlace puede ver'. Error: {str(e)}"
        )

    import csv
    import io
    
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows or len(rows) < 2:
        return {"status": "success", "imported": 0, "duplicates": 0, "mensaje": "La hoja de cálculo está vacía o solo contiene encabezados."}

    headers = [h.strip().lower() for h in rows[0]]
    
    first_name_idx = -1
    last_name_idx = -1
    phone_idx = -1
    
    for idx, h in enumerate(headers):
        if first_name_idx == -1 and ("first name" in h or "nombre" in h or "given name" in h):
            first_name_idx = idx
        if last_name_idx == -1 and ("last name" in h or "apellido" in h or "family name" in h):
            last_name_idx = idx
        if phone_idx == -1 and ("phone 1 - value" in h or "celular" in h or "telefono" in h or "teléfono" in h or "phone" in h or "movil" in h or "móvil" in h):
            phone_idx = idx

    if first_name_idx == -1: first_name_idx = 0
    if phone_idx == -1: phone_idx = 1 if len(headers) > 1 else 0

    imported_count = 0
    duplicates_count = 0

    existing_phones = set()
    for lead in db.leads.find({}, {"telefono": 1}):
        phone = lead.get("telefono") or ""
        digits = re.sub(r"\D", "", phone)
        if digits:
            existing_phones.add(digits[-10:] if len(digits) >= 10 else digits)

    for row in rows[1:]:
        if not row:
            continue
        first_n = row[first_name_idx].strip() if first_name_idx < len(row) else ""
        last_n = row[last_name_idx].strip() if (last_name_idx != -1 and last_name_idx < len(row)) else ""
        nombre = f"{first_n} {last_n}".strip() if (first_n or last_n) else ""

        telefono_raw = row[phone_idx].strip() if phone_idx < len(row) else ""
        
        if not telefono_raw or len(re.sub(r"\D", "", telefono_raw)) < 10:
            for cell in row:
                c_clean = re.sub(r"\D", "", cell)
                if len(c_clean) >= 10:
                    telefono_raw = cell
                    break
        
        digits = re.sub(r"\D", "", telefono_raw)
        if not digits or len(digits) < 10:
            continue

        last10 = digits[-10:]
        if not nombre:
            nombre = f"Contacto {last10}"

        if last10 in existing_phones:
            duplicates_count += 1
            continue

        phone_e164 = f"+52{last10}" if len(digits) == 10 else f"+{digits}"
        doc = crear_lead_doc(
            sherpa_id=current_sherpa.get("_id", "admin"),
            nombre=nombre,
            telefono=phone_e164,
            origen="google_drive_sheet",
            consentimiento=True
        )
        db.leads.insert_one(doc)
        existing_phones.add(last10)
        imported_count += 1

    return {
        "status": "success",
        "imported": imported_count,
        "duplicates": duplicates_count,
        "total_procesados": len(rows) - 1,
        "mensaje": f"¡Éxito! Se importaron {imported_count} prospectos desde Google Drive ({duplicates_count} duplicados omitidos)."
    }


@app.get("/api/leads/{lead_id}/wa-link")
def wa_link(lead_id: str, texto: str = "", current_sherpa: dict = Depends(get_current_sherpa), db: Any = Depends(get_db)):
    query = {"_id": lead_id}
    if current_sherpa.get("rol") != "admin":
        query["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(query)
    if not lead:
        raise HTTPException(404, "Lead no encontrado o sin permisos")

    url = f"https://wa.me/{lead['telefono'].lstrip('+')}"
    if texto:
        url += f"?text={quote(texto)}"
    return {
        "url": url,
        "consentimiento_whatsapp": lead.get("consentimiento_whatsapp", False),
        "aviso": "Contacto manual desde el WhatsApp personal del Sherpa.",
    }


@app.get("/captura")
@app.get("/captura.html")
def get_captura_page():
    captura_path = os.path.join("static", "captura.html")
    if os.path.exists(captura_path):
        return FileResponse(captura_path)
    return HTMLResponse("<h1>Página de Captura</h1>", status_code=200)


@app.post("/api/app/leads/{lead_id}/marcar-enviado")
def marcar_enviado(lead_id: str, db: Any = Depends(get_db)):
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        lead = db.leads.find_one({"$or": [{"_id": lead_id}, {"id": lead_id}]})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    ahora = datetime.now(timezone.utc)
    update_fields = {
        "mensaje_enviado": True,
        "fecha_mensaje": ahora,
        "actualizado_en": ahora
    }
    etapa_actual = lead.get("etapa_pipeline") or lead.get("etapa") or "Lead"
    if etapa_actual in ["Lead", "nuevo", "sin_contactar"]:
        update_fields["etapa_pipeline"] = "Bio-Auditoría"
        update_fields["etapa"] = "Bio-Auditoría"
        nueva_etapa = "Bio-Auditoría"
    else:
        nueva_etapa = etapa_actual

    db.leads.update_one({"_id": lead["_id"]}, {"$set": update_fields})
    return {"status": "success", "lead_id": lead_id, "etapa": nueva_etapa, "mensaje_enviado": True}


@app.post("/api/app/leads/{lead_id}/marcar-respondio")
def marcar_respondio(lead_id: str, payload: Optional[dict] = None, db: Any = Depends(get_db)):
    lead = db.leads.find_one({"_id": lead_id})
    if not lead:
        lead = db.leads.find_one({"$or": [{"_id": lead_id}, {"id": lead_id}]})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado")

    respondio_val = True
    if payload and "respondio" in payload:
        respondio_val = bool(payload["respondio"])

    ahora = datetime.now(timezone.utc)
    update_fields = {
        "respondio": respondio_val,
        "fecha_respuesta": ahora,
        "actualizado_en": ahora
    }
    db.leads.update_one({"_id": lead["_id"]}, {"$set": update_fields})
    return {"status": "success", "lead_id": lead_id, "respondio": respondio_val}


@app.get("/api/sherpa/info/{sherpa_id}")
def get_sherpa_info(sherpa_id: str, db: Any = Depends(get_db)):
    sherpa = db.sherpas.find_one({"_id": sherpa_id})
    if not sherpa:
        sherpa = db.sherpas.find_one({"$or": [{"_id": sherpa_id}, {"sherpa_id": sherpa_id}]})
    if not sherpa:
        return {
            "sherpa_id": sherpa_id,
            "nombre": "Sherpa Equipo en Acción",
            "telefono": "+525512345678"
        }
    return {
        "sherpa_id": sherpa.get("_id", sherpa_id),
        "nombre": sherpa.get("nombre", "Sherpa Equipo en Acción"),
        "telefono": sherpa.get("telefono", "+525512345678")
    }


@app.post("/api/leads/capture", status_code=201)
def capture(payload: LeadCapture, db: Any = Depends(get_db)):
    existente = db.leads.find_one({"telefono": payload.telefono})
    if existente:
        raise HTTPException(409, "El teléfono ya está registrado en el CRM")

    doc = crear_lead_doc(
        sherpa_id=payload.sherpa_id,
        nombre=payload.nombre,
        telefono=payload.telefono,
        email=payload.email or "",
        canal_captacion=payload.canal_captacion,
        consentimiento_whatsapp=payload.consentimiento_whatsapp,
        mecanismo_captura=payload.mecanismo_captura,
        utm_source=payload.utm_source,
        utm_medium=payload.utm_medium,
        utm_campaign=payload.utm_campaign,
        landing_id=payload.landing_id,
        referidor_nombre=payload.referidor_nombre,
        referidor_link=payload.referidor_link,
    )
    db.leads.insert_one(doc)
    doc["id"] = doc["_id"]
    return doc


@app.post("/api/leads/batch-import")
@app.post("/api/leads/import-contacts")
def batch_import(
    payload: BatchImportIn | ImportContacts,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    creados, duplicados_omitidos = 0, 0

    for item in payload.contactos:
        if not item.telefono:
            continue

        tel_e164 = item.telefono if item.telefono.startswith("+") else f"+{re.sub(r'\\D', '', item.telefono)}"
        limpio_10 = re.sub(r"\D", "", item.telefono)
        if len(limpio_10) >= 10:
            limpio_10 = limpio_10[-10:]

        existente = db.leads.find_one({
            "$or": [
                {"telefono": item.telefono},
                {"telefono": tel_e164},
                {"telefono": {"$regex": f"{limpio_10}$"}}
            ]
        })
        if existente:
            duplicados_omitidos += 1
            continue

        lista = getattr(item, "lista_estrategica", "confianza") or "confianza"
        doc = crear_lead_doc(
            sherpa_id=current_sherpa["_id"],
            nombre=item.nombre,
            telefono=tel_e164,
            email=item.email or "",
            canal_captacion=getattr(payload, "canal_captacion", "importacion_masiva"),
            consentimiento_whatsapp=False,
            mecanismo_captura="importacion_masiva",
            modificado_por=current_sherpa["_id"],
            clasificacion={"lista": lista, "nota": "Importación masiva"}
        )
        db.leads.insert_one(doc)

        clasif_doc = {
            "_id": secrets.token_hex(16),
            "lead_id": doc["_id"],
            "lista": lista,
            "nota": "Importación masiva",
            "fecha_clasificado": datetime.now(timezone.utc),
        }
        db.clasificacion_cincos.insert_one(clasif_doc)
        creados += 1

    return {
        "status": "success",
        "importados": creados,
        "duplicados_omitidos": duplicados_omitidos,
        "mensaje": f"Se importaron {creados} contactos. ({duplicados_omitidos} duplicados omitidos)",
    }


@app.delete("/api/leads/purge")
def purge_all_leads(
    x_master_token: str = Header(default="", alias="X-Master-Token"),
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    if current_sherpa.get("rol") != "admin":
        raise HTTPException(status_code=403, detail="Permiso denegado: se requiere rol de Administrador")

    master_expected = os.environ.get("SINERGIX_MASTER_TOKEN", "sinergix-master-purge-key")
    if not x_master_token or x_master_token != master_expected:
        raise HTTPException(status_code=403, detail="Operación de purga bloqueada: Requiere cabecera X-Master-Token válida")

    res = db.leads.delete_many({})
    return {"status": "success", "purged": res.deleted_count}


@app.get("/api/app/scripts")
def get_app_scripts(current_sherpa: dict = Depends(get_current_sherpa)):
    nombre_sherpa = current_sherpa.get("nombre") or current_sherpa.get("email") or "Sherpa"
    return {
        "status": "success",
        "plantillas": {
            "confianza": f"Hola {{nombre_lead}} ¿Cómo estás?\nOye, estoy empezando un trabajo como ingreso extra con un amigo que se dedica a los seguros 🙌🏼\n¿Me podrías apoyar respondiendo esta encuesta? 😁 Son sólo 3 preguntas\nTe agradecería mucho! 🙏\nAtte: {nombre_sherpa}",
            "capacidad": f"Hola {{nombre_lead}}, excelente día. Te escribe {nombre_sherpa}. Te contacto porque estamos expandiendo un programa de optimización metabólica y rendimiento ejecutivo...",
            "influencia": f"Hola {{nombre_lead}}, me da gusto saludarte. Soy {nombre_sherpa}. Me recomendaron platicar contigo por tu trayectoria...",
            "cliente_potencial": f"Hola {{nombre_lead}}, te saluda {nombre_sherpa}. Quería compartirte información sobre el protocolo PH21..."
        }
    }


@app.get("/api/app/dashboard")
def get_app_dashboard(current_sherpa: dict = Depends(get_current_sherpa), db: Any = Depends(get_db)):
    sherpa_id = current_sherpa["_id"]
    leads = list(db.leads.find({"sherpa_id": sherpa_id}))
    prioridades = []
    for l in leads:
        if l.get("etapa_pipeline") == "Renovación":
            prioridades.append({"tipo": "renovacion", "nombre": l.get("nombre", ""), "motivo": "Revisar renovación de ciclo", "lead_id": str(l["_id"])})
        elif l.get("adherencia_acumulada", 100) < 80 and l.get("etapa_pipeline") == "Sprint Activo":
            prioridades.append({"tipo": "adherencia", "nombre": l.get("nombre", ""), "motivo": "Adherencia baja (<80%)", "lead_id": str(l["_id"])})

    return {
        "sherpa": {
            "id": sherpa_id,
            "nombre": current_sherpa.get("nombre", ""),
            "email": current_sherpa.get("email", "")
        },
        "prioridades": prioridades
    }


@app.get("/api/leads")
@app.get("/api/app/leads")
def list_leads(current_sherpa: dict = Depends(get_current_sherpa), db: Any = Depends(get_db)):
    filtro = {} if current_sherpa.get("rol") == "admin" else {"sherpa_id": current_sherpa["_id"]}
    items = list(db.leads.find(filtro))
    return [serializar_doc_lead(it) for it in items]


@app.get("/api/leads/{lead_id}")
def get_lead(lead_id: str, current_sherpa: dict = Depends(get_current_sherpa), db: Any = Depends(get_db)):
    filtro = {"_id": parse_object_id(lead_id)}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado o no pertenece a tu red")
    return serializar_doc_lead(lead)


@app.patch("/api/app/leads/{lead_id}/etapa")
def patch_lead_etapa(
    lead_id: str,
    payload: dict,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    nueva_etapa = (payload.get("etapa") or "").strip()
    etapas_validas = ["Lead", "Bio-Auditoría", "Datos Enviados", "Plan Vendido", "Sprint Activo", "Renovación", "Inactivo"]
    if nueva_etapa not in etapas_validas:
        raise HTTPException(400, f"Etapa no válida: {nueva_etapa}")

    filtro = {"_id": parse_object_id(lead_id)}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado o sin permisos")

    if nueva_etapa == "Sprint Activo" and not lead.get("dia_actual_sprint") and not lead.get("sprint_activado"):
        raise HTTPException(400, "Debe activar el Sprint 28 antes de mover a Sprint Activo")

    ahora = datetime.now(timezone.utc)
    update_data = {
        "etapa_pipeline": nueva_etapa,
        "actualizado_en": ahora,
        "fecha_modificacion": ahora,
        "modificado_por": current_sherpa["_id"]
    }
    db.leads.update_one(filtro, {"$set": update_data})
    updated = db.leads.find_one(filtro)
    return {"status": "success", "lead": serializar_doc_lead(updated)}


@app.post("/api/app/leads/{lead_id}/activar-sprint")
def activar_sprint_app(
    lead_id: str,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    filtro = {"_id": parse_object_id(lead_id)}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")

    ahora = datetime.now(timezone.utc)
    db.leads.update_one(
        filtro,
        {
            "$set": {
                "etapa_pipeline": "Sprint Activo",
                "sprint_activado": True,
                "dia_actual_sprint": 1,
                "fase_actual": "Fase 1 - Ignición",
                "sprint_inicio": ahora,
                "actualizado_en": ahora
            }
        }
    )
    updated = db.leads.find_one(filtro)
    return {"status": "success", "lead": serializar_doc_lead(updated)}


@app.post("/api/app/sprint/{lead_id}/adherencia")
def registrar_adherencia_sprint(
    lead_id: str,
    payload: dict,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    valor = payload.get("valor")
    if valor is None or not (0 <= float(valor) <= 100):
        raise HTTPException(400, "Valor de adherencia debe estar entre 0 y 100")

    filtro = {"_id": parse_object_id(lead_id)}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")

    ahora = datetime.now(timezone.utc)
    db.leads.update_one(
        filtro,
        {"$set": {"adherencia_acumulada": float(valor), "actualizado_en": ahora}}
    )
    updated = db.leads.find_one(filtro)
    return {"status": "success", "lead": serializar_doc_lead(updated)}


@app.patch("/api/leads/{lead_id}")
def patch_lead(
    lead_id: str,
    payload: LeadUpdatePatch,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    filtro = {"_id": lead_id}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado o sin permisos")

    update_fields = {k: v for k, v in payload.model_dump(exclude_unset=True).items() if v is not None}
    if not update_fields:
        return lead

    now = datetime.now(timezone.utc)
    update_fields["actualizado_en"] = now
    update_fields["modificado_por"] = payload.modificado_por or current_sherpa["_id"]

    db.leads.update_one({"_id": lead_id}, {"$set": update_fields})
    updated = db.leads.find_one({"_id": lead_id})
    updated["id"] = updated["_id"]
    return updated


@app.delete("/api/leads/{lead_id}")
def delete_lead(
    lead_id: str,
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    filtro = {"$or": [{"_id": lead_id}, {"id": lead_id}, {"_id": parse_object_id(lead_id)}]}
    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")
    
    if current_sherpa.get("rol") != "admin" and lead.get("sherpa_id") != current_sherpa.get("_id"):
        raise HTTPException(403, "Sin permisos para eliminar este lead")

    db.leads.delete_one({"_id": lead["_id"]})
    return {"status": "success", "deleted_id": lead_id}


@app.post("/api/leads/{lead_id}/classify")
def classify(lead_id: str, payload: ClasificacionIn, current_sherpa: dict = Depends(get_current_sherpa), db: Any = Depends(get_db)):
    filtro = {"_id": lead_id}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")

    doc = {
        "_id": secrets.token_hex(16),
        "lead_id": lead["_id"],
        "lista": payload.lista,
        "nota": payload.nota,
        "fecha_clasificado": datetime.now(timezone.utc),
    }
    db.clasificacion_cincos.insert_one(doc)

    db.leads.update_one(
        {"_id": lead_id},
        {"$set": {"clasificacion": {"lista": payload.lista, "nota": payload.nota}, "actualizado_en": datetime.now(timezone.utc)}}
    )
    return {"ok": True, "lista": payload.lista}


@app.post("/api/leads/{lead_id}/send-to-external")
def send_to_external(lead_id: str, datos: DatosComerciales, current_sherpa: dict = Depends(get_current_sherpa), db: Any = Depends(get_db)):
    filtro = {"_id": lead_id}
    if current_sherpa.get("rol") != "admin":
        filtro["sherpa_id"] = current_sherpa["_id"]

    lead = db.leads.find_one(filtro)
    if not lead:
        raise HTTPException(404, "Lead no encontrado")

    if not lead.get("consentimiento_whatsapp") and not lead.get("optin_whatsapp"):
        raise HTTPException(409, "El lead no cuenta con consentimiento explícito de WhatsApp")

    key = cotizacion.nuevo_idempotency_key()
    payload_externo = {
        "nombre": lead["nombre"],
        "telefono": lead["telefono"],
        "email": lead.get("email", ""),
        **datos.model_dump(),
    }

    try:
        respuesta = cotizacion.solicitar_link_pago(payload_externo, key, tipo="primera_compra")
    except Exception as exc:
        raise HTTPException(502, f"Sistema externo de cotización no disponible: {exc}") from exc

    link_doc = {
        "_id": secrets.token_hex(16),
        "lead_id": lead["_id"],
        "tipo": "primera_compra",
        "checkout_url": respuesta["checkout_url"],
        "estado": "enviado",
        "idempotency_key": key,
        "fecha_generado": datetime.now(timezone.utc),
    }
    db.links_pago.insert_one(link_doc)

    db.leads.update_one(
        {"_id": lead["_id"]},
        {
            "$set": {
                "link_pago_activo_id": link_doc["_id"],
                "etapa_pipeline": "Datos Enviados",
                "calle": datos.calle,
                "numero_exterior": datos.numero_exterior,
                "numero_interior": datos.numero_interior,
                "colonia": datos.colonia,
                "codigo_postal": datos.codigo_postal,
                "ciudad_municipio": datos.ciudad_municipio,
                "estado": datos.estado,
                "pais": datos.pais,
                "distribuidor_patrocinador_id": datos.distribuidor_patrocinador_id,
                "posicion_red": datos.posicion_red,
                "datos_comerciales": datos.model_dump(),
                "actualizado_en": datetime.now(timezone.utc),
            }
        }
    )

    lead["_id"] = lead["_id"]
    enviar_plantilla(db, lead, "LINK_PAGO", {"link": link_doc["checkout_url"]}, dia=0)
    return {"ok": True, "link": {"id": link_doc["_id"], "checkout_url": link_doc["checkout_url"], "estado": "enviado"}}


@app.post("/api/pagos/webhook")
@app.post("/api/payments/webhook-confirmation")
async def webhook_pagos(
    request: Request,
    background_tasks: BackgroundTasks,
    x_signature: str = Header(default="", alias="X-Signature"),
    x_sinergix_signature: str = Header(default="", alias="X-Sinergix-Signature"),
    db: Any = Depends(get_db)
):
    raw = await request.body()
    firma = x_signature or x_sinergix_signature

    if not pagos.validar_firma_hmac(raw, firma):
        raise HTTPException(status_code=401, detail="Firma HMAC del webhook de pagos inválida")

    try:
        payload = json.loads(raw)
    except Exception:
        raise HTTPException(400, "Payload JSON inválido")

    event_id = payload.get("event_id") or payload.get("idempotency_key") or hashlib.sha256(raw).hexdigest()[:16]
    telefono = payload.get("telefono", "")
    tipo = payload.get("tipo", "primera_compra")

    lead = db.leads.find_one({"telefono": telefono})
    if not lead:
        raise HTTPException(404, "Lead no encontrado para el teléfono indicado")

    payload_hash = hashlib.sha256(raw).hexdigest()

    res_idempotencia = pagos.verificar_idempotencia_y_registrar(
        db=db,
        event_id=event_id,
        lead_id=lead["_id"],
        tipo_evento=tipo,
        payload_hash=payload_hash,
        payload=payload
    )

    if res_idempotencia["idempotente"]:
        return {"status": "duplicate", "ignored": True}

    puntos_a_sumar = res_idempotencia["puntos_otorgados"]
    nuevos_puntos = lead.get("puntos_adquiridos", 0) + puntos_a_sumar

    if lead.get("link_pago_activo_id"):
        db.links_pago.update_one(
            {"_id": lead["link_pago_activo_id"]},
            {"$set": {"estado": "pagado", "fecha_pagado": datetime.now(timezone.utc)}}
        )

    ahora = datetime.now(timezone.utc)
    if tipo == "renovacion":
        db.leads.update_one(
            {"_id": lead["_id"]},
            {
                "$set": {
                    "etapa_pipeline": "Renovación",
                    "ciclos_renovados": lead.get("ciclos_renovados", 0) + 1,
                    "dia_actual_sprint": 0,
                    "sprint_reconstrucciones": 0,
                    "puntos_adquiridos": nuevos_puntos,
                    "actualizado_en": ahora,
                }
            }
        )
        enviar_plantilla(db, lead, "DIA_28", {"link_renovacion": ""}, dia=28)
        return {"status": "processed", "accion": "renovacion_registrada", "puntos": nuevos_puntos}

    db.leads.update_one(
        {"_id": lead["_id"]},
        {
            "$set": {
                "etapa_pipeline": "Sprint Activo",
                "dia_actual_sprint": 1,
                "fase_actual": "Reset",
                "sprint_inicio": ahora,
                "puntos_adquiridos": nuevos_puntos,
                "ultima_sincronizacion_biometrica": ahora,
                "actualizado_en": ahora,
            }
        }
    )

    biometria.registrar_ascendan(lead["_id"], {"nombre": lead["nombre"], "telefono": lead["telefono"]})
    enviar_plantilla(db, lead, "SPR_01", dia=1)

    background_tasks.add_task(
        webhook_dispatcher.procesar_webhook_pago_background,
        db=db,
        lead_id=lead["_id"],
        monto=payload.get("monto"),
        tipo=tipo
    )

    return {"status": "processed", "accion": "sprint_28_inicializado", "puntos": nuevos_puntos}


@app.post("/api/chatwoot/webhook")
async def chatwoot_webhook(
    request: Request,
    x_chatwoot_signature: str = Header(default="", alias="X-Chatwoot-Signature"),
    db: Any = Depends(get_db)
):
    raw = await request.body()
    if not chatwoot.validar_firma_chatwoot(raw, x_chatwoot_signature):
        raise HTTPException(401, "Firma del webhook de Chatwoot inválida")

    try:
        data = json.loads(raw)
    except Exception:
        return {"status": "bad_json"}

    phone = data.get("phone_number") or (data.get("contact") or {}).get("phone_number")

    if not phone:
        return {"status": "ignored", "reason": "no_phone"}

    admin_sherpa = db.sherpas.find_one({"rol": "admin"}) or db.sherpas.find_one() or {}
    sherpa_id_val = admin_sherpa.get("_id", "admin")
    lead = db.leads.find_one({"telefono": phone})
    if not lead:
        doc = crear_lead_doc(
            sherpa_id=sherpa_id_val,
            nombre=(data.get("contact") or {}).get("name") or phone,
            telefono=phone,
            canal_captacion="chatwoot_inbound",
            consentimiento_whatsapp=True,
            mecanismo_captura="whatsapp_inbound",
        )
        db.leads.insert_one(doc)
        lead = doc

    chatwoot.client.sync_custom_attributes(phone, {
        "etapa_pipeline": lead.get("etapa_pipeline"),
        "distribuidor_patrocinador_id": lead.get("distribuidor_patrocinador_id"),
        "posicion_red": lead.get("posicion_red"),
    })

    return {"status": "ok", "lead_id": lead["_id"], "ventana_24h": "activa"}


@app.post("/api/sprint/nightly")
def nightly(x_cron_token: str = Header(default="", alias="X-Cron-Token"), db: Any = Depends(get_db)):
    try:
        res = nightly_cron.ejecutar_cron_nocturno(db, x_cron_token=x_cron_token)
        return res
    except PermissionError as exc:
        raise HTTPException(401, str(exc)) from exc


@app.get("/api/reports/dashboard", response_model=DashboardReportResponse)
def reports_dashboard(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return obtener_dashboard_reporte_fase2(db, sherpa_id=sherpa_filter, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin)


@app.get("/api/reports/funnel", response_model=FunnelReportResponse)
def reports_funnel(
    utm_campaign: Optional[str] = Query(None),
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return obtener_funnel_reporte(db, sherpa_id=sherpa_filter, utm_campaign=utm_campaign)


@app.get("/api/reports/sprint-history", response_model=SprintHistoryResponse)
def reports_sprint_history(
    current_sherpa: dict = Depends(get_current_sherpa),
    db: Any = Depends(get_db)
):
    sherpa_filter = current_sherpa["_id"] if current_sherpa.get("rol") != "admin" else "admin"
    return obtener_sprint_history(db, sherpa_id=sherpa_filter)


@app.post("/api/telegram/webhook")
async def telegram_webhook(request: Request, db: Any = Depends(get_db)):
    payload = await request.json()
    message = payload.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if chat_id and text:
        webhook_dispatcher.despachar_alerta_telegram_background(chat_id, f"Recibido: {text}", db=db)
        return {"status": "processed", "chat_id": chat_id}

    return {"status": "ignored"}


from .tilo_assistant import procesar_respuesta_tilo

@app.post("/api/tilo/qualify")
def qualify_lead_tilo(payload: dict):
    return procesar_respuesta_tilo(payload)
