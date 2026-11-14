"""Shared pytest fixtures and configuration."""

import os

# Keep tests isolated from a developer's database. The application imports its
# engine at module load time, so configure SQLite before importing the app.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-0123456789")
# Do not inherit a developer's CORS settings from backend/.env.
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"
os.environ["TRUSTED_PROXIES"] = "127.0.0.1"
# E-mails are captured by the ``outbox`` fixture, never sent.
os.environ["EMAIL_BACKEND"] = "console"
os.environ["FRONTEND_URL"] = "http://localhost:5173"

import re
from email.message import EmailMessage

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.rate_limit import limiter
from app.main import app
from app.models import models
from app.services import email_service

# Set it to a disposable PostgreSQL database to run the suite on the production
# engine; every table in it is emptied before each test.
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")


def _seed_roles(session_factory):
    """Insert the same roles that migration 0001 seeds."""
    with session_factory() as session:
        session.add_all([models.Rol(nombre_rol="Administrador"), models.Rol(nombre_rol="Usuario")])
        session.commit()


@pytest.fixture(scope="session")
def postgres_engine():
    """One schema for the whole session on ``TEST_DATABASE_URL``."""
    if not TEST_DATABASE_URL:
        pytest.skip("TEST_DATABASE_URL no está definido.")
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(request):
    """Provide an empty database per test: in-memory SQLite, or PostgreSQL if configured."""
    if TEST_DATABASE_URL:
        engine = request.getfixturevalue("postgres_engine")
        tables = ", ".join(table.name for table in Base.metadata.sorted_tables)
        with engine.begin() as connection:
            connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
        session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        _seed_roles(session_factory)
        yield session_factory
        return

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    _seed_roles(session_factory)
    yield session_factory
    Base.metadata.drop_all(bind=engine)


# Every message the app tried to send during the current test.
SENT: list[EmailMessage] = []
TOKEN_IN_LINK = re.compile(r"#token=([A-Za-z0-9_-]+)")


@pytest.fixture(autouse=True)
def outbox(monkeypatch):
    """Capture e-mails instead of delivering them; returns the list of messages."""
    SENT.clear()
    monkeypatch.setattr(email_service, "_deliver", SENT.append)
    yield SENT
    SENT.clear()


def last_token(to):
    """Token of the newest link e-mailed to ``to``."""
    for message in reversed(SENT):
        if message["To"] == to:
            match = TOKEN_IN_LINK.search(message.get_content())
            if match:
                return match.group(1)
    raise AssertionError(f"No hay enlace enviado a {to}")


def confirm_email(client, correo_electronico):
    """Open the newest link e-mailed to the address, as its owner would."""
    response = client.post("/users/verificacion/confirmar", json={"token": last_token(correo_electronico)})
    assert response.status_code == 200, response.text


def register_verified(client, credentials):
    """Register ``credentials`` and confirm the e-mail."""
    assert client.post("/users/register", json=credentials).status_code == 201
    confirm_email(client, credentials["correo_electronico"].strip().lower())


def register_and_login(client, nombre_usuario, correo_electronico, password="StrongPass1"):
    """Create a verified user and return its Bearer headers."""
    credentials = {
        "nombre_usuario": nombre_usuario,
        "correo_electronico": correo_electronico,
        "password": password,
    }
    register_verified(client, credentials)
    login = client.post("/users/login", data={"username": correo_electronico, "password": password})
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def second_user(client):
    """Bearer headers of a second user, distinct from ``auth_headers``."""
    return register_and_login(client, "second_user", "second@example.com")


@pytest.fixture(scope="function")
def client(test_db):
    """Provide a TestClient with overridden database dependency."""
    def override_get_db():
        db = test_db()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        limiter.enabled = True
        app.dependency_overrides.clear()


@pytest.fixture
def user_credentials(client):
    """Create and authenticate an isolated test user."""
    credentials = {
        "nombre_usuario": "test_user",
        "correo_electronico": "test@example.com",
        "password": "StrongPass1",
    }
    register_verified(client, credentials)

    login = client.post(
        "/users/login",
        data={"username": credentials["correo_electronico"], "password": credentials["password"]},
    )
    assert login.status_code == 200
    return credentials


@pytest.fixture
def auth_headers(client, user_credentials):
    """Return Bearer headers for the isolated test user."""
    login = client.post(
        "/users/login",
        data={
            "username": user_credentials["correo_electronico"],
            "password": user_credentials["password"],
        },
    )
    assert login.status_code == 200
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


class FakeClock:
    """Replaces ``security.utcnow``; ``advance`` moves time forward."""

    def __init__(self):
        from datetime import UTC, datetime

        # Real time at start: PyJWT checks "exp" against the real clock.
        self.now = datetime.now(UTC)

    def __call__(self):
        return self.now

    def advance(self, **delta):
        from datetime import timedelta

        self.now += timedelta(**delta)


@pytest.fixture
def clock(monkeypatch):
    """A controllable clock for lockouts and link expiry (one source of time)."""
    from app.core import security

    fake = FakeClock()
    monkeypatch.setattr(security, "utcnow", fake)
    return fake
