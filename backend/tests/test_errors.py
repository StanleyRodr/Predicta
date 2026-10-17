"""Regression tests for public error responses."""

from fastapi import HTTPException

from app.api.etl_routes import clear_history
from app.main import db_healthcheck, engine
from app.models import models


class _BrokenQuery:
    def filter(self, *_args):
        raise RuntimeError("internal database secret")


class _BrokenDatabase:
    def query(self, *_args):
        return _BrokenQuery()

    def rollback(self):
        pass


class _BrokenConnection:
    def __enter__(self):
        raise RuntimeError("internal connection secret")

    def __exit__(self, *_args):
        return False


def test_clear_history_hides_database_error():
    try:
        clear_history(_BrokenDatabase(), models.Usuario(id_usuario=1))
    except HTTPException as error:
        assert error.status_code == 500
        assert error.detail == "No se pudo depurar el historial."
        assert "internal database secret" not in error.detail
    else:
        raise AssertionError("clear_history debe convertir el error en HTTP 500")


def test_db_healthcheck_hides_connection_error(monkeypatch):
    monkeypatch.setattr(engine, "connect", lambda: _BrokenConnection())

    response = db_healthcheck()

    assert response.status_code == 503
    assert "internal connection secret" not in response.body.decode()
    assert "La base de datos no esta disponible." in response.body.decode()
