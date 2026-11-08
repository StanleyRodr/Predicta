"""Linear forecasting of monthly and daily sales with real prediction intervals.

Every model is ordinary least squares (``statsmodels.OLS``) with an intercept.
Intervals are 95 % observation intervals from ``get_prediction``, so they widen
with the distance from the data instead of using one fixed margin. Amounts and
units are fitted separately on the same predictors.

Monthly model, chosen per series from its complete observed months:

- fewer than 6: no projection (``InsufficientHistoryError``);
- 6 to 23: trend only, horizon of half the months (3 to 11);
- 24 to 35: trend only, horizon of 12;
- 36 or more, with every calendar month observed: trend plus 11 month dummies
  (January is the reference), horizon of 12.

Seasonality starts at 36 months, three observations per calendar month. With
24 the seasonal specification lost to the same-month-last-year baseline in
4 of 6 backtest horizons (``docs/evaluacion/resultados.md``).

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

from app.ml_models.evaluation import ModelFn, one_step_metrics, point_metrics

DAILY_METRIC_NAMES = ("r2", "mape", "rmse")
TARGETS = ("monto", "cantidad")
MIN_MONTHS = 6
#: History length from which the full 12-month horizon is projected.
FULL_HORIZON_MONTHS = 24
SEASONAL_MONTHS = 36
MAX_HORIZON = 12
# Fewest training months that leave one degree of freedom per specification.
TREND_MIN_FIT = 3
SEASONAL_MIN_FIT = 14
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
Metrics = dict[str, Any]


class SaleRecord(Protocol):
    """A sale, or a day of summed sales, as the aggregations read it."""

    @property
    def fecha_venta(self) -> date: ...

    @property
    def monto(self) -> Decimal | float: ...

    @property
    def cantidad(self) -> Decimal | float | None: ...


class InsufficientHistoryError(ValueError):
    """Too few complete months to project; ``detail`` is safe to show."""

    @property
    def detail(self) -> str:
        return str(self.args[0])


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
    #: Every reason that limits the projection, one sentence each.
    advertencias: list[str]
    #: The same reasons joined in one text, as the PDF reports print them.
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
    """R², MAPE, and RMSE on a temporal holdout, never on training rows."""
    scores = point_metrics(actual, predicted, np.array([]))
    return {name: scores[name] for name in DAILY_METRIC_NAMES}


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


def _monthly_design(dates: Sequence[pd.Timestamp], seasonal: bool) -> pd.DataFrame:
    series = pd.Series(list(dates))
    index = months_elapsed(series)
    if seasonal:
        return build_seasonal_features(index, series.dt.month)
    return pd.DataFrame({"mes_indice": index.astype(float)})


def monthly_regression(seasonal: bool) -> ModelFn:
    """The monthly OLS as a model function, for the final fit and for backtests.

    It returns ``None`` when the window cannot support the specification: the
    seasonal one needs every calendar month and one degree of freedom left.
    Predictions and bounds are clipped at zero, as the user sees them.
    """

    def model(train: pd.DataFrame, target: str, future_dates: Sequence[pd.Timestamp]) -> pd.DataFrame | None:
        if len(train) < (SEASONAL_MIN_FIT if seasonal else TREND_MIN_FIT):
            return None
        if seasonal and _missing_calendar_months(train):
            return None
        design = _monthly_design(list(train["fecha"]) + list(future_dates), seasonal)
        fitted = sm.OLS(train[target].to_numpy(dtype=float), _with_constant(design.iloc[: len(train)])).fit()
        frame = fitted.get_prediction(_with_constant(design.iloc[len(train) :])).summary_frame(alpha=ALPHA)
        return pd.DataFrame(
            {
                "mean": frame["mean"].clip(lower=0).to_numpy(),
                "lower": frame["obs_ci_lower"].clip(lower=0).to_numpy(),
                "upper": frame["obs_ci_upper"].clip(lower=0).to_numpy(),
            }
        )

    return model


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


def applied_model(observed: int, history: pd.DataFrame, max_horizon: int = MAX_HORIZON) -> tuple[bool, int]:
    """Whether the seasonal specification applies, and the horizon, for a history."""
    seasonal = observed >= SEASONAL_MONTHS and not _missing_calendar_months(history)
    horizon = min(max_horizon, MAX_HORIZON if observed >= FULL_HORIZON_MONTHS else observed // 2)
    return seasonal, horizon


def monthly_forecast_series(
    monthly: pd.DataFrame, last_sale: date, max_horizon: int = MAX_HORIZON
) -> MonthlyForecast:
    """Project a monthly series with the model its history supports.

    ``monthly`` holds one row per observed month (month-end ``fecha``, ``monto``,
    ``cantidad``), as ``monthly_aggregates`` returns it. ``last_sale`` is the date
    of the latest sale, which tells whether the last month is complete.

    Metrics come from refitting the same specification at each of the last
    months and predicting the next one unseen, against the baselines in
    ``evaluation``. They are ``None`` when the history leaves no such month.
    """
    history, partial = _split_partial_month(monthly, last_sale)
    observed = len(history)
    if observed < MIN_MONTHS:
        raise InsufficientHistoryError(
            f"Se necesitan al menos {MIN_MONTHS} meses completos de ventas para proyectar; "
            f"hay {observed} y faltan {MIN_MONTHS - observed}."
        )

    missing = _missing_calendar_months(history)
    seasonal, horizon = applied_model(observed, history, max_horizon)

    warnings: list[str] = []
    if observed < SEASONAL_MONTHS:
        warnings.append(
            f"Con {observed} meses completos la proyección es una tendencia: no anticipa "
            f"temporadas, que se modelan desde {SEASONAL_MONTHS} meses. Se proyectan {horizon} meses."
        )
    elif missing:
        warnings.append(
            f"No hay ventas en {', '.join(missing)}, así que la proyección usa solo la "
            "tendencia, sin temporadas."
        )
    if horizon > RELIABLE_MONTHS:
        warnings.append(
            f"Los meses {RELIABLE_MONTHS + 1} a {horizon} son extrapolación sin validar: "
            "su incertidumbre es mayor."
        )

    first_future = partial["fecha"] if partial is not None else history["fecha"].iloc[-1] + pd.offsets.MonthEnd(1)
    future_dates = [first_future + pd.offsets.MonthEnd(step) for step in range(horizon)]
    model = monthly_regression(seasonal)

    objetivos: dict[str, TargetForecast] = {}
    for target in TARGETS:
        projection = model(history, target, future_dates)
        if projection is None:  # unreachable: the rule only picks specifications the history supports
            raise InsufficientHistoryError("No se pudo ajustar el modelo con este historial.")
        points = [
            ForecastPoint(
                fecha=moment,
                prediccion=float(row.mean),
                inferior=float(row.lower),
                superior=float(row.upper),
                extrapolacion=step > RELIABLE_MONTHS,
            )
            for step, (moment, row) in enumerate(zip(future_dates, projection.itertuples(), strict=True), start=1)
        ]
        metrics = one_step_metrics(history, target, model, min_train=MIN_MONTHS)
        objetivos[target] = TargetForecast(puntos=points, metricas=metrics)

    return MonthlyForecast(
        modelo="tendencia_estacional" if seasonal else "tendencia",
        horizonte=horizon,
        meses_observados=observed,
        advertencias=warnings,
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
    dates: Sequence[date],
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
    # SQLAlchemy returns ``date`` objects on both SQLite and PostgreSQL.
    parsed = list(dates)
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
