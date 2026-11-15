"""Thesis scenario «Comunicación de datos»: DataFrame → JSON without loss or errors.

The monthly history is a pandas DataFrame inside the model. These tests follow it
to the JSON text the frontend receives and compare every period and value with
the DataFrame it came from: no row lost or added, periods in ISO ``YYYY-MM``,
amounts and units equal to two decimals.
"""

import calendar
import json
from datetime import date

import pandas as pd

from app.ml_models.forecast import monthly_aggregates, monthly_forecast_series
from app.schemas.schemas import MonthlyForecastResponse
from app.services.prediction_service import forecast_payload

ISO_MONTH = r"^\d{4}-(0[1-9]|1[0-2])$"


def _monthly_frame(months: int = 14) -> pd.DataFrame:
    """Month-end totals with cents, so that rounding errors would show."""
    dates = pd.date_range("2025-01-31", periods=months, freq="ME")
    return pd.DataFrame(
        {
            "fecha": dates,
            "monto": [10_000.0 + 137.456 * step + (step % 3) * 0.333 for step in range(months)],
            "cantidad": [250.0 + 3.5 * step for step in range(months)],
        }
    )


def _round_trip(frame: pd.DataFrame) -> dict:
    """DataFrame → model → response schema → JSON text → Python, as HTTP does."""
    forecast = monthly_forecast_series(frame, frame["fecha"].iloc[-1].date())
    payload = {"usuario": "tesis", **forecast_payload(None, None, forecast)}
    text = MonthlyForecastResponse.model_validate(payload).model_dump_json()
    return json.loads(text)


def test_serializacion_json():
    frame = _monthly_frame()

    body = _round_trip(frame)

    history = body["historial"]
    assert len(history) == len(frame)
    for row, sent in zip(frame.itertuples(), history, strict=True):
        assert sent["periodo"] == f"{row.fecha.year:04d}-{row.fecha.month:02d}"
        assert sent["monto"] == round(row.monto, 2)
        assert sent["cantidad"] == round(row.cantidad, 2)
    assert pd.Series([month["periodo"] for month in body["proyeccion"]]).str.match(ISO_MONTH).all()
    assert len(body["proyeccion"]) == body["horizonte_aplicado"]


def test_serializacion_json_keeps_projection_values_and_intervals():
    frame = _monthly_frame()
    forecast = monthly_forecast_series(frame, frame["fecha"].iloc[-1].date())

    body = _round_trip(frame)

    for point, sent in zip(forecast.objetivos["monto"].puntos, body["proyeccion"], strict=True):
        assert sent["monto"]["prediccion"] == round(point.prediccion, 2)
        assert sent["monto"]["inferior"] == round(point.inferior, 2)
        assert sent["monto"]["superior"] == round(point.superior, 2)
        assert sent["extrapolacion"] is point.extrapolacion


def test_serializacion_json_through_the_api(client, auth_headers):
    """Sales uploaded through the ETL reach the client grouped by month without loss."""
    rows = []
    for index in range(12):
        year, month = 2025 + index // 12, index % 12 + 1
        last = calendar.monthrange(year, month)[1]
        rows.append(("Arroz", f"{1000 + 25.5 * index:.2f}", "Abarrotes", date(year, month, 3), 2))
        rows.append(("Leche", f"{400.25 + 10 * index:.2f}", "Lácteos", date(year, month, last), 1))
    lines = ["producto,monto,categoria,fecha,cantidad", *(",".join(map(str, row)) for row in rows)]
    upload = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", "\n".join(lines).encode(), "text/csv")},
    )
    assert upload.status_code == 200, upload.text

    response = client.get("/analytics/forecast", headers=auth_headers)

    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    sales = pd.DataFrame(rows, columns=["producto", "monto", "categoria", "fecha_venta", "cantidad"])
    sales["monto"] = sales["monto"].astype(float)
    expected = monthly_aggregates(list(sales.itertuples()))
    history = response.json()["historial"]
    assert [month["periodo"] for month in history] == [f"{moment:%Y-%m}" for moment in expected["fecha"]]
    assert [month["monto"] for month in history] == [round(value, 2) for value in expected["monto"]]
    assert [month["cantidad"] for month in history] == [round(value, 2) for value in expected["cantidad"]]
