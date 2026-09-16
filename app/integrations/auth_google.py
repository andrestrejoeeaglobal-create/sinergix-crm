"""Autenticación Google OAuth 2.0 + Google People API (contactos) para Sherpas.

Flujo:
  1) GET  /api/auth/google/login    → authorization_url (scope: openid, email, profile, contacts)
  2) GET  /api/auth/google/callback → intercambia el código, guarda/actualiza al Sherpa
  3) GET  /api/auth/google/contacts → lee contactos con el refresh token guardado

Nota de compliance Google:
  - El scope `contacts` es RESTRICTED. Para el despliegue interno basta el modo
    Testing de Google Cloud Console con usuarios permitidos (los Sherpas).
  - Para uso público (>100 usuarios) se requiere verificación de Google + evaluación
    de seguridad anual del app OAuth.
"""
import logging
from urllib.parse import urlencode

import httpx

from ..config import settings

log = logging.getLogger("sinergix.auth")

AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
PEOPLE_URL = "https://people.googleapis.com/v1/people/me/connections"

SCOPES = "openid email profile https://www.googleapis.com/auth/contacts"


def _credenciales() -> tuple[str, str]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise ValueError("Google OAuth no configurado: define GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET")
    return settings.google_client_id, settings.google_client_secret


def authorization_url(state: str) -> str:
    client_id, _ = _credenciales()
    params = {
        "client_id": client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",   # para recibir refresh_token
        "prompt": "consent",        # garantiza refresh_token en la primera autorización
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{AUTH_BASE}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    client_id, client_secret = _credenciales()
    resp = httpx.post(
        TOKEN_URL,
        data={
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def userinfo(access_token: str) -> dict:
    resp = httpx.get(
        USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=15
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(refresh_token: str) -> str:
    client_id, client_secret = _credenciales()
    resp = httpx.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def listar_contactos(access_token: str, page_token: str | None = None, limite: int = 200) -> dict:
    """Lee contactos del Sherpa vía Google People API (connections)."""
    params: dict = {
        "personFields": "names,phoneNumbers,emailAddresses",
        "pageSize": min(limite, 200),
    }
    if page_token:
        params["pageToken"] = page_token
    resp = httpx.get(
        PEOPLE_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        params=params,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    contactos = []
    for persona in data.get("connections", []):
        nombres = persona.get("names") or [{}]
        telefonos = [t.get("value", "") for t in persona.get("phoneNumbers", [])]
        correos = [e.get("value", "") for e in persona.get("emailAddresses", [])]
        contacto = {
            "resource_name": persona.get("resourceName", ""),
            "nombre": nombres[0].get("displayName", "") if nombres else "",
            "telefono": telefonos[0] if telefonos else "",
            "email": correos[0] if correos else "",
        }
        if contacto["nombre"] or contacto["telefono"]:
            contactos.append(contacto)

    return {"contactos": contactos, "next_page_token": data.get("nextPageToken")}
