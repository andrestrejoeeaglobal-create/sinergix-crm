"""Módulo de capa de datos desacoplado (ENMIENDA 2 — MongoDB en Servidor Propio).

Redirige a app.database para operaciones en MongoDB (soporta mongomock en memoria para suite de tests).
"""
from .database import get_db, get_db_client, init_db_indexes, use_mock_db


def init_db() -> None:
    """Inicializa conexión e índices de MongoDB."""
    db = get_db_client()
    init_db_indexes(db)


class _SessionLocalMock:
    """Simulador de sesión para tests legacy que importan SessionLocal."""
    def __init__(self):
        self.db = get_db_client()

    def add(self, obj):
        pass

    def commit(self):
        pass

    def close(self):
        pass


def SessionLocal():
    return _SessionLocalMock()
