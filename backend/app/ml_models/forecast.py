"""Linear forecasting of monthly and daily sales with real prediction intervals.

Every model is ordinary least squares (``statsmodels.OLS``) with an intercept.
Intervals are 95 % observation intervals from ``get_prediction``, so they widen
with the distance from the data instead of using one fixed margin. Amounts and
units are fitted separately on the same predictors.

Monthly model, chosen per series from its complete observed months:

- fewer than 6: no projection (``InsufficientHistoryError``);
- 6 to 23: trend only, horizon of half the months (3 to 11);
- 24 or more, with every calendar month observed: trend plus 11 month dummies
  (January is the reference), horizon of 12.

Months without sales are absent from the data, never filled with zero.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Literal, Protocol

import numpy as np
import pandas as pd
import statsmodels.api as sm

METRIC_NAMES = ("r2", "mape", "rmse")
TARGETS = ("monto", "cantidad")
MIN_MONTHS = 6
SEASONAL_MONTHS = 24
MAX_HORIZON = 12
# Points past this many months ahead are extrapolation and are flagged as such.
RELIABLE_MONTHS = 6
# The weekday model needs two observations of each weekday.
WEEKDAY_MIN_DAYS = 14
ALPHA = 0.05
MONTH_NAMES = (
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
)

MonthlyModel = Literal["tendencia", "tendencia_estacional"]
Metrics = dict[str, float | None]


class SaleRecord(Protocol):
    """A sale, or a day of summed sales, as the aggregations read it."""

    @property
    def fecha_venta(self) -> date: ...

    @property
    def monto(self) -> Decimal | float: ...

    @property
    def cantidad(self) -> Decimal | float | None: ...


class InsufficientHistoryError(ValueError):
    """Too few complete months to project; the message is safe to show."""


@dataclass(frozen=True)
class ForecastResult:
    """Next-day forecast, non-negative interval, and holdout metrics."""

    prediction: float
    raw_prediction: float
    lower: float
    upper: float
    metrics: Metrics


@dataclass(frozen=True)
class ForecastPoint:
    """One projected month; values are clipped at zero."""

    fecha: pd.Timestamp
    prediccion: float
    inferior: float
    superior: float
    extrapolacion: bool


@dataclass(frozen=True)
class TargetForecast:
    puntos: list[ForecastPoint]
    metricas: Metrics


@dataclass(frozen=True)
class MonthlyForecast:
    """The model applied to one monthly series and its projection."""

    modelo: MonthlyModel
    horizonte: int
    meses_observados: int
    advertencia: str | None
    #: Complete months the model was fitted on.
    historial: pd.DataFrame
    #: The last month when its sales are still incomplete; it is projected, not fitted.
    mes_parcial: pd.Series | None
    objetivos: dict[str, TargetForecast]


# ---------------------------------------------------------------- aggregation


def monthly_aggregates(ventas: Sequence[SaleRecord]) -> pd.DataFrame:
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


# ---------------------------------------------------------------- features


def months_elapsed(dates: pd.Series) -> np.ndarray:
    """Calendar months since the first date: January to March is 2, gaps included."""
    first = dates.iloc[0]
    return ((dates.dt.year - first.year) * 12 + (dates.dt.month - first.month)).to_numpy()


def build_seasonal_features(months_index: np.ndarray, calendar_months: pd.Series) -> pd.DataFrame:
    """Trend plus February-to-December dummies; January is the reference level."""
    months = np.asarray(calendar_months)
    features = pd.DataFrame({"mes_indice": np.asarray(months_index, dtype=float)})
    for month in range(2, 13):
        features[f"mes_{month}"] = (months == month).astype(int)
    return features


def build_weekly_features(days_index: np.ndarray, weekdays: pd.Series) -> pd.DataFrame:
    """Trend plus Tuesday-to-Sunday dummies; Monday (weekday 0) is the reference."""
    days = np.asarray(weekdays)
    features = pd.DataFrame({"dia_indice": np.asarray(days_index, dtype=float)})
    for weekday in range(1, 7):
        features[f"dia_{weekday + 1}"] = (days == weekday).astype(int)
    return features


# ---------------------------------------------------------------- fitting


def _with_constant(features: pd.DataFrame) -> pd.DataFrame:
    return sm.add_constant(features, has_constant="add")


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> Metrics:
    """Calculate metrics on a temporal holdout, never on training rows."""
    if len(actual) == 0:
        return {name: None for name in METRIC_NAMES}
    errors = actual - predicted
    nonzero = actual != 0
    spread = np.sum((actual - actual.mean()) ** 2)
    return {
        "r2": float(1 - np.sum(errors**2) / spread) if len(actual) > 1 and spread > 0 else None,
        "mape": float(np.mean(np.abs(errors[nonzero] / actual[nonzero])) * 100)
        if np.any(nonzero)
        else None,
        "rmse": float(np.sqrt(np.mean(errors**2))),
    }


def _holdout_metrics(features: pd.DataFrame, y: np.ndarray) -> Metrics:
    """Score the last 20 % of observations with a model fitted only on earlier ones."""
    holdout = max(1, min(len(y) - 1, int(np.ceil(len(y) * 0.2))))
    split = len(y) - holdout
    model = sm.OLS(y[:split], _with_constant(features.iloc[:split])).fit()
    return _metrics(y[split:], np.asarray(model.predict(_with_constant(features.iloc[split:]))))


def _fit_and_project(
    features: pd.DataFrame, y: np.ndarray, future: pd.DataFrame
) -> tuple[pd.DataFrame, Metrics]:
    """Fit on every row and return the mean with its 95 % observation interval."""
    model = sm.OLS(y, _with_constant(features)).fit()
    frame = model.get_prediction(_with_constant(future)).summary_frame(alpha=ALPHA)
    projection = frame[["mean", "obs_ci_lower", "obs_ci_upper"]].reset_index(drop=True)
    return projection, _holdout_metrics(features, y)


# ---------------------------------------------------------------- monthly


def _missing_calendar_months(history: pd.DataFrame) -> list[str]:
    seen = set(history["fecha"].dt.month)
    return [MONTH_NAMES[month - 1] for month in range(1, 13) if month not in seen]


def _split_partial_month(
    monthly: pd.DataFrame, last_sale: date
) -> tuple[pd.DataFrame, pd.Series | None]:
    """Separate the last month when sales stop before its final day."""
    ordered = monthly.sort_values("fecha").reset_index(drop=True)
    if ordered.empty:
        return ordered, None
    last = ordered.iloc[-1]
    if pd.Timestamp(last_sale) < last["fecha"].normalize():
        return ordered.iloc[:-1].reset_index(drop=True), last
    return ordered, None


def monthly_forecast_series(
    monthly: pd.DataFrame, last_sale: date, max_horizon: int = MAX_HORIZON
) -> MonthlyForecast:
    """Project a monthly series with the model its history supports.

    ``monthly`` holds one row per observed month (month-end ``fecha``, ``monto``,
    ``cantidad``), as ``monthly_aggregates`` returns it. ``last_sale`` is the date
    of the latest sale, which tells whether the last month is complete.
    """
    history, partial = _split_partial_month(monthly, last_sale)
    observed = len(history)
    if observed < MIN_MONTHS:
        raise InsufficientHistoryError(
            f"Se necesitan al menos {MIN_MONTHS} meses completos de ventas para proyectar; "
            f"hay {observed} y faltan {MIN_MONTHS - observed}."
        )

    missing = _missing_calendar_months(history)
    seasonal = observed >= SEASONAL_MONTHS and not missing
    horizon = min(max_horizon, MAX_HORIZON if observed >= SEASONAL_MONTHS else observed // 2)

    warnings: list[str] = []
    if observed < SEASONAL_MONTHS:
        warnings.append(
            f"Con {observed} meses completos la proyección es una tendencia: no anticipa "
            f"temporadas. Se proyectan {horizon} meses."
        )
    elif missing:
        warnings.append(
            f"No hay ventas en {', '.join(missing)}, así que la proyección usa solo la "
            "tendencia, sin temporadas."
        )
    if horizon > RELIABLE_MONTHS:
        warnings.append(
            f"Los meses {RELIABLE_MONTHS + 1} a {horizon} son extrapolación: su incertidumbre es mayor."
        )

    first_future = partial["fecha"] if partial is not None else history["fecha"].iloc[-1] + pd.offsets.MonthEnd(1)
    future_dates = [first_future + pd.offsets.MonthEnd(step) for step in range(horizon)]
    all_dates = pd.Series(list(history["fecha"]) + future_dates)
    index = months_elapsed(all_dates)
    calendar = all_dates.dt.month
    if seasonal:
        features = build_seasonal_features(index, calendar)
    else:
        features = pd.DataFrame({"mes_indice": index.astype(float)})
    fitted, future = features.iloc[:observed], features.iloc[observed:].reset_index(drop=True)

    objetivos: dict[str, TargetForecast] = {}
    for target in TARGETS:
        projection, metrics = _fit_and_project(fitted, history[target].to_numpy(dtype=float), future)
        points = []
        for step, (moment, row) in enumerate(zip(future_dates, projection.itertuples(), strict=True), start=1):
            points.append(
                ForecastPoint(
                    fecha=moment,
                    prediccion=max(0.0, float(row.mean)),
                    inferior=max(0.0, float(row.obs_ci_lower)),
                    superior=max(0.0, float(row.obs_ci_upper)),
                    extrapolacion=step > RELIABLE_MONTHS,
                )
            )
        objetivos[target] = TargetForecast(puntos=points, metricas=metrics)

    return MonthlyForecast(
        modelo="tendencia_estacional" if seasonal else "tendencia",
        horizonte=horizon,
        meses_observados=observed,
        advertencia=" ".join(warnings) or None,
        historial=history,
        mes_parcial=partial,
        objetivos=objetivos,
    )


def forecast_from_sales(
    ventas: Sequence[SaleRecord], max_horizon: int = MAX_HORIZON
) -> MonthlyForecast:
    """Aggregate sales (or daily totals) by month and project them."""
    if not ventas:
        raise InsufficientHistoryError(
            f"Se necesitan al menos {MIN_MONTHS} meses completos de ventas para proyectar; "
            f"hay 0 y faltan {MIN_MONTHS}."
        )
    last_sale = max(venta.fecha_venta for venta in ventas)
    return monthly_forecast_series(monthly_aggregates(ventas), last_sale, max_horizon)


# ---------------------------------------------------------------- daily


def _daily_features(indices: np.ndarray, weekdays: pd.Series, use_weekdays: bool, use_trend: bool) -> pd.DataFrame:
    if use_weekdays:
        return build_weekly_features(indices, weekdays)
    if use_trend:
        return pd.DataFrame({"dia_indice": indices.astype(float)})
    # An intercept-only model: the forecast is the mean of the observed days.
    return pd.DataFrame(index=range(len(indices)))


def daily_predictions(
    dates: Sequence[date | str],
    amounts: Sequence[float],
    quantities: Sequence[float],
) -> tuple[date, dict[str, ForecastResult]]:
    """Forecast the day after the last observation for amount and units.

    The predictors grow with the history so the interval always has degrees of
    freedom left: the mean for 2 days, a trend from 3 days, and trend plus
    weekday dummies once there are 14 days covering every weekday.
    """
    if len(dates) < 2 or len(dates) != len(amounts) or len(dates) != len(quantities):
        raise ValueError("Se necesitan al menos 2 dias de datos para predecir.")
    parsed = [date.fromisoformat(value) if isinstance(value, str) else value for value in dates]
    first = parsed[0]
    next_date = parsed[-1] + timedelta(days=1)
    indices = np.array([(day - first).days for day in parsed + [next_date]])
    weekdays = pd.Series([day.weekday() for day in parsed + [next_date]])
    use_weekdays = len(parsed) >= WEEKDAY_MIN_DAYS and weekdays.iloc[:-1].nunique() == 7
    features = _daily_features(indices, weekdays, use_weekdays, use_trend=len(parsed) >= 3)
    fitted, future = features.iloc[:-1], features.iloc[-1:].reset_index(drop=True)

    results: dict[str, ForecastResult] = {}
    for target, values in (("monto", amounts), ("cantidad", quantities)):
        projection, metrics = _fit_and_project(fitted, np.asarray(values, dtype=float), future)
        row: Any = projection.iloc[0]
        raw = float(row["mean"])
        results[target] = ForecastResult(
            prediction=max(0.0, raw),
            raw_prediction=raw,
            lower=max(0.0, float(row["obs_ci_lower"])),
            upper=max(0.0, float(row["obs_ci_upper"])),
            metrics=metrics,
        )
    return next_date, results
