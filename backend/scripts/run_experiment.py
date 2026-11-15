"""Run the thesis experiment end to end and record its metrics with a date.

Phases (``docs/checking/VERIFICACION_TESIS.md`` §7):

1. Ingestion: generate the synthetic dataset with
   ``DatosDePrueba/ventas_fabricadas/generar_ventas.py`` (seed 2026).
2. Backend: load it through the real ETL (``etl_service.load_sales``, with the
   column mapping) and fit the monthly model (``analytics_service.monthly_projection``).
3. Metrics: write ``docs/resultados/metricas_AAAA-MM-DD.json`` with the commit,
   the seed, the dataset parameters, the model metrics, the MAE of each
   reference forecast, the coefficients, and the hypothesis result.
4. Frontend: covered by the Playwright suite (``frontend/e2e``), which renders the
   same API response in a browser.

Everything runs on an in-memory SQLite database built from the ORM models, so
no server or external database is needed and every run is reproducible. The
schema is created with ``create_all`` only here, inside this throwaway
database; the application itself is migrated by Alembic.

Hypothesis (author's decision of 2026-11-14): the regression wins when its WAPE
on amounts, one month ahead, is below the WAPE of the best of the three
reference forecasts. The MAPE is also graded on Lewis's (1982) scale.

Run from backend/: python scripts/run_experiment.py [--output-dir DIR] [--fecha AAAA-MM-DD]
"""

import argparse
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any

# The application settings require these before any app import; the experiment
# never touches a real database.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "experiment-only-secret-key-0123456789abcdef")
os.environ.setdefault("ENVIRONMENT", "test")

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.ml_models.evaluation import (
    BASELINES,
    RUNTIME_ORIGINS,
    baseline_model,
    point_metrics,
    rolling_origin,
)
from app.ml_models.forecast import MIN_MONTHS, TARGETS
from app.models import models
from app.services import analytics_service, etl_service
from app.services.prediction_service import forecast_payload

GENERATOR = ROOT / "DatosDePrueba" / "ventas_fabricadas" / "generar_ventas.py"
OUTPUT_DIR = ROOT / "docs" / "resultados"
MAPPING = {role: role for role in ("producto", "monto", "cantidad", "categoria", "fecha")}
MAIN_TARGET = "monto"
# Lewis, C. D. (1982). Industrial and Business Forecasting Methods. Butterworths.
LEWIS_SCALE = ((10.0, "muy precisa"), (20.0, "buena"), (50.0, "razonable"))


def load_generator():
    spec = importlib.util.spec_from_file_location("generar_ventas", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def lewis_grade(mape: float | None) -> str | None:
    """Lewis's accuracy band for a MAPE in percent."""
    if mape is None:
        return None
    for limit, label in LEWIS_SCALE:
        if mape < limit:
            return label
    return "imprecisa"


def git_commit() -> dict[str, Any]:
    """The code version, and whether the working tree had uncommitted changes."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],  # noqa: S607 - git from PATH, fixed arguments, no user input
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"],  # noqa: S607 - git from PATH, fixed arguments, no user input
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "cambios_sin_commit": None}
    return {"commit": commit, "cambios_sin_commit": bool(status.strip())}


def _session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autoflush=False)()


def _experiment_user(db: Session) -> int:
    role = models.Rol(nombre_rol="Usuario")
    db.add(role)
    db.flush()
    user = models.Usuario(
        nombre_usuario="experimento",
        correo_electronico="experimento@example.com",
        contrasena_hash="not-a-login-account",  # placeholder: nobody logs in as this user
        correo_verificado=True,
        id_rol=role.id_rol,
    )
    db.add(user)
    db.commit()
    return user.id_usuario


def reference_metrics(history: pd.DataFrame, target: str) -> dict[str, dict[str, float | None] | None]:
    """One-month-ahead metrics of each reference forecast on the model's origins."""
    initial = max(MIN_MONTHS, len(history) - RUNTIME_ORIGINS)
    result: dict[str, dict[str, float | None] | None] = {}
    for name, baseline in BASELINES.items():
        records = rolling_origin(history, target, baseline_model(baseline), initial=initial, horizons=[1])
        if not records or any(record.prediccion is None for record in records):
            result[name] = None
            continue
        actual = np.array([record.real for record in records])
        predicted = np.array([record.prediccion for record in records], dtype=float)
        training = history[target].to_numpy(dtype=float)[: min(record.origen for record in records)]
        scores = point_metrics(actual, predicted, training)
        result[name] = {key: scores[key] for key in ("mae", "rmse", "wape", "mape")}
    return result


def run(sales: pd.DataFrame, seed: int | None = None, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load ``sales`` through the ETL, fit the model, and return the experiment record."""
    buffer = io.BytesIO()
    sales.to_excel(buffer, index=False, sheet_name="ventas")
    contents, file_hash = etl_service.read_limited(io.BytesIO(buffer.getvalue()))

    db = _session()
    try:
        user_id = _experiment_user(db)
        load = etl_service.load_sales(db, user_id, "xlsx", contents, file_hash, MAPPING)
        _, _, forecast = analytics_service.monthly_projection(db, user_id)
    finally:
        db.close()

    payload = forecast_payload(None, None, forecast)
    targets: dict[str, Any] = {}
    for target in TARGETS:
        metrics = payload["metricas"][target]
        references = reference_metrics(forecast.historial, target)
        available = {name: values["wape"] for name, values in references.items() if values and values["wape"] is not None}
        best = min(available, key=available.get) if available else None
        targets[target] = {
            "metricas": metrics,
            "referencias": references,
            "mejor_referencia": best,
            "gana_a_la_mejor_referencia": None
            if best is None or metrics["wape"] is None
            else bool(metrics["wape"] < available[best]),
            "escala_lewis": lewis_grade(metrics["mape"]),
            "coeficientes": payload["coeficientes"][target],
        }

    main = targets[MAIN_TARGET]
    return {
        "dataset": {
            "generador": GENERATOR.relative_to(ROOT).as_posix(),
            "semilla": seed,
            **(parameters or {}),
            "filas": len(sales),
            "categorias": sorted(sales["categoria"].dropna().unique().tolist()),
            "monto_total": round(float(sales["monto"].sum()), 2),
        },
        "etl": {key: load[key] for key in ("registros_leidos", "registros_cargados", "filas_rechazadas")},
        "modelo": {
            "algoritmo": "Regresión lineal múltiple por OLS (statsmodels.OLS)",
            "especificacion": payload["modelo"],
            "meses_observados": payload["meses_observados"],
            "horizonte": payload["horizonte_aplicado"],
            "primer_mes_proyectado": payload["proyeccion"][0]["periodo"] if payload["proyeccion"] else None,
            "validacion": "Origen móvil: reajuste en cada uno de los últimos 6 meses y predicción del mes siguiente",
        },
        "objetivos": targets,
        "hipotesis": {
            "criterio": "WAPE del monto a un mes menor que el de la mejor de las tres referencias",
            "objetivo": MAIN_TARGET,
            "wape_modelo": main["metricas"]["wape"],
            "mejor_referencia": main["mejor_referencia"],
            "wape_referencia": None
            if main["mejor_referencia"] is None
            else main["referencias"][main["mejor_referencia"]]["wape"],
            "mejora_pct": main["metricas"]["mejora_vs_referencia"],
            "se_cumple": main["gana_a_la_mejor_referencia"],
            "escala_lewis": main["escala_lewis"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the thesis experiment and record its metrics.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--fecha", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    # Windows consoles default to cp1252; print the Spanish messages as UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    generator = load_generator()
    print(f"1/3 Generando el dataset (semilla {generator.SEED})...")
    sales = generator.build_sales(generator.SEED)
    print(f"2/3 Cargando {len(sales):,} ventas por el ETL y ajustando el modelo...")
    record = run(
        sales,
        seed=generator.SEED,
        parameters={"inicio": generator.START.isoformat(), "fin": generator.END.isoformat()},
    )
    record = {"fecha": args.fecha.isoformat(), **git_commit(), **record}
    record["dataset"]["sha256_filas"] = hashlib.sha256(
        sales.to_csv(index=False).encode("utf-8")
    ).hexdigest()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / f"metricas_{args.fecha.isoformat()}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    hypothesis = record["hipotesis"]
    print(f"3/3 Métricas -> {path}")
    print(
        f"WAPE modelo {hypothesis['wape_modelo']:.2f} % vs {hypothesis['mejor_referencia']} "
        f"{hypothesis['wape_referencia']:.2f} %: hipótesis {'se cumple' if hypothesis['se_cumple'] else 'no se cumple'}; "
        f"precisión {hypothesis['escala_lewis']} (Lewis)."
    )


if __name__ == "__main__":
    main()
