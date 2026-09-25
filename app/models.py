"""Modelos ORM — reflejan db/schema.sql (PostgreSQL). Tipos portables para SQLite en F0."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    String, Integer, Boolean, Text, DateTime, Date, Numeric, ForeignKey, JSON
)
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class TimestampMixin:
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )


class Sherpa(Base, TimestampMixin):
    __tablename__ = "sherpas"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    google_sub: Mapped[str] = mapped_column(String(64), unique=True)  # id de Google
    email: Mapped[str] = mapped_column(String(160), default="")
    nombre: Mapped[str] = mapped_column(String(120), default="")
    api_token: Mapped[str] = mapped_column(String(64), unique=True)   # token de API del CRM
    google_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    numero_distribuidor: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    sherpa_id: Mapped[str] = mapped_column(String(64), index=True)

    nombre: Mapped[str] = mapped_column(String(80))
    apellido1: Mapped[str] = mapped_column(String(80), default="")
    apellido2: Mapped[str] = mapped_column(String(80), default="")
    telefono: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    telefono_normalizado: Mapped[str] = mapped_column(String(10), default="", index=True)
    email: Mapped[str] = mapped_column(String(160), default="")

    # Consentimiento WhatsApp (política Meta)
    optin_whatsapp: Mapped[bool] = mapped_column(Boolean, default=False)
    optin_fecha: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    optin_origen: Mapped[str | None] = mapped_column(String(40), nullable=True)

    # Dirección de envío
    calle: Mapped[str] = mapped_column(String(160), default="")
    numero_exterior: Mapped[str] = mapped_column(String(20), default="")
    numero_interior: Mapped[str | None] = mapped_column(String(20), nullable=True)
    colonia: Mapped[str] = mapped_column(String(120), default="")
    codigo_postal: Mapped[str] = mapped_column(String(5), default="")
    ciudad_municipio: Mapped[str] = mapped_column(String(120), default="")
    estado: Mapped[str] = mapped_column(String(80), default="")
    pais: Mapped[str] = mapped_column(String(80), default="México")

    # Red binaria
    distribuidor_patrocinador_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    posicion_red: Mapped[str | None] = mapped_column(String(10), nullable=True)  # izq/der

    # Origen
    canal_captacion: Mapped[str | None] = mapped_column(String(40), nullable=True)
    utm_source: Mapped[str | None] = mapped_column(String(80), nullable=True)
    utm_medium: Mapped[str | None] = mapped_column(String(80), nullable=True)
    utm_campaign: Mapped[str | None] = mapped_column(String(120), nullable=True)
    landing_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Bio-Auditoría
    bioauditoria_fecha: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    bioauditoria_resultados: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Pipeline
    etapa_pipeline: Mapped[str] = mapped_column(String(20), default="Lead", index=True)
    link_pago_activo_id: Mapped[str | None] = mapped_column(
        String(32), ForeignKey("links_pago.id"), nullable=True
    )

    # Sprint PH21
    sprint_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sprint_reconstrucciones: Mapped[int] = mapped_column(Integer, default=0)
    hrv_baseline: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adherencia_acumulada: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    fase_actual: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dia_actual_sprint: Mapped[int] = mapped_column(Integer, default=0)
    ultima_sincronizacion_biometrica: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Gamificación
    puntos_adquiridos: Mapped[int] = mapped_column(Integer, default=0)
    estado_bono_activo: Mapped[str | None] = mapped_column(String(80), nullable=True)
    ciclos_renovados: Mapped[int] = mapped_column(Integer, default=0)


class LinkPago(Base):
    __tablename__ = "links_pago"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(32), ForeignKey("leads.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20), default="primera_compra")
    checkout_url: Mapped[str] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="generado")  # generado/enviado/abierto/pagado/expirado
    idempotency_key: Mapped[str] = mapped_column(String(32), unique=True, default=_uuid)
    fecha_generado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    fecha_pagado: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WebhookPagoLog(Base):
    __tablename__ = "webhooks_pago_log"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    idempotency_key: Mapped[str | None] = mapped_column(String(32), nullable=True)
    firma_valida: Mapped[bool] = mapped_column(Boolean)
    payload_hash: Mapped[str] = mapped_column(String(64), unique=True)
    procesado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PlantillaHSM(Base, TimestampMixin):
    __tablename__ = "plantillas_hsm"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    nombre: Mapped[str] = mapped_column(String(64), unique=True)
    texto: Mapped[str] = mapped_column(Text)
    idioma: Mapped[str] = mapped_column(String(10), default="es")
    estado_meta: Mapped[str] = mapped_column(String(20), default="pendiente")
    motivo_rechazo: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)


class EventoSprint(Base):
    __tablename__ = "eventos_sprint"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(32), ForeignKey("leads.id"), index=True)
    dia: Mapped[int] = mapped_column(Integer)
    tipo_evento: Mapped[str] = mapped_column(String(20))  # hito/alerta/reconstruccion/mensaje/nota
    plantilla: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    atendido_por_sherpa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ClasificacionCincos(Base):
    __tablename__ = "clasificacion_cincos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    lead_id: Mapped[str] = mapped_column(String(32), ForeignKey("leads.id"), index=True)
    lista: Mapped[str] = mapped_column(String(30))  # confianza/capacidad/influencia/cliente_potencial
    fecha_clasificado: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    nota: Mapped[str | None] = mapped_column(Text, nullable=True)
