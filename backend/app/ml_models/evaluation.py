"""Out-of-sample evaluation: baselines, error metrics, and rolling-origin backtests.

Nothing here imports the forecasting module. Models are passed in as functions
``(train, target, future_dates) -> DataFrame | None`` returning ``mean``,
``lower``, and ``upper`` per future date, or ``None`` when the model cannot be
fitted on that training window. Every error is measured on months the model
did not see.
"""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

ModelFn = Callable[[pd.DataFrame, str, Sequence[pd.Timestamp]], pd.DataFrame | None]
BaselineFn = Callable[[pd.DataFrame, str, pd.Timestamp], float | None]

MOVING_AVERAGE_MONTHS = 3
#: The runtime evaluation predicts each of the last months one step ahead.
RUNTIME_ORIGINS = 6
METRIC_NAMES = ("r2", "mape", "rmse", "wape", "mase")


# ---------------------------------------------------------------- baselines


def naive_last(history: pd.DataFrame, target: str, _moment: pd.Timestamp) -> float | None:
    """The last observed month, repeated."""
    return float(history[target].iloc[-1]) if len(history) else None


def seasonal_naive(history: pd.DataFrame, target: str, moment: pd.Timestamp) -> float | None:
    """The same calendar month one year earlier, when it was observed."""
    year_before = (moment - pd.offsets.MonthEnd(12)).normalize()
    match = history.loc[history["fecha"].dt.normalize() == year_before, target]
    return float(match.iloc[0]) if len(match) else None


def moving_average(history: pd.DataFrame, target: str, _moment: pd.Timestamp) -> float | None:
    """The mean of the last three observed months."""
    if len(history) == 0:
        return None
    return float(history[target].iloc[-MOVING_AVERAGE_MONTHS:].mean())


BASELINES: dict[str, BaselineFn] = {
    "ultimo_valor": naive_last,
    "mismo_mes_anio_anterior": seasonal_naive,
    "promedio_movil_3": moving_average,
}


def baseline_model(baseline: BaselineFn) -> ModelFn:
    """Wrap a baseline as a model; it has no interval."""

    def model(train: pd.DataFrame, target: str, future_dates: Sequence[pd.Timestamp]) -> pd.DataFrame | None:
        values = [baseline(train, target, moment) for moment in future_dates]
        return pd.DataFrame({"mean": values, "lower": [None] * len(values), "upper": [None] * len(values)})

    return model


# ---------------------------------------------------------------- metrics


def wape(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    """Weighted absolute percentage error: total absolute error over total actuals."""
    total = float(np.sum(np.abs(actual)))
    if len(actual) == 0 or total == 0:
        return None
    return float(np.sum(np.abs(actual - predicted)) / total * 100)


def mase(actual: np.ndarray, predicted: np.ndarray, training: np.ndarray) -> float | None:
    """Mean absolute error scaled by the in-sample error of the one-month naive model."""
    if len(actual) == 0 or len(training) < 2:
        return None
    scale = float(np.mean(np.abs(np.diff(training))))
    if scale == 0:
        return None
    return float(np.mean(np.abs(actual - predicted)) / scale)


def point_metrics(actual: np.ndarray, predicted: np.ndarray, training: np.ndarray) -> dict[str, float | None]:
    """R², MAPE, RMSE, WAPE, and MASE of predictions against unseen actuals."""
    if len(actual) == 0:
        return {name: None for name in METRIC_NAMES}
    errors = actual - predicted
    nonzero = actual != 0
    spread = float(np.sum((actual - actual.mean()) ** 2))
    return {
        "r2": float(1 - np.sum(errors**2) / spread) if len(actual) > 1 and spread > 0 else None,
        "mape": float(np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100) if np.any(nonzero) else None,
        "rmse": float(np.sqrt(np.mean(errors**2))),
        "wape": wape(actual, predicted),
        "mase": mase(actual, predicted, training),
    }


def improvement(model_error: float | None, baseline_error: float | None) -> float | None:
    """Percent reduction of the error against a baseline; negative when the model is worse."""
    if model_error is None or baseline_error is None or baseline_error == 0:
        return None
    return float((baseline_error - model_error) / baseline_error * 100)


# ---------------------------------------------------------------- backtest


@dataclass(frozen=True)
class BacktestRecord:
    """One prediction made at ``origen`` (training months) for ``horizonte`` months ahead."""

    origen: int
    horizonte: int
    fecha: pd.Timestamp
    real: float
    prediccion: float | None
    inferior: float | None
    superior: float | None


def _optional(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return float(value)


def rolling_origin(
    history: pd.DataFrame,
    target: str,
    model: ModelFn,
    *,
    initial: int,
    horizons: Iterable[int],
) -> list[BacktestRecord]:
    """Refit at every origin from ``initial`` months and predict the following months.

    The model only ever receives the months before the origin. Horizon ``h`` is
    the h-th observed month after it, so a gap in the data is never filled.
    """
    ordered = history.sort_values("fecha").reset_index(drop=True)
    steps = sorted(set(horizons))
    records: list[BacktestRecord] = []
    for origin in range(initial, len(ordered)):
        future = ordered.iloc[origin : origin + max(steps)]
        if future.empty:
            continue
        projection = model(ordered.iloc[:origin], target, list(future["fecha"]))
        if projection is None:
            continue
        for step in steps:
            if step > len(future):
                break
            row = projection.iloc[step - 1]
            records.append(
                BacktestRecord(
                    origen=origin,
                    horizonte=step,
                    fecha=future["fecha"].iloc[step - 1],
                    real=float(future[target].iloc[step - 1]),
                    prediccion=_optional(row["mean"]),
                    inferior=_optional(row["lower"]),
                    superior=_optional(row["upper"]),
                )
            )
    return records


def one_step_metrics(
    history: pd.DataFrame, target: str, model: ModelFn, *, min_train: int
) -> dict[str, Any]:
    """Metrics shown at runtime: one-month-ahead errors over the last months.

    The model and every baseline are scored on the same origins. The best
    baseline is the one with the lowest WAPE among those that predicted every
    origin; ``mejora_vs_referencia`` compares the model's WAPE against it.
    Values that cannot be computed stay ``None``, never zero.
    """
    initial = max(min_train, len(history) - RUNTIME_ORIGINS)
    records = rolling_origin(history, target, model, initial=initial, horizons=[1])
    empty: dict[str, Any] = {name: None for name in METRIC_NAMES}
    empty.update({"mejora_vs_referencia": None, "referencia": None, "origenes": 0})
    if not records:
        return empty

    origins = [record.origen for record in records]
    actual = np.array([record.real for record in records])
    predicted = np.array([record.prediccion for record in records], dtype=float)
    training = history[target].to_numpy(dtype=float)[: min(origins)]
    result: dict[str, Any] = point_metrics(actual, predicted, training)

    best: tuple[str, float] | None = None
    for name, baseline in BASELINES.items():
        values = []
        for record in records:
            value = baseline(history.iloc[: record.origen], target, record.fecha)
            if value is None:
                break
            values.append(value)
        else:
            error = wape(actual, np.array(values))
            if error is not None and (best is None or error < best[1]):
                best = (name, error)

    result["referencia"] = best[0] if best else None
    result["mejora_vs_referencia"] = improvement(result["wape"], best[1] if best else None)
    result["origenes"] = len(records)
    return result


def interval_coverage(records: Sequence[BacktestRecord]) -> float | None:
    """Share of actuals inside the predicted interval, in percent."""
    bounds = [(r.inferior, r.real, r.superior) for r in records if r.inferior is not None and r.superior is not None]
    if not bounds:
        return None
    inside = sum(1 for lower, real, upper in bounds if lower is not None and upper is not None and lower <= real <= upper)
    return inside / len(bounds) * 100
