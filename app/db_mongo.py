"""Capa de datos MongoDB en servidor propio (Enmienda 2).

Única fuente de verdad del CRM para colecciones:
- leads
- sherpas
- plantillas_hsm
- eventos_procesados (idempotencia y deduplicación)
- reportes_cache
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from .config import settings

logger = logging.getLogger(__name__)

# Memoria local de respaldo para dev/tests sin servidor MongoDB activo
_mock_db: Dict[str, List[Dict[str, Any]]] = {
    "leads": [],
    "sherpas": [],
    "plantillas_hsm": [],
    "eventos_procesados": [],
    "reportes_cache": []
}

_mongo_client = None
_mongo_db = None


def get_mongo_db():
    """Obtiene la instancia de la base de datos MongoDB o retorna el conector mock en dev."""
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db

    try:
        from pymongo import MongoClient
        client = MongoClient(settings.mongodb_url, serverSelectionTimeoutMS=2000)
        # Test connection
        client.admin.command('ping')
        _mongo_client = client
        _mongo_db = client[settings.mongodb_db_name]
        init_mongo_indexes(_mongo_db)
        logger.info(f"MongoDB conectado exitosamente a {settings.mongodb_url}/{settings.mongodb_db_name}")
        return _mongo_db
    except Exception as e:
        logger.warning(f"MongoDB no disponible en {settings.mongodb_url}, usando motor en memoria (dev/tests): {e}")
        return None


def init_mongo_indexes(db):
    """Inicializa los índices requeridos en MongoDB (Enmienda 1 y 2)."""
    if db is None:
        return
    try:
        # Leads
        db.leads.create_index("telefono", unique=True)
        db.leads.create_index("sherpa_id")
        
        # Sherpas
        db.sherpas.create_index("google_sub", unique=True, sparse=True)
        db.sherpas.create_index("api_token", unique=True, sparse=True)
        
        # Eventos procesados (Idempotencia de Pagos & Deduplicación)
        db.eventos_procesados.create_index("event_id", unique=True, sparse=True)
        db.eventos_procesados.create_index(
            [("lead_id", 1), ("tipo_evento", 1), ("ventana", 1)],
            unique=True,
            name="idx_dedup_concurso"
        )
        logger.info("Índices de MongoDB asegurados correctamente.")
    except Exception as err:
        logger.warning(f"Advertencia al crear índices en MongoDB: {err}")


def save_evento_procesado(evento_data: Dict[str, Any]) -> bool:
    """Guarda un evento procesado para idempotencia/deduplicación. Retorna True si se guardó, False si era duplicado."""
    db = get_mongo_db()
    event_id = evento_data.get("event_id")
    dedup_key = f"{evento_data.get('lead_id')}_{evento_data.get('tipo_evento')}_{evento_data.get('ventana')}"

    if db is not None:
        try:
            # Check duplicate by event_id or dedup composite
            if event_id and db.eventos_procesados.find_one({"event_id": event_id}):
                return False
            if db.eventos_procesados.find_one({
                "lead_id": evento_data.get("lead_id"),
                "tipo_evento": evento_data.get("tipo_evento"),
                "ventana": evento_data.get("ventana")
            }):
                return False

            evento_data["creado_en"] = datetime.now(timezone.utc).isoformat()
            db.eventos_procesados.insert_one(evento_data)
            return True
        except Exception as e:
            logger.warning(f"Error al insertar evento en MongoDB: {e}")
            return False
    else:
        # Fallback mock memory
        for ev in _mock_db["eventos_procesados"]:
            if event_id and ev.get("event_id") == event_id:
                return False
            if ev.get("lead_id") == evento_data.get("lead_id") and ev.get("tipo_evento") == evento_data.get("tipo_evento") and ev.get("ventana") == evento_data.get("ventana"):
                return False
        
        evento_data["creado_en"] = datetime.now(timezone.utc).isoformat()
        _mock_db["eventos_procesados"].append(evento_data)
        return True


def get_leads_by_sherpa(sherpa_id: str) -> List[Dict[str, Any]]:
    """Obtiene los leads pertenecientes a un sherpa específico (Enmienda 4)."""
    db = get_mongo_db()
    if db is not None:
        try:
            cursor = db.leads.find({"sherpa_id": sherpa_id})
            return list(cursor)
        except Exception as e:
            logger.warning(f"Error al leer leads en MongoDB: {e}")
            return []
    else:
        return [l for l in _mock_db["leads"] if str(l.get("sherpa_id")) == str(sherpa_id)]
