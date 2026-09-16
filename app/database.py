"""Módulo de conexión y registro de índices de base de datos MongoDB.

Soporta MongoDB real (PyMongo) y fallback automático a mongomock en desarrollo si no hay servidor MongoDB local.
"""
import json
import os
from typing import Any

_mock_db_client = None
DB_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "db_store.json"))


def _save_db_to_disk(raw_db: Any) -> None:
    try:
        store = {}
        for coll_name in raw_db.list_collection_names():
            if coll_name.startswith("system."):
                continue
            docs = []
            for doc in raw_db[coll_name].find():
                d = dict(doc)
                if "_id" in d and not isinstance(d["_id"], (str, int, float, bool)):
                    d["_id"] = str(d["_id"])
                docs.append(d)
            store[coll_name] = docs
        
        tmp_file = f"{DB_FILE}.tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, DB_FILE)
    except Exception as e:
        print(f"[DB Store Warning] Error al guardar datos en disco: {e}")


def _load_db_from_disk(raw_db: Any) -> None:
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                store = json.load(f)
            for coll_name, docs in store.items():
                if docs and isinstance(docs, list):
                    raw_db[coll_name].delete_many({})
                    raw_db[coll_name].insert_many(docs)
            print(f"[DB Store] Datos cargados exitosamente desde {DB_FILE}")
        except Exception as e:
            print(f"[DB Store Warning] Error al cargar datos desde disco: {e}")


class PersistentCollectionProxy:
    def __init__(self, coll: Any, raw_db: Any):
        self._coll = coll
        self._raw_db = raw_db

    def insert_one(self, *args, **kwargs):
        res = self._coll.insert_one(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def insert_many(self, *args, **kwargs):
        res = self._coll.insert_many(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def update_one(self, *args, **kwargs):
        res = self._coll.update_one(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def update_many(self, *args, **kwargs):
        res = self._coll.update_many(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def delete_one(self, *args, **kwargs):
        res = self._coll.delete_one(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def delete_many(self, *args, **kwargs):
        res = self._coll.delete_many(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def find_one_and_update(self, *args, **kwargs):
        res = self._coll.find_one_and_update(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def find_one_and_delete(self, *args, **kwargs):
        res = self._coll.find_one_and_delete(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def replace_one(self, *args, **kwargs):
        res = self._coll.replace_one(*args, **kwargs)
        _save_db_to_disk(self._raw_db)
        return res

    def __getattr__(self, name: str) -> Any:
        return getattr(self._coll, name)


class PersistentDatabaseProxy:
    def __init__(self, raw_db: Any):
        self._raw_db = raw_db

    def __getitem__(self, coll_name: str) -> Any:
        coll = self._raw_db[coll_name]
        return PersistentCollectionProxy(coll, self._raw_db)

    def __getattr__(self, name: str) -> Any:
        if hasattr(self._raw_db, name):
            attr = getattr(self._raw_db, name)
            if callable(attr):
                return attr
            return attr
        return self[name]


def set_mock_db_client(client: Any) -> None:
    global _mock_db_client
    _mock_db_client = client


def use_mock_db() -> Any:
    import mongomock
    client = mongomock.MongoClient()
    raw_db = client["sinergix_crm_test"]
    proxy = PersistentDatabaseProxy(raw_db)
    set_mock_db_client(proxy)
    return proxy


def get_db_client() -> Any:
    global _mock_db_client
    if _mock_db_client is not None:
        return _mock_db_client

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "sinergix_crm")

    from pymongo import MongoClient
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        return client[db_name]
    except Exception:
        # Fallback inteligente a mongomock con persistencia en disco (db_store.json)
        import mongomock
        mock_client = mongomock.MongoClient()
        raw_db = mock_client[db_name]
        _load_db_from_disk(raw_db)
        proxy = PersistentDatabaseProxy(raw_db)
        _mock_db_client = proxy
        return _mock_db_client


def get_db() -> Any:
    return get_db_client()


def init_db_indexes(db: Any) -> None:
    """Crea los índices de Fase 2 y Fase 5 en MongoDB."""
    try:
        # Índices Fase 2 (Leads)
        db.leads.create_index([("sherpa_id", 1), ("creado_en", -1)], name="idx_sherpa_creado_en")
        db.leads.create_index([("sherpa_id", 1), ("etapa_pipeline", 1)], name="idx_sherpa_pipeline_status")
        db.leads.create_index([("sherpa_id", 1), ("clasificacion.lista", 1)], name="idx_sherpa_clasificacion")
        db.leads.create_index([("sherpa_id", 1), ("posicion_red", 1)], name="idx_sherpa_posicion_red")
        db.leads.create_index([("sherpa_id", 1), ("canal_captacion", 1)], name="idx_sherpa_canal_captacion")

        # Índices Fase 5 (Biometría, Platos, Bus Ecosistema)
        db.telemetria_biometrica.create_index([("lead_id", 1), ("timestamp", -1)], name="idx_telemetria_lead_tiempo")
        db.telemetria_biometrica.create_index([("timestamp", -1)], expireAfterSeconds=60*60*24*90, name="idx_ttl_telemetria_90d")

        db.auditorias_platos.create_index([("lead_id", 1), ("sprint_dia", 1)], name="idx_platos_lead_dia")
        db.auditorias_platos.create_index([("analisis_ia.semaforo", 1), ("lead_id", 1)], name="idx_platos_semaforo")

        db.eventos_ecosistema_bus.create_index([("estado_despacho", 1), ("modulo_origen", 1)], name="idx_bus_estado")
        db.eventos_ecosistema_bus.create_index([("creado_en", -1)], expireAfterSeconds=60*60*24*30, name="idx_ttl_bus_30d")
    except Exception as exc:
        print(f"[DB Index Init Warning] {exc}")


def parse_object_id(oid: str) -> Any:
    """Convierte defensivamente un ID a bson.ObjectId si es un hash hexadecimal válido de 24 caracteres."""
    if not oid:
        return oid
    try:
        from bson import ObjectId
        return ObjectId(oid) if ObjectId.is_valid(str(oid)) else oid
    except Exception:
        return oid


def serializar_doc_lead(doc: dict[str, Any]) -> dict[str, Any]:
    """Retorna una copia del documento serializado limpia sin mutar el original en memoria."""
    if not doc:
        return {}
    res = dict(doc)
    res["id"] = str(res.get("_id", res.get("id", "")))
    if "_id" in res and not isinstance(res["_id"], str):
        res.pop("_id", None)
    return res
