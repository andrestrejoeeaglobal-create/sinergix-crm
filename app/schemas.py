"""Esquemas Pydantic de entrada/salida de la API."""
from datetime import datetime
from pydantic import BaseModel, Field, field_validator

LISTAS_VALIDAS = {"confianza", "capacidad", "influencia", "cliente_potencial"}


class SherpaLoginIn(BaseModel):
    user: str = ""
    password: str = ""
    User: str = ""
    Password: str = ""
    username: str = ""
    Username: str = ""


class LeadCapture(BaseModel):
    """Formulario de landing / captura rápida. El checkbox de consentimiento es obligatorio."""
    sherpa_id: str = Field(min_length=1)
    nombre: str = Field(min_length=1, max_length=80)
    telefono: str = Field(min_length=10, max_length=20, description="E.164, ej. +5215512345678")
    email: str = ""
    canal_captacion: str = "landing"
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None
    landing_id: str | None = None
    optin_whatsapp: bool = Field(description="Consentimiento explícito — obligatorio")

    @field_validator("optin_whatsapp")
    @classmethod
    def optin_obligatorio(cls, v: bool) -> bool:
        if not v:
            raise ValueError("Se requiere el consentimiento explícito (opt-in) de WhatsApp")
        return v


class DatosComerciales(BaseModel):
    """Datos que el CRM envía al sistema externo de cotización (SQL Server vía adaptador)."""
    calle: str = Field(min_length=1)
    numero_exterior: str
    numero_interior: str | None = None
    colonia: str
    codigo_postal: str = Field(pattern=r"^\d{5}$")
    ciudad_municipio: str
    estado: str
    pais: str = "México"
    distribuidor_patrocinador_id: str = Field(min_length=1)
    posicion_red: str = Field(pattern=r"^(izquierdo|derecho)$")


class ContactoIn(BaseModel):
    """Contacto de Google People API simplificado para importación."""
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


class LeadUpdateIn(BaseModel):
    nombre: str | None = None
    apellido1: str | None = None
    apellido2: str | None = None
    telefono: str | None = None
    email: str | None = None
    etapa_pipeline: str | None = None
    fase_actual: str | None = None
    adherencia_acumulada: float | None = None
    puntos_adquiridos: int | None = None
    optin_whatsapp: bool | None = None
    client_updated_at: datetime | None = None


class LeadOut(BaseModel):
    id: str
    nombre: str
    telefono: str
    telefono_normalizado: str | None = None
    etapa_pipeline: str
    optin_whatsapp: bool
    dia_actual_sprint: int
    fase_actual: str | None
    adherencia_acumulada: float
    puntos_adquiridos: int
    ciclos_renovados: int
    link_pago_activo_id: str | None
    actualizado_en: datetime | None = None
    updated_at: datetime | None = None


class LinkOut(BaseModel):
    id: str
    lead_id: str
    tipo: str
    checkout_url: str
    estado: str
