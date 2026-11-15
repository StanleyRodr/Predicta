"""Measure whether a long upload blocks the other users of the API.

The thesis states that FastAPI, on an asynchronous ASGI server, runs the ETL and
the model fit in worker threads, so one long operation does not block the rest.
This script measures it on the real stack:

1. Recreate a throwaway PostgreSQL database ``predicta_bench`` on the server of
   ``DATABASE_URL`` (backend/.env) and migrate it with Alembic. The development
   database is never touched.
2. Start ``uvicorn`` with one worker, as in production.
3. Register two users and confirm them in the database. User B uploads a small
   file, so its ``GET /analytics/stats`` has data to aggregate.
4. Time ``GET /analytics/stats`` for user B at rest, then while user A uploads the
   full thesis XLSX (about 28,700 rows).
5. Write ``docs/evaluacion/concurrencia.md``, stop the server, drop the database.

Requests are spaced 0.4 s apart so the run stays under the API's own rate limit
(120 per minute per endpoint), which would otherwise answer 429.

Run from backend/: python scripts/measure_concurrency.py
"""

import io
import os
import socket
import statistics
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pandas as pd
import psycopg2
from psycopg2 import sql
from sqlalchemy.engine import make_url

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

BENCH_DB = "predicta_bench"
GENERATOR = ROOT / "DatosDePrueba" / "ventas_fabricadas" / "generar_ventas.py"
OUTPUT = ROOT / "docs" / "evaluacion" / "concurrencia.md"
INTERVAL = 0.4
IDLE_SAMPLES = 30
PASSWORD = "BenchPass123"  # noqa: S105 - throwaway users of a throwaway database
MAPPING = '{"producto": "producto", "monto": "monto", "cantidad": "cantidad", "categoria": "categoria", "fecha": "fecha"}'


def _base_url() -> str:
    """DATABASE_URL from the environment or backend/.env, as the app reads it."""
    from app.core.config import settings  # imported late: it needs backend/.env

    return settings.database_url


def _admin_connection(url):
    connection = psycopg2.connect(
        host=url.host, port=url.port or 5432, user=url.username, password=url.password, dbname="postgres"
    )
    connection.autocommit = True
    return connection


def _drop(cursor) -> None:
    cursor.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s", (BENCH_DB,))
    cursor.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(BENCH_DB)))


def recreate_database(url) -> None:
    # ``with connection`` would open a transaction, where DROP/CREATE DATABASE fail.
    connection = _admin_connection(url)
    try:
        with connection.cursor() as cursor:
            _drop(cursor)
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(BENCH_DB)))
    finally:
        connection.close()


def drop_database(url) -> None:
    connection = _admin_connection(url)
    try:
        with connection.cursor() as cursor:
            _drop(cursor)
    finally:
        connection.close()


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _environment(database_url: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "DATABASE_URL": database_url,
            "ENVIRONMENT": "development",
            "EMAIL_BACKEND": "console",
            "FRONTEND_URL": "http://localhost:5173",
            "LOG_LEVEL": "WARNING",
        }
    )
    return env


def _wait_until_up(base: str, server: subprocess.Popen) -> None:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise RuntimeError("uvicorn terminó antes de responder")
        try:
            if httpx.get(f"{base}/health", timeout=1).status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.3)
    raise RuntimeError("uvicorn no respondió en 60 s")


def _verified_user(client: httpx.Client, database_url: str, name: str) -> dict[str, str]:
    email = f"{name}@example.com"
    response = client.post(
        "/users/register", json={"nombre_usuario": name, "correo_electronico": email, "password": PASSWORD}
    )
    response.raise_for_status()
    url = make_url(database_url)
    connection = psycopg2.connect(
        host=url.host, port=url.port or 5432, user=url.username, password=url.password, dbname=BENCH_DB
    )
    try:
        with connection, connection.cursor() as cursor:
            cursor.execute("UPDATE usuarios SET correo_verificado = TRUE WHERE correo_electronico = %s", (email,))
    finally:
        connection.close()
    token = client.post("/users/login", data={"username": email, "password": PASSWORD})
    token.raise_for_status()
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


def _xlsx(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_excel(buffer, index=False, sheet_name="ventas")
    return buffer.getvalue()


def _upload(client: httpx.Client, headers: dict[str, str], contents: bytes) -> httpx.Response:
    return client.post(
        "/etl/upload-ventas",
        headers=headers,
        data={"mapeo": MAPPING},
        files={"file": ("ventas.xlsx", contents, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        timeout=300,
    )


def _sample(client: httpx.Client, headers: dict[str, str]) -> tuple[float, int]:
    start = time.perf_counter()
    response = client.get("/analytics/stats", headers=headers)
    return (time.perf_counter() - start) * 1000, response.status_code


def _summary(samples: list[tuple[float, int]]) -> dict[str, float | int]:
    times = sorted(ms for ms, _ in samples)
    return {
        "n": len(times),
        "p50": statistics.median(times),
        "p95": times[min(len(times) - 1, round(0.95 * (len(times) - 1)))],
        "max": times[-1],
        "errores": sum(1 for _, status in samples if status != 200),
    }


def measure(base: str, database_url: str, sales: pd.DataFrame) -> dict:
    with httpx.Client(base_url=base, timeout=60) as client:
        user_a = _verified_user(client, database_url, "bench_a")
        user_b = _verified_user(client, database_url, "bench_b")
        small = _upload(client, user_b, _xlsx(sales.head(500)))
        small.raise_for_status()

        idle = []
        for _ in range(IDLE_SAMPLES):
            idle.append(_sample(client, user_b))
            time.sleep(INTERVAL)

    big = _xlsx(sales)
    result: dict = {}

    def upload_in_background() -> None:
        with httpx.Client(base_url=base) as uploader:
            start = time.perf_counter()
            response = _upload(uploader, user_a, big)
            result["upload_ms"] = (time.perf_counter() - start) * 1000
            result["upload_status"] = response.status_code
            result["upload_rows"] = response.json().get("registros_cargados")

    worker = threading.Thread(target=upload_in_background)
    during = []
    with httpx.Client(base_url=base, timeout=60) as client:
        worker.start()
        time.sleep(0.5)  # let the upload reach the server first
        while worker.is_alive():
            during.append(_sample(client, user_b))
            time.sleep(INTERVAL)
    worker.join()
    return {"reposo": _summary(idle), "durante": _summary(during), **result}


def write_report(data: dict, rows: int) -> None:
    rest, busy = data["reposo"], data["durante"]

    def row(label: str, values: dict) -> str:
        return (
            f"| {label} | {values['n']} | {values['p50']:.1f} | {values['p95']:.1f} | "
            f"{values['max']:.1f} | {values['errores']} |"
        )

    ratio = busy["p50"] / rest["p50"] if rest["p50"] else float("nan")
    blocked = busy["max"] >= data["upload_ms"] * 0.9 or busy["n"] == 0
    verdict = (
        f"Al menos una solicitud de B esperó casi toda la carga ({busy['max'] / 1000:.1f} s): hubo bloqueo."
        if blocked
        else (
            f"Ninguna solicitud de B esperó a que terminara la carga (la más lenta tardó "
            f"{busy['max'] / 1000:.2f} s de {data['upload_ms'] / 1000:.1f} s): el servidor siguió atendiendo "
            "a B mientras procesaba el archivo de A en un hilo de trabajo. La latencia sí sube, porque B "
            "comparte la CPU (y el GIL de Python) con el ETL."
        )
    )
    OUTPUT.write_text(
        f"""# Concurrencia: una carga larga frente a otras solicitudes

Generado por `backend/scripts/measure_concurrency.py` el {datetime.now(UTC):%Y-%m-%d %H:%M} UTC.

**Entorno:** `uvicorn` con 1 worker (como en producción), PostgreSQL local en la base
desechable `{BENCH_DB}`, cliente y servidor en la misma máquina (sin latencia de red).

**Prueba:** el usuario A sube el XLSX de la tesis ({rows:,} filas) mientras el usuario B
consulta `GET /analytics/stats` cada {INTERVAL} s. Se compara con B consultando en reposo.

La carga de A tardó **{data['upload_ms'] / 1000:.1f} s** (estado {data['upload_status']},
{data['upload_rows']:,} filas cargadas).

| Momento | n | p50 (ms) | p95 (ms) | Máximo (ms) | Respuestas distintas de 200 |
|---|---|---|---|---|---|
{row("En reposo", rest)}
{row("Durante la carga de A", busy)}

Durante la carga, la mediana de B fue {ratio:.1f} veces la de reposo. {verdict}

`SIN UMBRAL`: la tesis no fija una latencia máxima; los valores se reportan sin aprobar
ni reprobar. Una ejecución en otra máquina dará otros números.
""",
        encoding="utf-8",
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    base_url = make_url(_base_url())
    bench_url = base_url.set(database=BENCH_DB).render_as_string(hide_password=False)

    import importlib.util

    spec = importlib.util.spec_from_file_location("generar_ventas", GENERATOR)
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    sales = generator.build_sales()

    print(f"Recreando la base {BENCH_DB}...")
    recreate_database(base_url)
    env = _environment(bench_url)
    server = None
    try:
        subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, env=env, check=True,
            capture_output=True,
        )
        port = _free_port()
        base = f"http://127.0.0.1:{port}"
        server = subprocess.Popen(  # noqa: S603 - fixed command, no user input
            [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--workers", "1"],
            cwd=BACKEND, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        _wait_until_up(base, server)
        print(f"Midiendo en {base}...")
        data = measure(base, bench_url, sales)
    finally:
        if server is not None:
            server.terminate()
            server.wait(timeout=30)
        drop_database(base_url)
        print(f"Base {BENCH_DB} eliminada.")

    write_report(data, len(sales))
    rest, busy = data["reposo"], data["durante"]
    print(f"Reposo p50 {rest['p50']:.1f} ms, p95 {rest['p95']:.1f} ms")
    print(f"Durante p50 {busy['p50']:.1f} ms, p95 {busy['p95']:.1f} ms (n={busy['n']}), carga {data['upload_ms'] / 1000:.1f} s")
    print(f"-> {OUTPUT}")


if __name__ == "__main__":
    main()
