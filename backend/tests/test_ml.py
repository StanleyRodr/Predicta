"""Unit tests for the forecasting models."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.ml_models.forecast import (
    InsufficientHistoryError,
    build_seasonal_features,
    build_weekly_features,
    daily_predictions,
    monthly_aggregates,
    monthly_forecast_series,
    months_elapsed,
)
from app.models import models

SEASON = [0, -80, 40, 60, 120, 30, 10, 50, -20, 0, 90, 200]


def _monthly(months, start=(2023, 1), trend=20.0, noise=15.0, seed=7, skip_months=()):
    """Month-end totals with trend, seasonality, and deterministic noise."""
    rng = np.random.default_rng(seed)
    rows = []
    index = 0
    while len(rows) < months:
        year = start[0] + (start[1] - 1 + index) // 12
        month = (start[1] - 1 + index) % 12 + 1
        index += 1
        if month in skip_months:
            continue
        base = 1000 + trend * index + SEASON[month - 1]
        rows.append(
            {
                "fecha": pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0),
                "monto": float(base + rng.normal(0, noise)),
                "cantidad": float(base / 10 + rng.normal(0, noise / 10)),
            }
        )
    return pd.DataFrame(rows)


def _last_day(monthly):
    return monthly["fecha"].max().date()


# ---------------------------------------------------------------- features


def test_trend_counts_calendar_months_not_rows():
    dates = pd.Series(pd.to_datetime(["2026-01-31", "2026-03-31"]))

    assert months_elapsed(dates).tolist() == [0, 2]


def test_seasonal_features_use_trend_and_eleven_month_dummies():
    features = build_seasonal_features(np.array([0, 1, 2]), pd.Series([1, 2, 12]))

    assert list(features.columns) == ["mes_indice"] + [f"mes_{month}" for month in range(2, 13)]
    assert features.loc[0, ["mes_2", "mes_12"]].tolist() == [0, 0]
    assert features.loc[1, "mes_2"] == 1
    assert features.loc[2, "mes_12"] == 1


def test_weekly_features_use_trend_and_six_weekday_dummies():
    features = build_weekly_features(np.array([0, 1]), pd.Series([0, 6]))

    assert list(features.columns) == ["dia_indice"] + [f"dia_{day}" for day in range(2, 8)]
    assert features.loc[0].sum() == 0
    assert features.loc[1, "dia_7"] == 1


# ---------------------------------------------------------------- aggregation


def test_monthly_aggregates_sums_sales_by_month():
    sales = [
        models.Venta(fecha_venta=date(2026, 1, 10), monto=10),
        models.Venta(fecha_venta=date(2026, 1, 20), monto=15),
        models.Venta(fecha_venta=date(2026, 2, 1), monto=20),
    ]

    result = monthly_aggregates(sales)

    assert result["monto"].tolist() == [25.0, 20.0]
    assert result.iloc[0]["fecha"].day == 31


def test_monthly_aggregates_does_not_create_empty_months():
    sales = [
        models.Venta(fecha_venta=date(2026, 1, 10), monto=10),
        models.Venta(fecha_venta=date(2026, 3, 10), monto=20),
    ]

    assert monthly_aggregates(sales)["fecha"].dt.month.tolist() == [1, 3]


# ---------------------------------------------------------------- model choice


def test_fewer_than_six_months_explains_how_many_are_missing():
    monthly = _monthly(5)

    with pytest.raises(InsufficientHistoryError) as error:
        monthly_forecast_series(monthly, _last_day(monthly))

    assert "6 meses completos" in str(error.value)
    assert "faltan 1" in str(error.value)


@pytest.mark.parametrize(
    ("months", "model", "horizon"),
    [(6, "tendencia", 3), (23, "tendencia", 11), (24, "tendencia", 12), (35, "tendencia", 12), (36, "tendencia_estacional", 12)],
)
def test_model_and_horizon_follow_observed_months(months, model, horizon):
    monthly = _monthly(months)

    forecast = monthly_forecast_series(monthly, _last_day(monthly))

    assert forecast.modelo == model
    assert forecast.horizonte == horizon
    assert forecast.meses_observados == months
    assert len(forecast.objetivos["monto"].puntos) == horizon
    assert len(forecast.objetivos["cantidad"].puntos) == horizon


def test_max_horizon_caps_the_applied_horizon():
    monthly = _monthly(30)

    assert monthly_forecast_series(monthly, _last_day(monthly), max_horizon=6).horizonte == 6


def test_short_history_warns_that_seasons_are_not_modeled():
    monthly = _monthly(10)

    forecast = monthly_forecast_series(monthly, _last_day(monthly))

    assert "temporada" in forecast.advertencia


def test_two_years_still_use_trend_and_say_when_seasons_start():
    monthly = _monthly(30)

    forecast = monthly_forecast_series(monthly, _last_day(monthly))

    assert forecast.modelo == "tendencia"
    assert forecast.horizonte == 12
    assert "desde 36 meses" in forecast.advertencia


def test_seasonality_needs_every_calendar_month_observed():
    monthly = _monthly(38, skip_months=(8,))

    forecast = monthly_forecast_series(monthly, _last_day(monthly))

    assert forecast.modelo == "tendencia"
    assert forecast.horizonte == 12
    assert "Agosto" in forecast.advertencia


# ---------------------------------------------------------------- partial month


def test_incomplete_last_month_is_left_out_of_the_fit_and_projected_first():
    monthly = _monthly(9)
    last_sale = (monthly["fecha"].max() - pd.Timedelta(days=12)).date()

    forecast = monthly_forecast_series(monthly, last_sale)

    assert forecast.meses_observados == 8
    assert forecast.historial["fecha"].max() == monthly["fecha"].iloc[7]
    assert forecast.mes_parcial is not None
    assert forecast.mes_parcial["fecha"] == monthly["fecha"].iloc[8]
    assert forecast.objetivos["monto"].puntos[0].fecha == monthly["fecha"].iloc[8]
    assert forecast.horizonte == 4


def test_complete_last_month_is_fitted_and_projection_starts_next_month():
    monthly = _monthly(8)

    forecast = monthly_forecast_series(monthly, _last_day(monthly))

    assert forecast.mes_parcial is None
    assert forecast.objetivos["monto"].puntos[0].fecha == monthly["fecha"].max() + pd.offsets.MonthEnd(1)


# ---------------------------------------------------------------- points


def test_points_are_consecutive_months_flagging_extrapolation_from_month_seven():
    monthly = _monthly(24)

    points = monthly_forecast_series(monthly, _last_day(monthly)).objetivos["monto"].puntos

    expected = [monthly["fecha"].max() + pd.offsets.MonthEnd(step) for step in range(1, 13)]
    assert [point.fecha for point in points] == expected
    assert points[5].extrapolacion is False
    assert points[6].extrapolacion is True


def test_intervals_contain_the_point_and_are_never_negative():
    falling = _monthly(12, trend=-75.0)

    forecast = monthly_forecast_series(falling, _last_day(falling))

    for target in forecast.objetivos.values():
        for point in target.puntos:
            assert 0 <= point.inferior <= point.prediccion <= point.superior
    assert forecast.objetivos["monto"].puntos[-1].prediccion == 0


def test_interval_widens_further_from_the_data():
    monthly = _monthly(12)

    points = monthly_forecast_series(monthly, _last_day(monthly)).objetivos["monto"].puntos

    assert points[-1].superior - points[-1].inferior > points[0].superior - points[0].inferior


def test_metrics_come_from_one_month_ahead_predictions_of_the_last_months():
    monthly = _monthly(24)

    metrics = monthly_forecast_series(monthly, _last_day(monthly)).objetivos["monto"].metricas

    assert set(metrics) == {"r2", "mape", "rmse", "wape", "mase", "mejora_vs_referencia", "referencia", "origenes"}
    assert metrics["origenes"] == 6
    assert metrics["rmse"] >= 0 and metrics["wape"] >= 0 and metrics["mase"] >= 0
    assert metrics["referencia"] in {"ultimo_valor", "mismo_mes_anio_anterior", "promedio_movil_3"}
    assert metrics["mejora_vs_referencia"] is not None


def test_metrics_stay_null_when_no_month_can_be_predicted_unseen():
    monthly = _monthly(6)

    metrics = monthly_forecast_series(monthly, _last_day(monthly)).objetivos["monto"].metricas

    assert metrics["origenes"] == 0
    for name in ("r2", "mape", "rmse", "wape", "mase", "mejora_vs_referencia", "referencia"):
        assert metrics[name] is None


def test_a_single_unseen_month_leaves_r2_null_but_scores_the_error():
    monthly = _monthly(7)

    metrics = monthly_forecast_series(monthly, _last_day(monthly)).objetivos["monto"].metricas

    assert metrics["origenes"] == 1
    assert metrics["r2"] is None
    assert metrics["wape"] is not None


def test_category_projections_add_up_to_the_total():
    first = _monthly(24, seed=1)
    second = _monthly(24, seed=2, trend=5.0)
    total = first.copy()
    total[["monto", "cantidad"]] = first[["monto", "cantidad"]] + second[["monto", "cantidad"]]
    last = _last_day(total)

    parts = [monthly_forecast_series(frame, last) for frame in (first, second)]
    whole = monthly_forecast_series(total, last)

    assert {part.modelo for part in parts} == {whole.modelo}
    for index, point in enumerate(whole.objetivos["monto"].puntos):
        assert point.prediccion == pytest.approx(
            sum(part.objetivos["monto"].puntos[index].prediccion for part in parts)
        )


# ---------------------------------------------------------------- daily


def test_daily_prediction_returns_metrics_and_non_negative_interval():
    dates = [date(2026, 1, day) for day in (5, 6, 7, 8)]

    next_date, forecasts = daily_predictions(dates, [10, 12, 14, 16], [2, 3, 4, 5])

    assert next_date.isoformat() == "2026-01-09"
    for forecast in forecasts.values():
        assert 0 <= forecast.lower <= forecast.prediction <= forecast.upper
        assert set(forecast.metrics) == {"r2", "mape", "rmse"}
    assert forecasts["monto"].prediction == pytest.approx(18.0)


def test_daily_prediction_with_two_days_uses_their_mean():
    next_date, forecasts = daily_predictions([date(2026, 1, 5), date(2026, 1, 6)], [10, 20], [1, 3])

    assert next_date.isoformat() == "2026-01-07"
    assert forecasts["monto"].prediction == pytest.approx(15.0)
    assert forecasts["monto"].lower <= 15.0 <= forecasts["monto"].upper


def test_daily_prediction_uses_weekdays_with_two_full_weeks():
    days = pd.date_range("2026-01-05", periods=21, freq="D")
    amounts = [100 + (50 if day.weekday() == 5 else 0) for day in days]

    next_date, forecasts = daily_predictions([day.date() for day in days], amounts, [1] * 21)

    assert next_date.weekday() == 0
    assert forecasts["monto"].prediction == pytest.approx(100, abs=1)
