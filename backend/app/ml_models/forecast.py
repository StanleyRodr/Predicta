"""Reusable multiple-linear-regression functions for sales analytics."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.models import models


METRIC_NAMES = ("r2", "mape", "rmse")


@dataclass(frozen=True)
class ForecastResult:
    """Forecast, non-negative interval, and out-of-sample quality metrics."""

    prediction: float
    raw_prediction: float
    lower: float
    upper: float
    metrics: dict[str, float | None]


def _empty_metrics() -> dict[str, float | None]:
    return {name: None for name in METRIC_NAMES}


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float | None]:
    """Calculate metrics on a temporal holdout, never on training rows."""
    if len(actual) == 0:
        return _empty_metrics()
    errors = actual - predicted
    nonzero = actual != 0
    mape = (
        float(np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100)
        if np.any(nonzero)
        else None
    )
    return {
        "r2": float(1 - np.sum(errors**2) / np.sum((actual - actual.mean()) ** 2))
        if len(actual) > 1 and np.sum((actual - actual.mean()) ** 2) > 0
        else None,
        "mape": mape,
        "rmse": float(np.sqrt(np.mean(errors**2))),
    }


def _fit_and_evaluate(
    features: pd.DataFrame, target: Sequence[float], horizon_features: pd.DataFrame
) -> tuple[np.ndarray, dict[str, float | None], float]:
    """Fit on history, evaluate a chronological holdout, and forecast future rows."""
    y = np.asarray(target, dtype=float)
    if len(y) < 2:
        raise ValueError("Se necesitan al menos 2 observaciones para predecir.")

    # Reserve the last observations for evaluation. The model used for the
    # forecast is refit with all historical rows only after this evaluation.
    holdout_size = max(1, min(len(y) - 1, int(np.ceil(len(y) * 0.2))))
    split = len(y) - holdout_size
    validation_model = LinearRegression().fit(features.iloc[:split], y[:split])
    validation_prediction = validation_model.predict(features.iloc[split:])
    metrics = _metrics(y[split:], validation_prediction)

    model = LinearRegression().fit(features, y)
    residuals = y - model.predict(features)
    spread = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0
    if spread == 0:
        spread = float(np.std(y, ddof=1)) if len(y) > 1 else 0.0
    predictions = model.predict(horizon_features)
    return predictions, metrics, 1.96 * spread


def build_seasonal_features(
    months_index: np.ndarray, calendar_months: pd.Series
) -> pd.DataFrame:
    """Build trend plus one-hot calendar-month features."""
    features = pd.DataFrame({"mes_indice": months_index})
    for month in range(1, 13):
        features[f"mes_{month}"] = (calendar_months == month).astype(int)
    return features


def build_weekly_features(
    days_index: np.ndarray, weekdays: pd.Series
) -> pd.DataFrame:
    """Build trend plus seven stable Monday-to-Sunday dummy features."""
    features = pd.DataFrame({"dia_indice": days_index})
    for weekday in range(7):
        features[f"dia_{weekday + 1}"] = (weekdays == weekday).astype(int)
    return features


def monthly_aggregates(ventas: Sequence[models.Venta]) -> pd.DataFrame:
    """Aggregate sales by observed month without fabricating empty months."""
    if not ventas:
        return pd.DataFrame(columns=["fecha", "monto", "cantidad"])

    df = pd.DataFrame(
        [
            {
                "fecha": venta.fecha_venta,
                "monto": float(venta.monto),
                "cantidad": float(venta.cantidad if venta.cantidad is not None else 1),
            }
            for venta in ventas
        ]
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    monthly = (
        df.assign(periodo=df["fecha"].dt.to_period("M"))
        .groupby("periodo", as_index=False)[["monto", "cantidad"]]
        .sum()
    )
    monthly["fecha"] = monthly["periodo"].dt.to_timestamp("M")
    return monthly[["fecha", "monto", "cantidad"]]


def daily_aggregates(ventas: Sequence[models.Venta]) -> pd.DataFrame:
    """Aggregate sales by observed day without fabricating missing dates."""
    if not ventas:
        return pd.DataFrame(columns=["fecha", "monto", "cantidad"])
    df = pd.DataFrame(
        [
            {
                "fecha": venta.fecha_venta,
                "monto": float(venta.monto),
                "cantidad": float(venta.cantidad if venta.cantidad is not None else 1),
            }
            for venta in ventas
        ]
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    return df.groupby("fecha", as_index=False)[["monto", "cantidad"]].sum()


def _forecast_target(
    features: pd.DataFrame,
    target: Sequence[float],
    future_features: pd.DataFrame,
) -> ForecastResult:
    predictions, metrics, margin = _fit_and_evaluate(features, target, future_features)
    raw_prediction = float(predictions[0])
    point = max(0.0, raw_prediction)
    return ForecastResult(
        prediction=point,
        raw_prediction=raw_prediction,
        lower=max(0.0, point - margin),
        upper=max(0.0, point + margin),
        metrics=metrics,
    )


def monthly_predictions(
    ventas: Sequence[models.Venta], horizon: int = 1
) -> tuple[pd.DataFrame, list[pd.Timestamp], dict[str, ForecastResult]]:
    """Forecast monthly revenue and units with identical seasonal predictors."""
    monthly = monthly_aggregates(ventas)
    if len(monthly) < 2:
        raise ValueError("Se necesitan al menos 2 meses de datos para predecir.")
    features = build_seasonal_features(
        np.arange(len(monthly)), monthly["fecha"].dt.month
    )
    last_date = monthly["fecha"].max()
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, horizon + 1)]
    future_features = build_seasonal_features(
        np.arange(len(monthly), len(monthly) + horizon),
        pd.Series([current_date.month for current_date in future_dates]),
    )
    return (
        monthly,
        future_dates,
        {
            "monto": _forecast_target(features, monthly["monto"], future_features),
            "cantidad": _forecast_target(
                features, monthly["cantidad"], future_features
            ),
        },
    )


def monthly_forecast(
    ventas: Sequence[models.Venta], horizon: int = 12
) -> tuple[pd.DataFrame, list[pd.Timestamp], np.ndarray]:
    """Return observed monthly data, future dates, and non-negative forecasts."""
    monthly, future_dates, forecasts = monthly_predictions(ventas, horizon)
    # This compatibility wrapper is used by chart reports that only plot revenue.
    predictions = np.array([forecasts["monto"].prediction])
    if horizon > 1:
        features = build_seasonal_features(
            np.arange(len(monthly), len(monthly) + horizon),
            pd.Series([current_date.month for current_date in future_dates]),
        )
        X_train = build_seasonal_features(
            np.arange(len(monthly)), monthly["fecha"].dt.month
        )
        model = LinearRegression().fit(X_train, monthly["monto"])
        predictions = np.clip(model.predict(features), 0.0, None)
    return monthly, future_dates, predictions


def predict_next_day(
    dates: Sequence[date | str], amounts: Sequence[float]
) -> tuple[date, float, float]:
    """Predict next-day revenue from daily observations."""
    if len(dates) < 2 or len(dates) != len(amounts):
        raise ValueError("Se necesitan al menos 2 dias de datos para predecir.")

    parsed_dates = [
        date.fromisoformat(value) if isinstance(value, str) else value for value in dates
    ]
    first_date = parsed_dates[0]
    X = np.array([[(current_date - first_date).days] for current_date in parsed_dates])
    next_date = parsed_dates[-1] + timedelta(days=1)
    y = np.array([float(amount) for amount in amounts])
    model = LinearRegression().fit(X, y)
    raw_prediction = float(model.predict([[(next_date - first_date).days]])[0])
    return next_date, max(0.0, raw_prediction), raw_prediction


def daily_predictions(
    dates: Sequence[date | str],
    amounts: Sequence[float],
    quantities: Sequence[float],
) -> tuple[date, dict[str, ForecastResult]]:
    """Forecast next-day amount and units using trend plus weekday dummies."""
    if len(dates) < 2 or len(dates) != len(amounts) or len(dates) != len(quantities):
        raise ValueError("Se necesitan al menos 2 dias de datos para predecir.")
    parsed_dates = [
        date.fromisoformat(value) if isinstance(value, str) else value for value in dates
    ]
    first_date = parsed_dates[0]
    indices = np.array([[(current_date - first_date).days] for current_date in parsed_dates])
    weekdays = pd.Series([current_date.weekday() for current_date in parsed_dates])
    features = build_weekly_features(indices.ravel(), weekdays)
    next_date = parsed_dates[-1] + timedelta(days=1)
    future_features = build_weekly_features(
        np.array([(next_date - first_date).days]), pd.Series([next_date.weekday()])
    )
    return next_date, {
        "monto": _forecast_target(features, amounts, future_features),
        "cantidad": _forecast_target(features, quantities, future_features),
    }
