-- ============================================================
-- Sinergix Negocio CRM · Esquema v3 (PostgreSQL)
-- Autoridad: este archivo es el DDL de producción.
-- Los modelos SQLAlchemy (app/models.py) reflejan esta estructura.
-- ============================================================

-- ── ENUMs ────────────────────────────────────────────────────
CREATE TYPE etapa_pipeline AS ENUM (
  'Lead', 'Bio-Auditoría', 'Datos Enviados', 'Plan Vendido',
  'Sprint Activo', 'Renovación', 'Inactivo'
);

CREATE TYPE fase_sprint AS ENUM ('Reset', 'Ignicion', 'Ingenieria', 'Cierre');

CREATE TYPE link_pago_tipo AS ENUM ('primera_compra', 'renovacion');
CREATE TYPE link_pago_estado AS ENUM ('generado', 'enviado', 'abierto', 'pagado', 'expirado');

CREATE TYPE lista_cincos AS ENUM (
  'confianza', 'capacidad', 'influencia', 'cliente_potencial'
);

CREATE tipo_evento_sprint AS ENUM (
  'hito', 'alerta', 'reconstruccion', 'mensaje', 'nota'
);

-- ── SHERPAS (autenticación Google + importación de contactos) ──
CREATE TABLE sherpas (
  id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  google_sub              VARCHAR(64)  NOT NULL UNIQUE,   -- id de Google
  email                   VARCHAR(160) NOT NULL,
  nombre                  VARCHAR(120) DEFAULT '',
  api_token               VARCHAR(64)  NOT NULL UNIQUE,   -- token de API del CRM
  google_refresh_token    TEXT,                            -- para People API (contactos)
  google_access_token     TEXT,
  numero_distribuidor     VARCHAR(64),                     -- nº de distribuidor EEA
  creado_en               TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── LEADS (Perfil Maestro) ───────────────────────────────────
CREATE TABLE leads (
  id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sherpa_id                       VARCHAR(64)  NOT NULL,          -- row-level isolation
  nombre                          VARCHAR(80)  NOT NULL,
  apellido1                       VARCHAR(80),
  apellido2                       VARCHAR(80),
  telefono                        VARCHAR(20)  NOT NULL UNIQUE,   -- WhatsApp E.164
  email                           VARCHAR(160),

  -- Consentimiento WhatsApp (política Meta) — sin opt-in NO hay plantillas
  optin_whatsapp                  BOOLEAN      NOT NULL DEFAULT FALSE,
  optin_fecha                     TIMESTAMPTZ,
  optin_origen                    VARCHAR(40),

  -- Dirección de envío estructurada
  calle                           VARCHAR(160),
  numero_exterior                 VARCHAR(20),
  numero_interior                 VARCHAR(20),
  colonia                         VARCHAR(120),
  codigo_postal                   VARCHAR(5),
  ciudad_municipio                VARCHAR(120),
  estado                          VARCHAR(80),
  pais                            VARCHAR(80)  NOT NULL DEFAULT 'México',

  -- Colocación en red binaria
  distribuidor_patrocinador_id    VARCHAR(64),
  posicion_red                    VARCHAR(10)  CHECK (posicion_red IN ('izquierdo','derecho')),

  -- Origen y trazabilidad
  canal_captacion                 VARCHAR(40),
  utm_source                      VARCHAR(80),
  utm_medium                      VARCHAR(80),
  utm_campaign                    VARCHAR(120),
  landing_id                      VARCHAR(64),

  -- Bio-Auditoría
  bioauditoria_fecha              DATE,
  bioauditoria_resultados         JSONB,

  -- Pipeline
  etapa_pipeline                  etapa_pipeline NOT NULL DEFAULT 'Lead',
  link_pago_activo_id             UUID,                            -- FK agregada tras crear links_pago

  -- Sprint PH21
  sprint_inicio                   DATE,
  sprint_reconstrucciones         INT  NOT NULL DEFAULT 0,
  hrv_baseline                    INT,
  adherencia_acumulada            DECIMAL(5,2) NOT NULL DEFAULT 0,
  fase_actual                     fase_sprint,
  dia_actual_sprint               INT  NOT NULL DEFAULT 0,
  ultima_sincronizacion_biometrica TIMESTAMPTZ,

  -- Gamificación
  puntos_adquiridos               INT  NOT NULL DEFAULT 0,
  estado_bono_activo              VARCHAR(80),
  ciclos_renovados                INT  NOT NULL DEFAULT 0,

  creado_en                       TIMESTAMPTZ NOT NULL DEFAULT now(),
  actualizado_en                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_leads_sherpa        ON leads(sherpa_id);
CREATE INDEX idx_leads_etapa         ON leads(etapa_pipeline);
CREATE INDEX idx_leads_telefono      ON leads(telefono);
CREATE INDEX idx_leads_patrocinador  ON leads(distribuidor_patrocinador_id);

-- ── LINKS DE PAGO ────────────────────────────────────────────
CREATE TABLE links_pago (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id           UUID NOT NULL REFERENCES leads(id),
  tipo              link_pago_tipo   NOT NULL DEFAULT 'primera_compra',
  checkout_url      TEXT             NOT NULL,
  estado            link_pago_estado NOT NULL DEFAULT 'generado',
  idempotency_key   UUID             NOT NULL UNIQUE,
  fecha_generado    TIMESTAMPTZ      NOT NULL DEFAULT now(),
  fecha_pagado      TIMESTAMPTZ
);

CREATE INDEX idx_links_lead    ON links_pago(lead_id);
ALTER TABLE leads
  ADD CONSTRAINT fk_leads_link_activo
  FOREIGN KEY (link_pago_activo_id) REFERENCES links_pago(id);

-- ── WEBHOOKS DE PAGO (auditoría + idempotencia) ─────────────
CREATE TABLE webhooks_pago_log (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  idempotency_key  UUID,
  firma_valida     BOOLEAN NOT NULL,
  payload_hash     CHAR(64) NOT NULL UNIQUE,   -- sha256 del body crudo
  procesado_en     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── PLANTILLAS HSM (sincronización con Meta) ────────────────
CREATE TABLE plantillas_hsm (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre           VARCHAR(64)  NOT NULL UNIQUE,   -- SPR_01, SPR_02, CIE_03...
  texto            TEXT         NOT NULL,
  idioma           VARCHAR(10)  NOT NULL DEFAULT 'es',
  estado_meta      VARCHAR(20)  NOT NULL DEFAULT 'pendiente'
                   CHECK (estado_meta IN ('pendiente','aprobada','rechazada','pausada')),
  motivo_rechazo   TEXT,
  version          INT NOT NULL DEFAULT 1,
  actualizado_en   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── EVENTOS DEL SPRINT (bitácora de hitos/alertas/reconstrucciones) ──
CREATE TABLE eventos_sprint (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id           UUID NOT NULL REFERENCES leads(id),
  dia               INT    NOT NULL,
  tipo_evento       VARCHAR(20) NOT NULL
                    CHECK (tipo_evento IN ('hito','alerta','reconstruccion','mensaje','nota')),
  plantilla         VARCHAR(64),
  payload           JSONB,
  atendido_por_sherpa BOOLEAN NOT NULL DEFAULT FALSE,
  creado_en         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_eventos_lead ON eventos_sprint(lead_id, dia);

-- ── CLASIFICACIÓN "LOS CUATRO CINCOS" ───────────────────────
CREATE TABLE clasificacion_cincos (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id            UUID NOT NULL REFERENCES leads(id),
  lista              lista_cincos NOT NULL,
  fecha_clasificado  TIMESTAMPTZ NOT NULL DEFAULT now(),
  nota               TEXT
);

CREATE INDEX idx_cincos_lead ON clasificacion_cincos(lead_id);
