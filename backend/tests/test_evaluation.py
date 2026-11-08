"""Tests for baselines, error metrics, and rolling-origin evaluation."""

import math

import numpy as np
import pandas as pd
import pytest

from app.ml_models.evaluation import (
    BASELINES,
    BacktestRecord,
    improvement,
    interval_coverage,
    mase,
    moving_average,
    naive_last,
    rolling_origin,
    seasonal_naive,
    wape,
)


def _series(values, start="2024-01"):
    dates = pd.period_range(start, periods=len(values), freq="M").to_timestamp("M")
    return pd.DataFrame({"fecha": dates, "monto": [float(v) for v in values]})


# ---------------------------------------------------------------- baselines


def test_naive_last_repeats_the_last_observation():
    history = _series([10, 20, 30])

    assert naive_last(history, "monto", pd.Timestamp("2024-05-31")) == 30


def test_seasonal_naive_uses_the_same_month_a_year_earlier():
    history = _series(range(1, 14))

    assert seasonal_naive(history, "monto", pd.Timestamp("2025-02-28")) == 2
    assert seasonal_naive(history, "monto", pd.Timestamp("2025-03-31")) == 3


def test_seasonal_naive_is_null_without_that_month():
    history = _series([5, 6, 7])

    assert seasonal_naive(history, "monto", pd.Timestamp("2024-04-30")) is None


def test_moving_average_uses_the_last_three_months():
    history = _series([100, 1, 2, 3])

    assert moving_average(history, "monto", pd.Timestamp("2024-05-31")) == 2


# ---------------------------------------------------------------- metrics


def test_wape_divides_absolute_errors_by_total_actuals():
    assert wape(np.array([100.0, 50.0]), np.array([90.0, 60.0])) == pytest.approx(20 / 150 * 100)


def test_wape_is_null_when_every_actual_is_zero():
    assert wape(np.array([0.0, 0.0]), np.array([1.0, 2.0])) is None


def test_mase_scales_by_the_in_sample_one_month_naive_error():
    training = np.array([10.0, 12.0, 11.0, 15.0])  # naive errors 2, 1, 4 -> 7 / 3

    value = mase(np.array([20.0]), np.array([18.0]), training)

    assert value == pytest.approx(2 / (7 / 3))


def test_mase_is_null_for_a_flat_training_series():
    assert mase(np.array([5.0]), np.array([4.0]), np.array([3.0, 3.0, 3.0])) is None


def test_improvement_is_relative_to_the_best_baseline():
    assert improvement(8.0, 10.0) == pytest.approx(20.0)
    assert improvement(12.0, 10.0) == pytest.approx(-20.0)
    assert improvement(None, 10.0) is None
    assert improvement(5.0, 0.0) is None


# ---------------------------------------------------------------- rolling origin


def test_rolling_origin_never_lets_a_model_see_the_month_it_predicts():
    history = _series(range(100, 124))
    seen = []

    def spy(train, target, future_dates):
        seen.append((train["fecha"].max(), list(future_dates)))
        last = float(train[target].iloc[-1])
        return pd.DataFrame({"mean": [last] * len(future_dates), "lower": [None] * len(future_dates), "upper": [None] * len(future_dates)})

    records = rolling_origin(history, "monto", spy, initial=18, horizons=range(1, 7))

    assert seen, "the model was never fitted"
    for train_end, future in seen:
        assert all(moment > train_end for moment in future)
    assert {record.origen for record in records} == set(range(18, 24))
    assert max(record.horizonte for record in records) == 6
    assert all(record.origen + record.horizonte <= 24 for record in records)


def test_rolling_origin_records_actual_and_prediction_per_horizon():
    history = _series(range(1, 25))

    def last_value(train, target, future_dates):
        last = float(train[target].iloc[-1])
        return pd.DataFrame({"mean": [last] * len(future_dates), "lower": [math.nan] * len(future_dates), "upper": [math.nan] * len(future_dates)})

    records = rolling_origin(history, "monto", last_value, initial=20, horizons=[1, 2])
    first = next(record for record in records if record.origen == 20 and record.horizonte == 2)

    assert first.real == 22
    assert first.prediccion == 20


def test_interval_coverage_counts_actuals_inside_the_bounds():
    stamp = pd.Timestamp("2025-01-31")
    records = [
        BacktestRecord(18, 1, stamp, 10.0, 10.0, 8.0, 12.0),
        BacktestRecord(19, 1, stamp, 15.0, 10.0, 8.0, 12.0),
        BacktestRecord(20, 1, stamp, 9.0, 9.0, None, None),
    ]

    assert interval_coverage(records) == pytest.approx(50.0)
    assert interval_coverage(records[2:]) is None


def test_baselines_are_named_for_the_report():
    assert set(BASELINES) == {"ultimo_valor", "mismo_mes_anio_anterior", "promedio_movil_3"}
