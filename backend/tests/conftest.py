"""Shared pytest fixtures and configuration."""

import os

# Keep tests isolated from a developer's database. The application imports its
# engine at module load time, so configure SQLite before importing the app.
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ.setdefault("SECRET_KEY", "test-secret-key")
# Do not inherit a developer's CORS settings from backend/.env.
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.rate_limit import limiter
from app.main import app
from app.models import models

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


def register_and_login(client, nombre_usuario, correo_electronico, password="StrongPass1"):
    """Create a user and return its Bearer headers."""
    credentials = {
        "nombre_usuario": nombre_usuario,
        "correo_electronico": correo_electronico,
        "password": password,
    }
    assert client.post("/users/register", json=credentials).status_code == 201
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
    response = client.post("/users/register", json=credentials)
    assert response.status_code == 201

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
