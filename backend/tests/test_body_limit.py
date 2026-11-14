"""Oversized bodies are refused with 413 before the application reads them."""

import pytest

from app.core.middleware import DEFAULT_BODY_LIMIT, MEGABYTE, UPLOAD_BODY_LIMIT
from app.services import etl_service

TOO_LARGE = {"detail": "La solicitud es demasiado grande."}


@pytest.fixture
def read_calls(monkeypatch):
    """Count the calls to ``read_limited``, the ETL's own 25 MB guard."""
    calls = []
    original = etl_service.read_limited

    def spy(stream):
        calls.append(stream)
        return original(stream)

    monkeypatch.setattr(etl_service, "read_limited", spy)
    return calls


def test_limits_match_the_plan():
    assert UPLOAD_BODY_LIMIT == 26 * MEGABYTE
    assert DEFAULT_BODY_LIMIT == 1 * MEGABYTE


def test_declared_27_mb_upload_is_refused_without_reading_it(client, auth_headers, read_calls):
    response = client.post(
        "/etl/upload-ventas",
        headers={**auth_headers, "Content-Type": "multipart/form-data; boundary=x"},
        content=b"x" * (27 * MEGABYTE),
    )
    assert response.status_code == 413
    assert response.json() == TOO_LARGE
    assert read_calls == []


def test_chunked_upload_is_cut_past_26_mb(client, auth_headers, read_calls):
    def chunks():
        for _ in range(27):
            yield b"x" * MEGABYTE

    response = client.post(
        "/etl/upload-ventas",
        headers={**auth_headers, "Content-Type": "multipart/form-data; boundary=x"},
        content=chunks(),
    )
    assert response.status_code == 413
    assert response.json() == TOO_LARGE
    assert read_calls == []


def test_2_mb_registration_is_refused(client):
    payload = '{"nombre_usuario": "' + "a" * (2 * MEGABYTE) + '"}'
    response = client.post(
        "/users/register", content=payload, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json() == TOO_LARGE


def test_chunked_body_past_1_mb_is_cut_outside_the_etl(client):
    def chunks():
        for _ in range(3):
            yield b"a" * MEGABYTE

    response = client.post(
        "/users/register", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 413
    assert response.json() == TOO_LARGE


def test_1_mb_csv_still_uploads(client, auth_headers, read_calls):
    header = b"producto,monto,categoria,fecha\n"
    row = b"Arroz,25.50,Abarrotes,2026-01-10\n"
    rows = [row.replace(b"Arroz", f"Arroz {n}".encode()) for n in range(MEGABYTE // len(row) + 1)]
    contents = header + b"".join(rows)
    assert len(contents) > MEGABYTE

    response = client.post(
        "/etl/upload-ventas",
        headers=auth_headers,
        files={"file": ("ventas.csv", contents, "text/csv")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["registros_cargados"] == len(rows)
    assert len(read_calls) == 1
