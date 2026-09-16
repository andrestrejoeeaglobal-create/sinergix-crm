"""Adaptador a BiometriaAPI (Cloud Functions de Firebase — Sinergix Salud).

Sin BIOMETRIA_URL configurado → modo mock: genera datos plausibles para F0.
Pipeline real: Banda Sinergix Eco (H7) → App Android (SDK Veepoo) → Firestore → esta API.
"""
import logging
import random
from datetime import datetime, timezone

import httpx

from ..config import settings

log = logging.getLogger("sinergix.biometria")

# Baseline plausible para mocks (inspirado en h7_simulator.py)
_RNG = random.Random(42)


def registrar_ascendan(ascendan_id: str, perfil: dict) -> dict:
    """Crea la cartera de salud del Ascendan en Sinergix Salud (Firestore)."""
    if not settings.biometria_url:
        log.info("[MOCK BiometriaAPI] cartera creada para %s", ascendan_id)
        return {"ok": True, "mock": True, "ascendan_id": ascendan_id}
    resp = httpx.post(
        f"{settings.biometria_url}/ascendans",
        headers={"Authorization": f"Bearer {settings.biometria_token}"},
        json={"ascendan_id": ascendan_id, **perfil},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def get_resumen(ascendan_id: str, dia: int) -> dict:
    """Resumen biométrico del día para el motor del Sprint.

    Mock: genera valores con tendencia de mejora ligera (como el simulador H7).
    Real: GET /biometria/{id}/resumen?dia=N → agregados, nunca datos crudos.
    """
    if not settings.biometria_url:
        mejora = min(dia * 0.5, 8)  # HRV sube hasta +8ms en 28 días
        hrv = round(46 + mejora + _RNG.uniform(-3, 3))
        fc = max(52, round(61 - dia * 0.18 + _RNG.uniform(-2, 2)))
        sueno = round(min(8.2, 6.4 + dia * 0.05) + _RNG.uniform(-0.4, 0.4), 1)
        registrado = _RNG.random() > 0.12  # ~88% de días con datos (dispara reconstrucciones)
        return {
            "mock": True,
            "ascendan_id": ascendan_id,
            "dia": dia,
            "registrado": registrado,
            "hrv": hrv,
            "fc_reposo": fc,
            "sueno_horas": sueno,
            "adherencia_dia": round(_RNG.uniform(0.55, 1.0), 2) if registrado else 0.0,
        }
    resp = httpx.get(
        f"{settings.biometria_url}/biometria/{ascendan_id}/resumen",
        headers={"Authorization": f"Bearer {settings.biometria_token}"},
        params={"dia": dia},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def ahora() -> datetime:
    return datetime.now(timezone.utc)
