"""Settings, password hashing, roles, duplicate races, and download headers."""

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

import pytest
from pydantic import ValidationError

from app.api.analytics_routes import content_disposition
from app.core import security
from app.core.config import DEFAULT_CORS_ORIGINS, DEFAULT_TRUSTED_PROXIES, SECRET_KEY_PLACEHOLDER, Settings
from app.models import models
from app.schemas import schemas
from app.services import user_service

BACKEND = Path(__file__).resolve().parents[1]

# Made with passlib 1.7.4 + bcrypt 4.0.1, before passlib was removed.
LEGACY_HASHES = {
    "StrongPass1": "$2b$12$Rjlq2Xfd6HVGNScB.J8Bru5zs6lPFZACOgxa.sZIFmmqXKw2MJdpC",
    "Contraseña1é": "$2b$12$VFfNFo0nryXHVetMEUNi3uBO44BGMmIRZulh1YK4iA.sUSIWBLtrK",
}


STRONG_SECRET = "a" * 32
SSL_DATABASE_URL = "postgresql+psycopg2://u:p@db.example/predicta?sslmode=require"


def _settings(**values):
    """Settings that pass every production rule unless a test overrides one."""
    base = {"database_url": SSL_DATABASE_URL, "secret_key": STRONG_SECRET, "_env_file": None}
    return Settings(**{**base, **values})


# --------------------------------------------------------------- settings


def test_cors_defaults_to_the_vite_origin(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert _settings().cors_origins == DEFAULT_CORS_ORIGINS == ["http://localhost:5173"]


def test_cors_origins_are_split_on_commas():
    settings = _settings(cors_origins=" http://a.test , http://b.test,")
    assert settings.cors_origins == ["http://a.test", "http://b.test"]


@pytest.mark.parametrize("environment", ["production", "test"])
def test_wildcard_cors_is_rejected_outside_development(environment):
    with pytest.raises(ValidationError, match="solo se permite con ENVIRONMENT=development"):
        _settings(cors_origins="*", environment=environment)


def test_wildcard_cors_is_allowed_in_development():
    assert _settings(cors_origins="*", environment="development").cors_origins == ["*"]


def test_unset_environment_means_production(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    assert _settings().environment == "production"


@pytest.mark.parametrize("secret", ["x", "a" * 31, SECRET_KEY_PLACEHOLDER])
def test_production_rejects_a_weak_secret(secret):
    with pytest.raises(ValidationError, match="SECRET_KEY debe tener al menos 32"):
        _settings(secret_key=secret, environment="production")


@pytest.mark.parametrize("environment", ["development", "test"])
def test_weak_secret_is_accepted_outside_production(environment):
    assert _settings(secret_key="x", environment=environment).secret_key == "x"


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg2://u:p@db.example/predicta",
        "postgresql+psycopg2://u:p@db.example/predicta?sslmode=prefer",
        "postgresql+psycopg2://u:p@db.example/predicta?sslmode=disable",
        "sqlite:///:memory:",
    ],
)
def test_production_requires_ssl_to_the_database(url):
    with pytest.raises(ValidationError, match="sslmode=require"):
        _settings(database_url=url, environment="production")


@pytest.mark.parametrize(
    "url",
    [
        SSL_DATABASE_URL,
        "postgresql+psycopg2://u:p@db.example/predicta?sslmode=verify-full",
        # Neon's connection string.
        "postgresql+psycopg2://u:p@ep-x.neon.tech/predicta?sslmode=require&channel_binding=require",
    ],
)
def test_production_accepts_secure_ssl_modes(url):
    assert _settings(database_url=url, environment="production").database_url == url


def test_database_without_ssl_is_accepted_in_development():
    assert _settings(database_url="sqlite:///:memory:", environment="development")


def test_trusted_proxies_default_to_localhost_and_split_on_commas(monkeypatch):
    monkeypatch.delenv("TRUSTED_PROXIES", raising=False)
    assert _settings().trusted_proxies == DEFAULT_TRUSTED_PROXIES == ["127.0.0.1"]
    assert _settings(trusted_proxies=" 10.0.0.1, 10.0.0.0/8 ,").trusted_proxies == ["10.0.0.1", "10.0.0.0/8"]


def test_app_refuses_to_start_with_wildcard_cors_in_production():
    env = {
        **os.environ,
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "x",
        "ENVIRONMENT": "production",
        "CORS_ORIGINS": "*",
    }
    result = subprocess.run(
        [sys.executable, "-c", "import app.main"],
        check=False,
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert "solo se permite con ENVIRONMENT=development" in result.stderr


def test_only_config_reads_the_environment():
    offenders = [
        str(path.relative_to(BACKEND))
        for path in (BACKEND / "app").rglob("*.py")
        if path.name != "config.py"
        and any(token in path.read_text(encoding="utf-8") for token in ("os.getenv", "os.environ", "load_dotenv"))
    ]
    assert offenders == []


def test_env_example_holds_only_placeholders():
    example = (BACKEND / ".env.example").read_text(encoding="utf-8")
    values = dict(
        line.split("=", 1) for line in example.splitlines() if line and not line.startswith("#")
    )
    assert set(values) == {
        "DATABASE_URL",
        "SECRET_KEY",
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "ENVIRONMENT",
        "CORS_ORIGINS",
        "LOG_LEVEL",
        "MAX_UPLOAD_ROWS",
        "TRUSTED_PROXIES",
    }
    assert "CHANGE_ME" in values["DATABASE_URL"]
    assert values["SECRET_KEY"].startswith("CHANGE_ME")


# --------------------------------------------------------------- passwords


@pytest.mark.parametrize(("password", "hashed"), LEGACY_HASHES.items())
def test_hashes_created_with_passlib_still_validate(password, hashed):
    assert security.verify_password(password, hashed)
    assert not security.verify_password(password + "x", hashed)


def test_existing_account_logs_in_with_its_old_hash(client, test_db):
    with test_db() as session:
        role = session.query(models.Rol).filter_by(nombre_rol="Usuario").one()
        session.add(
            models.Usuario(
                nombre_usuario="legado",
                correo_electronico="legado@example.com",
                contrasena_hash=LEGACY_HASHES["StrongPass1"],
                id_rol=role.id_rol,
            )
        )
        session.commit()

    response = client.post("/users/login", data={"username": "legado@example.com", "password": "StrongPass1"})
    assert response.status_code == 200


def test_new_hash_round_trips():
    hashed = security.get_password_hash("Contraseña1é")
    assert hashed.startswith("$2b$12$")
    assert security.verify_password("Contraseña1é", hashed)


def test_malformed_hash_never_matches():
    assert not security.verify_password("StrongPass1", "not-a-hash")


def test_password_limit_counts_bytes_not_characters(client):
    # 37 characters but 71 bytes: "é" takes 2 bytes in UTF-8.
    fits = "Aa1" + "é" * 34
    # 38 characters, 73 bytes.
    too_long = "Aa1" + "é" * 35
    assert len(fits.encode()) == 71 and len(too_long.encode()) == 73

    accepted = client.post(
        "/users/register",
        json={"nombre_usuario": "cabe", "correo_electronico": "cabe@example.com", "password": fits},
    )
    rejected = client.post(
        "/users/register",
        json={"nombre_usuario": "largo", "correo_electronico": "largo@example.com", "password": too_long},
    )

    assert accepted.status_code == 201
    assert rejected.status_code == 422
    assert "72 bytes" in rejected.text
    login = client.post("/users/login", data={"username": "cabe@example.com", "password": fits})
    assert login.status_code == 200


def test_hashing_refuses_more_than_72_bytes():
    with pytest.raises(ValueError):
        security.get_password_hash("Aa1" + "é" * 35)
    assert not security.verify_password("a" * 73, security.get_password_hash("a" * 72))


# --------------------------------------------------------------- roles


def test_new_users_get_the_role_by_name_whatever_the_insertion_order(client, test_db):
    with test_db() as session:
        session.query(models.Rol).delete()
        session.add_all([models.Rol(id_rol=7, nombre_rol="Usuario"), models.Rol(id_rol=3, nombre_rol="Administrador")])
        session.commit()

    response = client.post(
        "/users/register",
        json={"nombre_usuario": "orden", "correo_electronico": "orden@example.com", "password": "StrongPass1"},
    )

    assert response.status_code == 201
    assert response.json()["id_rol"] == 7


def test_missing_default_role_is_a_clear_error(test_db):
    with test_db() as session:
        session.query(models.Rol).delete()
        session.commit()
        payload = schemas.UserCreate(
            nombre_usuario="sinrol", correo_electronico="sinrol@example.com", password="StrongPass1"
        )
        with pytest.raises(user_service.MissingRoleError):
            user_service.create_user(session, payload)


# --------------------------------------------------------------- races


def _skip_duplicate_checks(monkeypatch):
    """Simulate a concurrent request that passed the checks before the other committed."""
    monkeypatch.setattr(user_service, "get_user_by_email", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(user_service, "get_user_by_username", lambda *_args, **_kwargs: None)


def test_register_collision_answers_400(client, user_credentials, monkeypatch):
    _skip_duplicate_checks(monkeypatch)

    response = client.post("/users/register", json=user_credentials)

    assert response.status_code == 400
    assert "ya se encuentra registrado" in response.json()["detail"]


def test_profile_collision_answers_400(client, auth_headers, monkeypatch):
    other = {"nombre_usuario": "otra", "correo_electronico": "otra@example.com", "password": "StrongPass1"}
    assert client.post("/users/register", json=other).status_code == 201
    _skip_duplicate_checks(monkeypatch)

    response = client.put("/users/me", headers=auth_headers, json={"correo_electronico": other["correo_electronico"]})

    assert response.status_code == 400
    assert "ya se encuentra registrado" in response.json()["detail"]
    # The rolled-back session still serves the user.
    assert client.get("/users/me", headers=auth_headers).json()["correo_electronico"] == "test@example.com"


# --------------------------------------------------------------- downloads


def test_content_disposition_keeps_an_ascii_fallback_and_the_utf8_name():
    header = content_disposition("Reporte_Ventas_José Núñez.xlsx")

    assert header.startswith('attachment; filename="Reporte_Ventas_Jose_Nunez.xlsx"; ')
    encoded = header.split("filename*=UTF-8''", 1)[1]
    assert unquote(encoded) == "Reporte_Ventas_José Núñez.xlsx"
    header.encode("latin-1")  # HTTP headers must be Latin-1 safe.


def test_report_download_works_for_an_accented_username(client):
    credentials = {"nombre_usuario": "josé_ñ", "correo_electronico": "jose@example.com", "password": "StrongPass1"}
    assert client.post("/users/register", json=credentials).status_code == 201
    token = client.post(
        "/users/login", data={"username": credentials["correo_electronico"], "password": credentials["password"]}
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    upload = client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", b"producto,monto,categoria,fecha\nPan,10.5,Abarrotes,2025-01-02", "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    response = client.get("/analytics/export/excel", headers=headers)

    assert response.status_code == 200
    disposition = response.headers["content-disposition"]
    assert 'filename="Reporte_Ventas_jose_n.xlsx"' in disposition
    assert unquote(disposition.split("filename*=UTF-8''", 1)[1]) == "Reporte_Ventas_josé_ñ.xlsx"
