"""Adaptador al Sistema Externo de Cotización (SQL Server vía API).

Sin COTIZACION_URL configurado → modo mock: devuelve una checkout_url de prueba.
El CRM NUNCA guarda precios fijos: el desglose lo calcula y muestra el sistema externo.
"""
import logging
import uuid

import httpx

from ..config import settings

log = logging.getLogger("sinergix.cotizacion")


def solicitar_link_pago(lead_payload: dict, idempotency_key: str, tipo: str = "primera_compra") -> dict:
    """Envía los datos comerciales del lead y recibe su checkout_url personalizada.

    lead_payload: nombre, apellidos, teléfono, dirección estructurada,
                  distribuidor_patrocinador_id, posicion_red.
    Devuelve: {checkout_url, modo}
    """
    if not settings.cotizacion_url:
        log.info("[MOCK CotizacionAPI] link generado para %s (tipo=%s)", lead_payload.get("telefono"), tipo)
        key_corta = idempotency_key[:12]
        return {
            "checkout_url": f"https://pay.sinergix.test/checkout/{key_corta}",
            "modo": "mock",
        }

    resp = httpx.post(
        settings.cotizacion_url,
        headers={"Authorization": f"Bearer {settings.cotizacion_token}"},
        json={"idempotency_key": idempotency_key, "tipo": tipo, **lead_payload},
        timeout=20,
    )
    resp.raise_for_status()
    data = resp.json()
    if "checkout_url" not in data:
        raise ValueError(f"CotizacionAPI no devolvió checkout_url: {data}")
    return {"checkout_url": data["checkout_url"], "modo": "live"}


def nuevo_idempotency_key() -> str:
    return uuid.uuid4().hex
