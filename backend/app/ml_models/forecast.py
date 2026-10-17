"""Reusable forecasting functions for sales analytics."""

from collections.abc import Sequence
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from app.models import models


def build_seasonal_features(
    months_index: np.ndarray, calendar_months: pd.Series
) -> pd.DataFrame:
    """Build trend plus one-hot calendar-month features."""
    features = pd.DataFrame({"mes_indice": months_index})
    for month in range(1, 13):
        features[f"mes_{month}"] = (calendar_months == month).astype(int)
    return features


def monthly_aggregates(ventas: Sequence[models.Venta]) -> pd.DataFrame:
    """Aggregate sales by observed month without fabricating empty months."""
    if not ventas:
        return pd.DataFrame(columns=["fecha", "monto"])

    df = pd.DataFrame(
        [{"fecha": venta.fecha_venta, "monto": float(venta.monto)} for venta in ventas]
    )
    df["fecha"] = pd.to_datetime(df["fecha"])
    monthly = (
        df.assign(periodo=df["fecha"].dt.to_period("M"))
        .groupby("periodo", as_index=False)["monto"]
        .sum()
    )
    monthly["fecha"] = monthly["periodo"].dt.to_timestamp("M")
    return monthly[["fecha", "monto"]]


def monthly_forecast(
    ventas: Sequence[models.Venta], horizon: int = 12
) -> tuple[pd.DataFrame, list[pd.Timestamp], np.ndarray]:
    """Return observed monthly data, future dates, and non-negative forecasts."""
    monthly = monthly_aggregates(ventas)
    if len(monthly) < 2:
        raise ValueError("Se necesitan al menos 2 meses de datos para predecir.")

    X_train = build_seasonal_features(
        np.arange(len(monthly)), monthly["fecha"].dt.month
    )
    model = LinearRegression().fit(X_train, monthly["monto"])
    last_date = monthly["fecha"].max()
    future_dates = [last_date + pd.DateOffset(months=i) for i in range(1, horizon + 1)]
    X_future = build_seasonal_features(
        np.arange(len(monthly), len(monthly) + horizon),
        pd.Series([current_date.month for current_date in future_dates]),
    )
    predictions = np.clip(model.predict(X_future), 0.0, None)
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
    y = np.array([float(amount) for amount in amounts])
    model = LinearRegression().fit(X, y)

    next_date = parsed_dates[-1] + timedelta(days=1)
    raw_prediction = float(model.predict([[(next_date - first_date).days]])[0])
    return next_date, max(0.0, raw_prediction), raw_prediction
