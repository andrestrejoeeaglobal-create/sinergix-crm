# Sinergix Negocio CRM — Fase 0

CRM conversacional del Sherpa: bandeja omnicanal (Chatwoot), Sprint PH21 (28 días),
links de pago con el sistema externo, gamificación y SafetyEngine COFEPRIS en todo
mensaje saliente.

## Contenido del paquete F0

| Componente | Archivo | Estado |
|---|---|---|
| Esquema PostgreSQL v3 | `db/schema.sql` | ✅ DDL autoritativo |
| Backend FastAPI | `app/main.py` | ✅ rutas de captura, perfil, links, webhook, cron |
| Máquina de estados Sprint | `app/sprint.py` | ✅ plan adaptativo (reconstrucciones) |
| SafetyEngine COFEPRIS | `app/safety.py` | ✅ valida TODO mensaje saliente |
| Salesbot + plantillas | `app/salesbot.py` | ✅ SPR_01–05, DIA_28, CIE_03, LINK_PAGO |
| Chatwoot (modo mock/live) | `app/integrations/chatwoot.py` | ✅ mock en F0, live en F1 |
| CotizacionAPI (mock/live) | `app/integrations/cotizacion.py` | ✅ mock hasta que exista la API real |
| BiometriaAPI (mock/live) | `app/integrations/biometria.py` | ✅ mock hasta Firebase |
| Google OAuth + contactos | `app/integrations/auth_google.py` | ✅ login Sherpa + People API |
| Pruebas | `tests/` | ✅ webhook idempotente, compliance, flujos |

## Ejecutar en local (sin Docker) — Windows

```powershell
cd C:\Users\HP\.openclaw-autoclaw\workspace\sinergix-crm

# Primera vez: crear el entorno virtual e instalar (ya hecho en esta máquina)
C:\Python313\python.exe -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt "psycopg[binary]"

# Día a día — OPCIÓN A (activar el venv y usar comandos normales):
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload        # → http://localhost:8000/docs
pytest tests/ -v                     # 10 passed

# Día a día — OPCIÓN B (sin activar nada):
.venv\Scripts\python.exe -m uvicorn app.main:app --reload
.venv\Scripts\python.exe -m pytest tests/ -v
```

Sin configurar nada más, todo corre en **modo mock**: Chatwoot no envía nada
(registra en memoria), CotizacionAPI y BiometriaAPI devuelven datos de prueba.

> Nota: el `python` que está primero en el PATH es el empaquetado de AutoClaw
> (sin módulo venv). Por eso el venv se creó con `C:\Python313\python.exe`.

Cubre: webhook con firma HMAC e idempotencia (sin doble acreditación de puntos),
SafetyEngine (bloqueo + sustitución), captura con opt-in obligatorio, flujo de
link de pago, importación de contactos de Google sin opt-in, cron nocturno.

## Desplegar en el VPS (Jorge — cuando esté listo)

```bash
cd sinergix-crm
docker compose up -d --build
# Servicios: postgres (crm + chatwoot), redis, chatwoot, chatwoot-worker, crm-api
```

Después del primer arranque:
1. Entrar a Chatwoot en `http://<vps>:3000` y crear la cuenta/inbox
2. Configurar `CHATWOOT_URL` y `CHATWOOT_API_KEY` en el `.env` del crm-api
3. Cargar el esquema si no se autoejecutó: `psql -U crm -d sinergix_crm -f db/schema.sql`

## Pendientes de integración real (F1–F2)

| Integración | Bloqueo actual | Acción |
|---|---|---|
| WhatsApp Cloud API (Meta) | Verificación de Meta Business | Arrancar trámite YA (camino crítico) |
| Plantillas HSM | Requieren Business verificado + revisión de Meta | Textos ya listos (aprobados por SafetyEngine) |
| CotizacionAPI real | Definir contrato con Daniel/Jorge (SQL Server) | El mock devuelve checkout_url de prueba |
| BiometriaAPI real | Proyecto Firebase + app Android con SDK Veepoo | Pipeline documentado: Eco (H7) → app → Firestore → API |

## Google OAuth (Sherpas + contactos)

1. Google Cloud Console → crear proyecto → habilitar **People API**
2. Credenciales → OAuth 2.0 Client (Web) con redirect `http://localhost:8000/api/auth/google/callback`
3. **Scope `contacts` es RESTRICTED**: para el despliegue interno basta el modo
   *Testing* con los Sherpas como usuarios de prueba. Para uso público se requiere
   verificación de Google + evaluación de seguridad anual.
4. Flujo: `GET /api/auth/google/login` → Sherpa autoriza → callback guarda el
   refresh token → `GET /api/auth/google/contacts` lista contactos → 
   `POST /api/leads/import-contacts` los importa **sin opt-in** (contacto manual
   del Sherpa vía `/api/leads/{id}/wa-link`, nunca Salesbot).

## Reglas de compliance integradas

- Todo mensaje saliente pasa por SafetyEngine (bloqueo de términos COFEPRIS + sustitución)
- Terminología fija: Sherpa guía · Ascendans busca mejorar su vida · cero "paciente"
- Sin `optin_whatsapp`, el Salesbot no inicia contacto (solo responde en ventana de 24 h)
- Contactos importados de Google: sin opt-in → solo enlace wa.me manual
- Webhooks de pago: firma HMAC + idempotencia (sin doble acreditación de puntos)
- Fotos de comidas: nunca salen del dispositivo del Ascendan
