"""Per-user isolation of every private endpoint.

The first user (``auth_headers``) owns huge, oddly named sales; the second user
(``second_user``) owns small ones. Every private endpoint is called as the
second user, and nothing of the first user may show up: no product or category
name and no amount anywhere near the first user's values.

Every new endpoint with private data must be added to ``PRIVATE_CASES``;
``test_every_private_route_is_covered`` fails otherwise.
"""

import io
import json
import re
from datetime import date

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from app.main import app

FOREIGN_PRODUCT = "ProductoAjeno"
FOREIGN_CATEGORY = "CategoriaAjena"
FOREIGN_AMOUNT = 77_777.77
# The second user's sales stay far below this, so any larger number is a leak.
LEAK_THRESHOLD = 50_000
FOREIGN_TEXT = re.compile(r"Ajen|77,?777")
LARGE_FORMATTED_NUMBER = re.compile(r"\d{2,},\d{3}(?:\.\d+)?|\d{5,}(?:\.\d+)?")

MONTHS = [(2023 + index // 12, index % 12 + 1) for index in range(24)]


def _upload(client, headers, rows):
    lines = ["producto,monto,categoria,fecha,cantidad"]
    lines.extend(",".join(map(str, row)) for row in rows)
    response = client.post(
        "/etl/upload-ventas",
        headers=headers,
        files={"file": ("ventas.csv", "\n".join(lines).encode(), "text/csv")},
    )
    assert response.status_code == 200, response.text


@pytest.fixture
def two_users(client, auth_headers, second_user):
    """The first user's foreign sales and the second user's own, over the same 24 months."""
    foreign = [
        (FOREIGN_PRODUCT, FOREIGN_AMOUNT, FOREIGN_CATEGORY, date(year, month, day), 9_999)
        for year, month in MONTHS
        for day in (3, 17, 28)
    ]
    own = [
        (product, 100 + 3 * index + offset, category, date(year, month, day), 2)
        for index, (year, month) in enumerate(MONTHS)
        for product, category, day, offset in (("Pan", "Abarrotes", 5, 0), ("Jabon", "Limpieza", 28, 20))
    ]
    _upload(client, auth_headers, foreign)
    _upload(client, second_user, own)
    return auth_headers, second_user


# (method, path, params): every private route, with the variants that read data.
PRIVATE_CASES = [
    ("GET", "/users/me", {}),
    ("PUT", "/users/me", {}),
    ("GET", "/analytics/stats", {}),
    ("GET", "/analytics/stats/categories", {}),
    ("GET", "/analytics/stats/temporal", {}),
    ("GET", "/analytics/stats/series", {"granularidad": "mes"}),
    ("GET", "/analytics/stats/series", {"granularidad": "dia"}),
    ("GET", "/analytics/stats/series", {"granularidad": "mes", "por_categoria": "true"}),
    ("GET", "/analytics/ventas", {"limit": 200}),
    ("GET", "/analytics/ventas", {"limit": 200, "categoria": "Abarrotes", "producto": "Pan"}),
    ("GET", "/analytics/productos", {"categoria": "Abarrotes"}),
    ("GET", "/analytics/predict", {}),
    ("GET", "/analytics/forecast", {}),
    ("GET", "/analytics/forecast", {"categoria": "Abarrotes"}),
    ("GET", "/analytics/forecast", {"categoria": "Abarrotes", "producto": "pan"}),
    ("POST", "/analytics/predicciones", {}),
    ("GET", "/analytics/predicciones", {}),
    ("GET", "/analytics/export/excel", {}),
    ("GET", "/analytics/export/pdf", {}),
    ("GET", "/analytics/reporte-predictivo-anual-pdf", {}),
    ("GET", "/analytics/reporte-mensual/{mes}", {"mes": "Mayo"}),
    ("GET", "/analytics/prediccion-categorias/{categoria}", {"categoria": "Abarrotes"}),
    ("POST", "/etl/upload-ventas", {}),
    ("DELETE", "/etl/clear-history", {}),
]


def _numbers(value):
    if isinstance(value, bool):
        return
    if isinstance(value, int | float):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _numbers(item)
    elif isinstance(value, list):
        for item in value:
            yield from _numbers(item)


def _response_text(response):
    content_type = response.headers.get("content-type", "")
    if content_type == "application/pdf":
        reader = PdfReader(io.BytesIO(response.content))
        return "\n".join(page.extract_text() for page in reader.pages)
    if "spreadsheetml" in content_type:
        workbook = load_workbook(io.BytesIO(response.content))
        return "\n".join(
            str(cell) for sheet in workbook for row in sheet.iter_rows(values_only=True) for cell in row if cell is not None
        )
    return response.text


def _call(client, headers, method, path, params):
    path_params = {key: value for key, value in params.items() if "{" + key + "}" in path}
    query = {key: value for key, value in params.items() if key not in path_params}
    url = path.format(**path_params)
    if method == "PUT":
        return client.put(url, headers=headers, json={"nombre_usuario": "second_renamed"})
    if method == "POST" and path == "/etl/upload-ventas":
        rows = "producto,monto,categoria,fecha\nSal,12,Abarrotes,2025-02-02"
        return client.post(url, headers=headers, files={"file": ("nuevo.csv", rows.encode(), "text/csv")})
    if method == "POST" and path == "/analytics/predicciones":
        return client.post(url, headers=headers, json={})
    return client.request(method, url, headers=headers, params=query)


@pytest.mark.parametrize(
    ("method", "path", "params"),
    PRIVATE_CASES,
    ids=[f"{method} {path} {json.dumps(params)}" for method, path, params in PRIVATE_CASES],
)
def test_second_user_never_sees_the_first_users_data(client, two_users, method, path, params):
    _, second = two_users

    response = _call(client, second, method, path, params)

    assert response.status_code in (200, 201), response.text
    text = _response_text(response)
    assert not FOREIGN_TEXT.search(text), FOREIGN_TEXT.search(text)
    if response.headers.get("content-type", "").startswith("application/json"):
        assert all(abs(number) < LEAK_THRESHOLD for number in _numbers(response.json()))
    else:
        assert not LARGE_FORMATTED_NUMBER.search(text), LARGE_FORMATTED_NUMBER.search(text)


def test_every_private_route_is_covered():
    # OpenAPI marks every operation that depends on the bearer token with ``security``.
    routes = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method, operation in operations.items()
        if operation.get("security")
    }
    covered = {(method, path) for method, path, _ in PRIVATE_CASES}
    assert routes == covered


def test_the_first_users_category_does_not_exist_for_the_second_user(client, two_users):
    _, second = two_users

    sales = client.get("/analytics/ventas", headers=second, params={"categoria": FOREIGN_CATEGORY})
    forecast = client.get("/analytics/forecast", headers=second, params={"categoria": FOREIGN_CATEGORY})
    report = client.get(f"/analytics/prediccion-categorias/{FOREIGN_CATEGORY}", headers=second)

    assert sales.status_code == 200
    assert sales.json()["total_registros"] == 0
    assert forecast.status_code in (404, 422)
    assert report.status_code in (400, 404)
    assert FOREIGN_PRODUCT not in report.text


def test_the_second_users_totals_are_only_their_own(client, two_users):
    first, second = two_users
    own_total = sum(100 + 3 * index + offset for index in range(24) for offset in (0, 20))

    second_stats = client.get("/analytics/stats", headers=second).json()
    first_stats = client.get("/analytics/stats", headers=first).json()

    assert second_stats["metricas_globales"]["total_ingresos"] == pytest.approx(own_total)
    assert first_stats["metricas_globales"]["total_ingresos"] == pytest.approx(FOREIGN_AMOUNT * 72)


def test_saved_predictions_belong_to_their_owner(client, two_users):
    first, second = two_users
    assert client.post("/analytics/predicciones", headers=first, json={}).status_code == 201

    page = client.get("/analytics/predicciones", headers=second).json()

    assert page["total_lotes"] == 0
    assert page["lotes"] == []


def test_suite_runs_on_the_configured_engine(test_db):
    from tests.conftest import TEST_DATABASE_URL

    with test_db() as session:
        dialect = session.get_bind().dialect.name
    assert dialect == ("postgresql" if TEST_DATABASE_URL else "sqlite")
