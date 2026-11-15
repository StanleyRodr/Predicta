"""Start the API for the Playwright suite on a fresh, seeded PostgreSQL database.

``frontend/playwright.config.ts`` runs this as its backend web server:

1. Use ``E2E_DATABASE_URL``, or the server of ``DATABASE_URL`` (backend/.env)
   with the database ``predicta_e2e``. It is dropped and recreated on every run,
   so the development database is never touched.
2. Migrate it with Alembic.
3. Create the confirmed user ``E2E_EMAIL`` / ``E2E_PASSWORD`` and load the thesis
   dataset (``generar_ventas.py``, seed 2026) through the real ETL.
4. Replace this process with ``uvicorn`` on ``E2E_API_PORT`` (default 8001).

Run from backend/: python scripts/e2e_server.py
"""

import importlib.util
import io
import os
import subprocess
import sys
from pathlib import Path

import psycopg2
from psycopg2 import sql
from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

GENERATOR = ROOT / "DatosDePrueba" / "ventas_fabricadas" / "generar_ventas.py"
DEFAULT_DATABASE = "predicta_e2e"
EMAIL = os.environ.get("E2E_EMAIL", "e2e@example.com")
PASSWORD = os.environ.get("E2E_PASSWORD", "E2ePass1234")
PORT = os.environ.get("E2E_API_PORT", "8001")
WEB_ORIGINS = os.environ.get("E2E_WEB_ORIGINS", "http://127.0.0.1:4173,http://localhost:4173")
MAPPING = {role: role for role in ("producto", "monto", "cantidad", "categoria", "fecha")}


def database_url() -> URL:
    explicit = os.environ.get("E2E_DATABASE_URL")
    if explicit:
        return make_url(explicit)
    from app.core.config import (
        settings,  # needs DATABASE_URL from the environment or backend/.env
    )

    return make_url(settings.database_url).set(database=DEFAULT_DATABASE)


def recreate(url: URL) -> None:
    """Drop and create the database; ``with connection`` is avoided because DROP DATABASE needs autocommit."""
    connection = psycopg2.connect(
        host=url.host, port=url.port or 5432, user=url.username, password=url.password, dbname="postgres"
    )
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s", (url.database,))
            cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(url.database)))
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(url.database)))
    finally:
        connection.close()


def environment(url: URL) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "DATABASE_URL": url.render_as_string(hide_password=False),
            "ENVIRONMENT": "development",
            "CORS_ORIGINS": WEB_ORIGINS,
            "EMAIL_BACKEND": "console",
            "FRONTEND_URL": "http://127.0.0.1:4173",
        }
    )
    env.setdefault("SECRET_KEY", "e2e-only-secret-key-0123456789abcdefghij")
    return env


def seed(url: URL) -> int:
    """Create the confirmed E2E user and load the thesis dataset; return the rows loaded."""
    os.environ["DATABASE_URL"] = url.render_as_string(hide_password=False)
    os.environ.setdefault("SECRET_KEY", "e2e-only-secret-key-0123456789abcdefghij")
    # Without backend/.env (CI) an unset ENVIRONMENT means production, which demands SSL.
    os.environ["ENVIRONMENT"] = "development"
    from app.core.security import get_password_hash
    from app.models import models
    from app.services import etl_service

    spec = importlib.util.spec_from_file_location("generar_ventas", GENERATOR)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    buffer = io.BytesIO()
    generator.build_sales().to_excel(buffer, index=False, sheet_name="ventas")
    contents, file_hash = etl_service.read_limited(io.BytesIO(buffer.getvalue()))

    engine = create_engine(url)
    session = sessionmaker(bind=engine, autoflush=False)()
    try:
        role = session.query(models.Rol).filter(models.Rol.nombre_rol == "Usuario").one()
        user = models.Usuario(
            nombre_usuario="e2e",
            correo_electronico=EMAIL,
            contrasena_hash=get_password_hash(PASSWORD),
            correo_verificado=True,
            id_rol=role.id_rol,
        )
        session.add(user)
        session.commit()
        result = etl_service.load_sales(session, user.id_usuario, "xlsx", contents, file_hash, MAPPING)
    finally:
        session.close()
        engine.dispose()
    return result["registros_cargados"]


def main() -> None:
    url = database_url()
    env = environment(url)
    print(f"E2E: recreando la base {url.database}...", flush=True)
    recreate(url)
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True
    )
    rows = seed(url)
    print(f"E2E: {rows:,} ventas cargadas para {EMAIL}. API en el puerto {PORT}.", flush=True)
    command = [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", PORT]
    # Replace this process, so Playwright stops uvicorn when it stops the server.
    if os.name == "nt":
        sys.exit(subprocess.call(command, cwd=BACKEND, env=env))  # noqa: S603 - fixed command
    os.chdir(BACKEND)
    os.execve(sys.executable, command, env)  # noqa: S606 - fixed command, no user input


if __name__ == "__main__":
    main()
