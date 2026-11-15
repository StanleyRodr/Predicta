"""The single-command experiment loads through the ETL and records its result."""

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_experiment.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("run_experiment", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sales(months: int = 14) -> pd.DataFrame:
    """Three sales per month with an upward trend and noise, one on the last day."""
    rng = np.random.default_rng(3)
    rows = []
    for moment in pd.date_range("2025-01-31", periods=months, freq="ME"):
        for day, category in ((3, "Abarrotes"), (15, "Bebidas"), (moment.day, "Lácteos")):
            rows.append(
                {
                    "producto": f"Producto {category}",
                    "monto": round(1000 + 40 * moment.month + rng.normal(0, 60), 2),
                    "cantidad": 2,
                    "categoria": category,
                    "fecha": f"{moment:%Y-%m}-{day:02d} 10:00:00",
                }
            )
    return pd.DataFrame(rows)


def test_experiment_loads_every_row_and_scores_the_model_against_the_references():
    module = _load_script()

    record = module.run(_sales(), seed=1, parameters={"inicio": "2025-01-01"})

    assert record["etl"] == {"registros_leidos": 42, "registros_cargados": 42, "filas_rechazadas": 0}
    assert record["dataset"]["semilla"] == 1
    assert record["dataset"]["categorias"] == ["Abarrotes", "Bebidas", "Lácteos"]
    amount = record["objetivos"]["monto"]
    assert amount["metricas"]["origenes"] == 6
    assert set(amount["referencias"]) == {"ultimo_valor", "mismo_mes_anio_anterior", "promedio_movil_3"}
    assert set(amount["coeficientes"]) == {"const", "mes_indice"}
    hypothesis = record["hipotesis"]
    assert hypothesis["objetivo"] == "monto"
    if hypothesis["mejor_referencia"] is not None:
        expected = hypothesis["wape_modelo"] < hypothesis["wape_referencia"]
        assert hypothesis["se_cumple"] is expected


def test_experiment_is_reproducible():
    module = _load_script()

    assert module.run(_sales()) == module.run(_sales())


def test_lewis_scale_bands():
    module = _load_script()

    assert [module.lewis_grade(value) for value in (9.29, 10.0, 25.0, 50.0, None)] == [
        "muy precisa",
        "buena",
        "razonable",
        "imprecisa",
        None,
    ]
