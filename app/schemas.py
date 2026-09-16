"""Esquemas Pydantic de entrada/salida de la API (Fases 1, 2, 3, 4 y 5)."""
import re
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

LISTAS_VALIDAS = {"confianza", "capacidad", "influencia", "cliente_potencial"}


def sanitizar_csv_injection(v: Any) -> Any:
    """Protección contra CSV Injection: escapa =, +, -, @ al inicio de strings."""
    if isinstance(v, str) and v and v[0] in ("=", "+", "-", "@"):
        return f"'{v}"
    return v


def normalizar_telefono_e164(v: Any, default_region: str = "MX") -> str:
    """Limpia y estandariza un teléfono a formato internacional E.164 determinista."""
    if not v:
        return ""
    raw = str(v).strip()
    try:
        import phonenumbers
        if raw.startswith("+"):
            parsed = phonenumbers.parse(raw, None)
        else:
            parsed = phonenumbers.parse(raw, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except Exception:
        pass

    limpio = re.sub(r"\D", "", raw)
    if not limpio:
        return ""
    if len(limpio) == 10:
        return f"+52{limpio}"
    if not raw.startswith("+"):
        return f"+{limpio}"
    return f"+{limpio}"


# ── Modelos de Lead & Prospección ────────────────────────────────

class LeadCapture(BaseModel):
    sherpa_id: str = Field(min_length=1)
    nombre: str = Field(min_length=1, max_length=80)
    telefono: str = Field(min_length=10, max_length=20, description="E.164, ej. +5215512345678")
    email: str = ""
    canal_captacion: str = "landing"
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    landing_id: str | None = None
    consentimiento_whatsapp: bool = Field(default=True, alias="optin_whatsapp")
    mecanismo_captura: str = Field(default="formulario_web")
    referidor_nombre: str | None = "Daniel Osorio"
    referidor_link: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitizar_nombre(cls, v: Any) -> Any:
        return sanitizar_csv_injection(v)

    @field_validator("telefono", mode="before")
    @classmethod
    def normalizar_tel(cls, v: Any) -> str:
        return normalizar_telefono_e164(v)

    @model_validator(mode="before")
    @classmethod
    def validar_optin_meta(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val = data.get("consentimiento_whatsapp")
            if val is None:
                val = data.get("optin_whatsapp")
            if val is False:
                raise ValueError("Se requiere el consentimiento explícito (opt-in) de WhatsApp para la Cloud API")
        return data


class ContactoImportItem(BaseModel):
    nombre: str = Field(min_length=1)
    telefono: str = Field(min_length=10)
    email: str = ""
    canal_captacion: str = "importacion_masiva"
    lista_estrategica: str = Field(default="confianza", description="confianza | capacidad | influencia | cliente_potencial")

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitizar_nombre(cls, v: Any) -> Any:
        return sanitizar_csv_injection(v)

    @field_validator("telefono", mode="before")
    @classmethod
    def normalizar_tel(cls, v: Any) -> str:
        return normalizar_telefono_e164(v)


class BatchImportIn(BaseModel):
    contactos: list[ContactoImportItem] = Field(max_length=1000)
    canal_captacion: str = "importacion_masiva"


class LeadUpdatePatch(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    email: str | None = None
    etapa_pipeline: str | None = None
    respondio: bool | None = None
    is_cancelled: bool | None = None
    consentimiento_whatsapp: bool | None = None
    modificado_por: str | None = None

    @field_validator("nombre", mode="before")
    @classmethod
    def sanitizar_nombre(cls, v: Any) -> Any:
        return sanitizar_csv_injection(v) if v is not None else None

    @field_validator("telefono", mode="before")
    @classmethod
    def normalizar_tel(cls, v: Any) -> Any:
        return normalizar_telefono_e164(v) if v is not None else None


class DatosComerciales(BaseModel):
    calle: str = Field(min_length=1)
    numero_exterior: str
    numero_interior: str | None = None
    colonia: str
    codigo_postal: str = Field(pattern=r"^\d{5}$")
    ciudad_municipio: str
    estado: str
    pais: str = "México"
    distribuidor_patrocinador_id: str = Field(min_length=1)
    posicion_red: str = Field(pattern=r"^(inscripcion|equilibrio|izquierdo|derecho)$", description="Lado de registro: inscripción o equilibrio")


class ContactoIn(BaseModel):
    nombre: str = ""
    telefono: str = ""
    email: str = ""


class ImportContacts(BaseModel):
    contactos: list[ContactoIn] = Field(max_length=500)


class ClasificacionIn(BaseModel):
    lista: str
    nota: str | None = None

    @field_validator("lista")
    @classmethod
    def lista_valida(cls, v: str) -> str:
        if v not in LISTAS_VALIDAS:
            raise ValueError(f"lista debe ser una de: {sorted(LISTAS_VALIDAS)}")
        return v


class PagoWebhookIn(BaseModel):
    event_id: str = Field(description="ID único de evento emitido por el procesador")
    lead_id: str | None = None
    telefono: str = Field(description="Teléfono del lead E.164")
    tipo: str = Field(default="primera_compra", description="primera_compra / renovacion")
    monto: float | None = None
    ventana_concurso: str | None = Field(default="2026-Q3", description="Ventana temporal para el concurso")


class PlantillaHSMCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=64)
    texto: str = Field(min_length=1)
    idioma: str = "es"


class PlantillaHSMOut(BaseModel):
    id: str
    nombre: str
    texto: str
    idioma: str
    estado_meta: str
    motivo_rechazo: str | None = None
    version: int


class ChatwootWebhookPayload(BaseModel):
    event: str = ""
    phone_number: str | None = None
    content: str | None = None
    conversation_id: int | str | None = None
    additional_attributes: dict[str, Any] | None = None


class LeadOut(BaseModel):
    id: str
    sherpa_id: str
    nombre: str
    telefono: str
    etapa_pipeline: str
    consentimiento_whatsapp: bool = True
    fecha_consentimiento: datetime | None = None
    mecanismo_captura: str | None = "formulario_web"
    optin_whatsapp: bool = True
    respondio: bool = False
    is_cancelled: bool = False
    referidor_nombre: str | None = "Daniel Osorio"
    referidor_link: str | None = None
    dia_actual_sprint: int = 0
    fase_actual: str | None = None
    adherencia_acumulada: float = 0.0
    puntos_adquiridos: int = 0
    ciclos_renovados: int = 0
    link_pago_activo_id: str | None = None
    creado_en: datetime | str | None = None
    actualizado_en: datetime | str | None = None
    modificado_por: str | None = None


# ── MODELOS DE REPORTES Y MÉTRICAS (FASE 2) ──────────────────────

class MetricasPipeline(BaseModel):
    total_leads: int = Field(0, description="Total acumulado en el periodo")
    sin_encuesta: int = Field(0, description="Leads pendientes de primer contacto")
    respondieron: int = Field(0, description="Leads que respondieron mensaje/encuesta")
    cotizados: int = Field(0, description="Leads transferidos a red/cotizador")
    cancelados: int = Field(0, description="Leads marcados como is_cancelled")
    tasa_conversion_global: float = Field(0.0, description="Porcentaje cotizados / total_leads")


class MetricasCuatroCincos(BaseModel):
    confianza: int = 0
    capacidad: int = 0
    influencia: int = 0
    cliente_potencial: int = 0
    sin_clasificar: int = 0


class MetricasSprint(BaseModel):
    sprint_id: int = 28
    dia_actual: int = 28
    dias_totales: int = 28
    progreso_porcentaje: float = 100.0
    meta_contactos: int = 100
    contactos_logrados: int = 0


class DashboardReportResponse(BaseModel):
    periodo_inicio: date
    periodo_fin: date
    pipeline: MetricasPipeline
    clasificacion: MetricasCuatroCincos
    sprint: MetricasSprint
    canales_adquisicion: Dict[str, int] = Field(default_factory=dict)
    distribucion_red: Dict[str, int] = Field(default_factory=dict, description="Conteo por Lado de registro: inscripción vs equilibrio")


class FunnelStageItem(BaseModel):
    etapa: str
    conteo: int
    porcentaje: float


class FunnelReportResponse(BaseModel):
    utm_campaign: str | None = None
    total_leads: int = 0
    etapas: List[FunnelStageItem] = Field(default_factory=list)


class SprintHistoryItem(BaseModel):
    sprint_id: int
    fecha_inicio: date
    fecha_fin: date
    contactos_logrados: int
    adherencia_promedio: float
    completado: bool


class SprintHistoryResponse(BaseModel):
    sherpa_id: str
    historico: List[SprintHistoryItem] = Field(default_factory=list)


# ── MODELOS DE FASE 4 (CORE CONVERSACIONAL, RETENCIÓN DE CARTERA & RED) ──

class BriefingAccionItem(BaseModel):
    tipo: str = Field(description="critico | lider_emergente | seguimiento | cotizacion")
    lead_id: str
    nombre: str
    mensaje: str
    boton_label: str
    accion: str


class SherpaBriefingResponse(BaseModel):
    sherpa_id: str
    sherpa_nombre: str
    fecha: str
    resumen_texto: str
    contactos_seguimiento: int = 0
    sprints_por_vencer: int = 0
    lideres_emergentes: int = 0
    acciones_prioritarias: List[BriefingAccionItem] = Field(default_factory=list)


class SaludCarteraClienteItem(BaseModel):
    lead_id: str
    nombre: str
    telefono: str
    sprint_dia: int
    adherencia_porcentaje: float
    alerta_abandono: bool = Field(description="True si adherencia < 80%")
    nivel_riesgo: str = Field(description="alto | medio | optimo")
    accion_sugerida: str


class SaludCarteraReportResponse(BaseModel):
    total_clientes_activos: int
    optimos: int
    riesgo_medio: int
    riesgo_alto_critico: int
    clientes: List[SaludCarteraClienteItem] = Field(default_factory=list)


class LiderEmergenteItem(BaseModel):
    distribuidor_id: str
    nombre: str
    nivel: int
    reclutas_ultimos_14_dias: int
    es_estrella_emergente: bool = True
    insignia: str = "⭐ Velocidad +3/sem"


class RadarMultiplicadoresResponse(BaseModel):
    sherpa_id: str
    total_descentralizados: int
    lideres_emergentes: List[LiderEmergenteItem] = Field(default_factory=list)


class BonoRetiroLeaderItem(BaseModel):
    lider_id: str
    nombre: str
    activos_actuales: int
    meta: int = 50
    porcentaje: float


class BonoRetiroResponse(BaseModel):
    avance_personal: int = 42
    meta_personal: int = 50
    porcentaje_personal: float = 84.0
    calificado: bool = False
    bono_monto_mxn: float = 50000.0
    faltantes: int = 8
    lideres_directos: List[BonoRetiroLeaderItem] = Field(default_factory=list)


class BioAuditoriaBookingIn(BaseModel):
    lead_id: str
    coworking_sede: str = Field(default="Coworking Norte", description="Sede física seleccionada")
    fecha_hora: datetime
    incluye_envio_gdl: bool = False
    costo_flete_gdl: float = 95.0


class BioAuditoriaOut(BaseModel):
    id: str
    lead_id: str
    coworking_sede: str
    fecha_hora: datetime
    costo_flete: float
    estado: str = "confirmada"
    mensaje_confirmacion: str


class COFEPRISCheckIn(BaseModel):
    texto: str = Field(min_length=1)


class COFEPRISSugerenciaItem(BaseModel):
    termino_prohibido: str
    reemplazo_normativo: str
    motivo: str


class COFEPRISCheckOut(BaseModel):
    es_seguro: bool
    palabras_detectadas: List[str] = Field(default_factory=list)
    sugerencias: List[COFEPRISSugerenciaItem] = Field(default_factory=list)
    texto_sanitizado: str


# ── MODELOS DE FASE 5 (TELEMETRÍA H7, VISIÓN IA, BUS & SIMULADOR) ─────────

class IngestaBiometricaIn(BaseModel):
    lead_id: str
    hrv_ms: int = Field(..., ge=10, le=250, description="Variabilidad frecuencia cardíaca ms")
    frecuencia_cardiaca_lpm: int = Field(..., ge=30, le=220, description="FC en reposo lpm")
    temperatura_basal_delta: float = Field(..., description="Desviación °C")
    minutos_sueno: int = Field(..., ge=0, le=1440)
    calidad_sueno_porcentaje: float = Field(..., ge=0.0, le=100.0)
    dispositivo_id: str = "H7_BAND_DEFAULT"


class SuenoDetalleDoc(BaseModel):
    minutos_totales: int
    calidad_porcentaje: float
    profundo_min: int = 120
    rem_min: int = 90
    ligero_min: int = 240


class TelemetriaBiometricaOut(BaseModel):
    id: str
    lead_id: str
    timestamp: datetime
    hrv_ms: int
    frecuencia_cardiaca_lpm: int
    temperatura_basal_delta: float
    sueno: SuenoDetalleDoc
    dispositivo_id: str


class IngestaPlatoIn(BaseModel):
    lead_id: str
    sprint_dia: int = Field(..., ge=1, le=28)
    imagen_url: str = Field(..., min_length=5)


class IngestaPlatoOut(BaseModel):
    analisis_id: str
    lead_id: str
    sprint_dia: int
    adherencia_score: float = Field(..., ge=0.0, le=1.0)
    semaforo: str = Field(..., description="verde | amarillo | rojo")
    alimentos_detectados: List[str] = Field(default_factory=list)
    score_antiinflamatorio: float = Field(..., ge=0.0, le=10.0)
    requiere_intervencion: bool


class EventoEcosistemaIn(BaseModel):
    modulo_origen: str = Field(..., description="creator | salud | pro | admin | crm")
    tipo_evento: str = Field(..., description="ej. lead.capturado, biometria.alerta, pedido.pagado")
    payload: Dict[str, Any] = Field(default_factory=dict)
    firma_hmac: str = Field(default="", description="Firma HMAC SHA256")


class EventoEcosistemaOut(BaseModel):
    id: str
    modulo_origen: str
    tipo_evento: str
    estado_despacho: str = "procesado"
    timestamp: datetime


class SimuladorFinancieroResponse(BaseModel):
    sherpa_id: str
    mrr_actual: float = 14600.0
    directos_activos: int = 50
    proyeccion_4_sherpas: float = 54600.0
    matching_bonus_10pct: float = 5460.0
    patrimonio_5_anos: float = 911000.0
    bono_retiro_calificado: bool = False
    escenarios: Dict[str, float] = Field(default_factory=dict)
