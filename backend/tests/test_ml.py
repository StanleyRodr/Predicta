"""Unit tests for ML models (linear predictor, seasonality)."""

import numpy as np
import pandas as pd

from app.ml_models.forecast import build_seasonal_features, monthly_aggregates
from app.models import models


def test_seasonality_features_include_trend_and_all_months():
    features = build_seasonal_features(
        np.array([0, 1]), pd.Series([1, 12])
    )

    assert list(features.columns) == ["mes_indice"] + [f"mes_{month}" for month in range(1, 13)]
    assert features.shape == (2, 13)
    assert features.loc[0, "mes_1"] == 1
    assert features.loc[1, "mes_12"] == 1


def test_monthly_aggregates_sums_sales_by_month():
    sales = [
        models.Venta(fecha_venta=pd.Timestamp("2026-01-10"), monto=10),
        models.Venta(fecha_venta=pd.Timestamp("2026-01-20"), monto=15),
        models.Venta(fecha_venta=pd.Timestamp("2026-02-01"), monto=20),
    ]

    result = monthly_aggregates(sales)

    assert len(result) == 2
    assert result["monto"].tolist() == [25.0, 20.0]


def test_monthly_aggregates_returns_month_end_dates():
    sales = [models.Venta(fecha_venta=pd.Timestamp("2026-03-10"), monto=10)]

    result = monthly_aggregates(sales)

    assert result.iloc[0]["fecha"].month == 3
    assert result.iloc[0]["fecha"].day == 31


def test_monthly_aggregates_does_not_create_empty_months():
    sales = [
        models.Venta(fecha_venta=pd.Timestamp("2026-01-10"), monto=10),
        models.Venta(fecha_venta=pd.Timestamp("2026-03-10"), monto=20),
    ]

    result = monthly_aggregates(sales)

    assert result["fecha"].dt.month.tolist() == [1, 3]
