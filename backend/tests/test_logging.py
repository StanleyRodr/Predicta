"""Logs never carry the values of local variables (audit S-26)."""

import io

import pytest
from loguru import logger

from app.core import security
from app.main import LOG_FORMAT, add_log_sink

SECRET = "ClaveQueNoDebeVerse9"


@pytest.fixture
def captured():
    """The log text written with the app's sink options during the test."""
    buffer = io.StringIO()
    sink_id = add_log_sink(buffer, "DEBUG")
    yield buffer
    logger.remove(sink_id)


def _failing_login(client, monkeypatch):
    def broken(password, hashed):
        raise RuntimeError("fallo simulado al comprobar la contraseña")

    monkeypatch.setattr(security, "verify_password", broken)
    return client.post("/users/login", data={"username": "test@example.com", "password": SECRET})


def test_a_failing_login_logs_the_error_but_not_the_password(client, user_credentials, monkeypatch, captured):
    response = _failing_login(client, monkeypatch)

    assert response.status_code == 500
    text = captured.getvalue()
    assert "RuntimeError: fallo simulado" in text
    assert SECRET not in text


def test_the_default_loguru_options_would_leak_it(client, user_credentials, monkeypatch):
    # Guards the test above: with loguru's defaults the password does appear.
    buffer = io.StringIO()
    sink_id = logger.add(buffer, level="DEBUG", format=LOG_FORMAT)
    try:
        _failing_login(client, monkeypatch)
    finally:
        logger.remove(sink_id)

    assert SECRET in buffer.getvalue()
