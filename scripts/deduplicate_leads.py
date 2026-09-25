#!/usr/bin/env python3
"""scripts/deduplicate_leads.py — Deduplicación Canónica de Leads en MongoDB.

Regla de Integridad (Etapa 2.2):
  Un lead es único por combinación de (sherpa_id, telefono_normalizado).
  Este script normaliza los teléfonos a los últimos 10 dígitos, detecta
  duplicados por Sherpa y conserva únicamente el registro más reciente
  (según updated_at / actualizado_en), eliminando copias redundantes previo
  a la creación del índice único compuesto.

Uso:
  python scripts/deduplicate_leads.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.db_mongo import get_mongo_db, _mock_db


def normalizar_telefono(telefono: str) -> str:
    """Extrae solo dígitos y devuelve los últimos 10 caracteres nacionales."""
    if not telefono:
        return ""
    digitos = re.sub(r"\D", "", str(telefono))
    return digitos[-10:] if len(digitos) >= 10 else digitos


def parse_date(date_val) -> datetime:
    """Parsea una fecha de MongoDB / mock a datetime UTC para comparación."""
    if isinstance(date_val, datetime):
        return date_val if date_val.tzinfo else date_val.replace(tzinfo=timezone.utc)
    if isinstance(date_val, str) and date_val:
        try:
            return datetime.fromisoformat(date_val.replace("Z", "+00:00"))
        except Exception:
            pass
    return datetime.min.replace(tzinfo=timezone.utc)


def deduplicar_coleccion_leads() -> dict:
    """Escanea la colección de leads, normaliza teléfonos y elimina duplicados más antiguos."""
    db = get_mongo_db()
    stats = {"procesados": 0, "normalizados": 0, "duplicados_eliminados": 0}

    print("[*] Iniciando proceso de deduplicación canónica de leads...")

    if db is not None:
        leads_cursor = db.leads.find({})
        todos_leads = list(leads_cursor)
    else:
        todos_leads = list(_mock_db.get("leads", []))

    stats["procesados"] = len(todos_leads)
    grupos = {}

    for lead in todos_leads:
        doc_id = lead.get("_id") or lead.get("id")
        sherpa_id = str(lead.get("sherpa_id") or "101")
        tel_raw = lead.get("telefono") or ""
        tel_norm = normalizar_telefono(tel_raw)

        # Actualizar teléfono normalizado si falta
        if lead.get("telefono_normalizado") != tel_norm and tel_norm:
            if db is not None:
                db.leads.update_one({"_id": doc_id}, {"$set": {"telefono_normalizado": tel_norm}})
            else:
                lead["telefono_normalizado"] = tel_norm
            stats["normalizados"] += 1

        if not tel_norm:
            continue

        clave = (sherpa_id, tel_norm)
        if clave not in grupos:
            grupos[clave] = []
        grupos[clave].append(lead)

    # Identificar y resolver duplicados por grupo
    for clave, items in grupos.items():
        if len(items) > 1:
            # Ordenar por fecha más reciente
            items_ordenados = sorted(
                items,
                key=lambda x: parse_date(x.get("updated_at") or x.get("actualizado_en") or x.get("creado_en")),
                reverse=True
            )
            # Conservar el primero (más reciente), eliminar el resto
            conservado = items_ordenados[0]
            duplicados = items_ordenados[1:]

            for dup in duplicados:
                dup_id = dup.get("_id") or dup.get("id")
                print(f"[-] Eliminando lead duplicado id={dup_id} para Sherpa={clave[0]} Tel={clave[1]}")
                if db is not None:
                    db.leads.delete_one({"_id": dup_id})
                else:
                    if dup in _mock_db["leads"]:
                        _mock_db["leads"].remove(dup)
                stats["duplicados_eliminados"] += 1

    print(f"[+] Deduplicación finalizada: {stats['procesados']} procesados, "
          f"{stats['normalizados']} normalizados, {stats['duplicados_eliminados']} duplicados eliminados.")
    return stats


if __name__ == "__main__":
    deduplicar_coleccion_leads()
