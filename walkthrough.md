# Walkthrough — Corrección de Google OAuth v2 (RFC 6749) & Cero Datos Falsos

Se ha corregido el endpoint `GET /api/auth/google/login` en [`app/main.py`](file:///C:/Users/andre/.gemini/antigravity/brain/4a56e4cf-d25c-47b6-87f7-c3811c0fc4f8/scratch/Sinergix-CRM/sinergix-crm/app/main.py) para cumplir estrictamente con la especificación de **Google OAuth 2.0**.

---

## 🎯 Causa Raíz & Solución Implementada

### 1. Parámetro Faltante `response_type=code` (Error 400 Google)
* **Diagnóstico:** La pantalla de Google indicaba: `Required parameter is missing: response_type`. La URL generada por la API omitía los parámetros estándar de OAuth 2.0.
* **Solución en Backend:** Se actualizó `google_login()` para construir la URL canónica de la API de Google Accounts:
  ```http
  https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=...&redirect_uri=...&scope=...&state=...
  ```
  Incluye explícitamente:
  - `response_type=code`
  - `client_id` (tomado de `.env` o parámetro configurado)
  - `redirect_uri` (`http://127.0.0.1:8080/api/auth/google/callback`)
  - `scope` (perfil, email y `contacts.readonly`)
  - `access_type=offline` & `prompt=consent`

### 2. Purga y Cumplimiento Estricto "Cero Datos Falsos"
* La base de datos local MongoDB (`sinergix_crm`) fue purgada a **0 registros**.
* `GET /api/leads` responde con `[]` (Array vacío de estado inicial / Fresh Install).
* Todo dato de prospectos proviene **únicamente de entradas reales** del usuario via formulario o importación de archivos CSV / VCF.

---

## 🧪 Pruebas Automatizadas (44/44 Passing)

```bash
============================= 44 passed in 1.14s ==============================
```

- **`GET /api/auth/google/login`:** Retorna `200 OK` con la URL de autorización formateada correctamente.
- **`GET /api/leads`:** Retorna `200 OK` con `[]` en estado inicial.
