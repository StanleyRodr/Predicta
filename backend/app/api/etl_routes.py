"""ETL endpoints for ingesting sales data from external files.

Supported formats: CSV, XLSX, and SQL ``INSERT INTO`` statements.
Each endpoint enforces user-level data isolation.
"""

import csv
import hashlib
import io
import math
import os
import re
import zipfile
from datetime import date
from typing import Any, BinaryIO

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models
from app.services.category_service import normalize_category

router = APIRouter(prefix="/etl", tags=["ETL"])

ALLOWED_EXTENSIONS = {"csv", "xlsx", "sql"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_XLSX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB
MAX_ROWS = int(os.getenv("MAX_UPLOAD_ROWS", "200000"))
MAX_REPORTED_ERRORS = 20
READ_CHUNK_BYTES = 1024 * 1024
REQUIRED_COLUMNS = {"producto", "monto", "fecha"}
SQL_DEFAULT_COLUMNS = ("producto", "monto", "categoria", "fecha", "cantidad")

# DECIMAL(10, 2) upper bound shared by ventas.monto and ventas.cantidad.
MAX_DECIMAL_VALUE = 99_999_999.99
MAX_PRODUCT_LENGTH = 150
MAX_CATEGORY_LENGTH = 100

THOUSANDS_NUMBER = re.compile(r"[+-]?[1-9]\d{0,2}(,\d{3})+(\.\d+)?")
DECIMAL_COMMA_NUMBER = re.compile(r"[+-]?\d+,\d{1,2}")
SQL_INSERT = re.compile(
    r"INSERT\s+INTO\s+[^\s(]+\s*(?:\(([^)]*)\))?\s*VALUES\s*", re.IGNORECASE
)


class RowValidationError(ValueError):
    """A row problem whose message is safe to show to the user."""


class FileValidationError(ValueError):
    """A file problem whose message is safe to show to the user."""


def _is_missing(value: object) -> bool:
    """Return whether a parsed cell is empty or represents a missing value."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _is_blank(value: object) -> bool:
    return _is_missing(value) or (isinstance(value, str) and not value.strip())


def _parse_number(value: object, label: str) -> float:
    """Read a number using comma thousands and point decimals.

    A comma followed by one or two digits stays accepted as a legacy decimal.
    Spreadsheet cells that are already numeric skip this text handling.
    """
    text = str(value).strip()
    if "," in text:
        if THOUSANDS_NUMBER.fullmatch(text):
            text = text.replace(",", "")
        elif DECIMAL_COMMA_NUMBER.fullmatch(text):
            text = text.replace(",", ".")
        else:
            raise RowValidationError(f"{label} no tiene un formato numerico valido")
    try:
        number = float(text)
    except ValueError as exc:
        raise RowValidationError(f"{label} no es numerico") from exc
    if not math.isfinite(number):
        raise RowValidationError(f"{label} debe ser finito")
    return round(number, 2)


def _parse_amount(value: object) -> float:
    """Parse an amount inside the range the database column can store."""
    if _is_blank(value):
        raise RowValidationError("el monto es obligatorio")
    amount = _parse_number(value, "el monto")
    if amount <= 0:
        raise RowValidationError("el monto debe ser mayor que cero")
    if amount > MAX_DECIMAL_VALUE:
        raise RowValidationError("el monto supera el maximo permitido")
    return amount


def _parse_quantity(value: object) -> float:
    """Parse a non-negative quantity, defaulting legacy rows to one unit."""
    if _is_blank(value):
        return 1.0
    quantity = _parse_number(value, "la cantidad")
    if quantity < 0:
        raise RowValidationError("la cantidad no puede ser negativa")
    if quantity > MAX_DECIMAL_VALUE:
        raise RowValidationError("la cantidad supera el maximo permitido")
    return quantity


def _parse_date(value: object) -> date:
    """Parse a date or raise a validation error."""
    if _is_missing(value):
        raise RowValidationError("la fecha es obligatoria")

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise RowValidationError("la fecha no es valida")
    return parsed.date()


def _decode_text(contents: bytes) -> str:
    """Decode common CSV/SQL encodings without replacing invalid bytes."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise FileValidationError("el archivo no usa una codificacion compatible")


def _normalize_row(row: dict[Any, Any]) -> dict[str, Any]:
    """Normalize headers so files with surrounding spaces remain usable."""
    return {
        str(key).strip().lower().replace(" ", "_"): value for key, value in row.items()
    }


def _require_columns(headers: set[str]) -> None:
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise FileValidationError(
            f"faltan columnas requeridas: {', '.join(sorted(missing))}"
        )


def _parse_csv(contents: bytes) -> list[dict[str, Any]]:
    """Parse comma, semicolon, or tab-delimited CSV content."""
    text = _decode_text(contents)
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    _require_columns(
        {
            str(header).strip().lower().replace(" ", "_")
            for header in reader.fieldnames or []
        }
    )
    return [_normalize_row(row) for row in reader]


def _check_xlsx_size(contents: bytes) -> None:
    """Reject archives that declare more data than they can safely expand to."""
    with zipfile.ZipFile(io.BytesIO(contents)) as archive:
        declared_size = sum(item.file_size for item in archive.infolist())
    if declared_size > MAX_XLSX_UNCOMPRESSED_BYTES:
        raise HTTPException(
            status_code=413, detail="El contenido del archivo XLSX es demasiado grande."
        )


def _parse_xlsx(contents: bytes) -> list[dict[str, Any]]:
    """Parse an XLSX file, reading at most one row past the allowed limit."""
    _check_xlsx_size(contents)
    frame = pd.read_excel(io.BytesIO(contents), nrows=MAX_ROWS + 1)
    rows = [_normalize_row(row) for row in frame.to_dict(orient="records")]
    _require_columns(set(rows[0]) if rows else set())
    return rows


def _read_sql_tuples(text: str, start: int) -> list[list[str | None]]:
    """Read ``(...), (...)`` value groups, honoring quotes, up to the semicolon."""
    groups: list[list[str | None]] = []
    current: list[str | None] | None = None
    token: list[str] = []
    quote: str | None = None
    was_quoted = False
    position = start

    while position < len(text):
        char = text[position]
        if quote:
            if char != quote:
                token.append(char)
            elif text[position + 1 : position + 2] == quote:
                token.append(char)
                position += 1
            else:
                quote = None
        elif char in "'\"":
            quote = char
            was_quoted = True
        elif current is None:
            if char == "(":
                current = []
            elif char == ";":
                break
        elif char in ",)":
            value = "".join(token) if was_quoted else "".join(token).strip()
            current.append(None if not was_quoted and value.upper() == "NULL" else value)
            token = []
            was_quoted = False
            if char == ")":
                groups.append(current)
                current = None
        else:
            token.append(char)
        position += 1
    return groups


def _parse_sql(contents: bytes) -> list[dict[str, Any]]:
    """Parse ``INSERT ... VALUES`` statements without executing any SQL."""
    sql_text = _decode_text(contents)
    rows: list[dict[str, Any]] = []
    for statement in SQL_INSERT.finditer(sql_text):
        declared = statement.group(1)
        columns = (
            [name.strip().strip("`\"[]").lower() for name in declared.split(",")]
            if declared
            else list(SQL_DEFAULT_COLUMNS)
        )
        for values in _read_sql_tuples(sql_text, statement.end()):
            rows.append(_normalize_row(dict(zip(columns, values, strict=False))))
    return rows


def _build_venta(row: dict[str, Any], user_id: int) -> models.Venta:
    """Validate and translate a raw row into a ``Venta`` ORM instance."""
    producto = row.get("producto")
    if _is_missing(producto) or not str(producto).strip():
        raise RowValidationError("el producto es obligatorio")
    product_name = str(producto).strip()
    if len(product_name) > MAX_PRODUCT_LENGTH:
        raise RowValidationError("el producto supera el largo maximo")

    category = normalize_category(row.get("categoria"))
    if category is not None and len(category) > MAX_CATEGORY_LENGTH:
        raise RowValidationError("la categoria supera el largo maximo")

    return models.Venta(
        id_usuario=user_id,
        producto=product_name,
        monto=_parse_amount(row.get("monto")),
        cantidad=_parse_quantity(row.get("cantidad")),
        categoria=category,
        fecha_venta=_parse_date(row.get("fecha")),
    )


def _read_limited(stream: BinaryIO) -> tuple[bytes, str]:
    """Read in chunks, aborting past the limit, and return bytes plus SHA-256."""
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    total = 0
    while chunk := stream.read(READ_CHUNK_BYTES):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Archivo demasiado grande (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
            )
        digest.update(chunk)
        chunks.append(chunk)
    return b"".join(chunks), digest.hexdigest()


def _read_rows(extension: str, contents: bytes) -> list[dict[str, Any]]:
    """Parse a file, exposing only controlled messages to the client."""
    try:
        if extension == "xlsx":
            rows = _parse_xlsx(contents)
        elif extension == "csv":
            rows = _parse_csv(contents)
        else:
            rows = _parse_sql(contents)
    except FileValidationError as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.warning("Archivo de ventas ilegible: {}", exc)
        raise HTTPException(status_code=400, detail="No se pudo leer el archivo.") from exc

    if len(rows) > MAX_ROWS:
        raise HTTPException(
            status_code=413, detail=f"El archivo supera el maximo de {MAX_ROWS:,} filas."
        )
    return rows


def _duplicate_upload_error() -> HTTPException:
    return HTTPException(
        status_code=409,
        detail="Este archivo ya fue cargado. Purga el historial si deseas cargarlo de nuevo.",
    )


# Declared as a plain function so FastAPI runs this blocking work in its
# threadpool instead of stalling the event loop for every other request.
@router.post("/upload-ventas")
def upload_ventas(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Ingest sales rows from a CSV, XLSX, or SQL file.

    The file is detected by extension. All rows are assigned to the
    authenticated user.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo vacio.")

    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no compatible. Usa: {', '.join(sorted(ALLOWED_EXTENSIONS))}.",
        )

    contents, file_hash = _read_limited(file.file)
    already_loaded = (
        db.query(models.CargaArchivo.id_carga)
        .filter(
            models.CargaArchivo.id_usuario == current_user.id_usuario,
            models.CargaArchivo.sha256 == file_hash,
        )
        .first()
    )
    if already_loaded:
        raise _duplicate_upload_error()

    rows = _read_rows(extension, contents)

    errores: list[dict[str, Any]] = []
    ventas_creadas = 0
    # SQL rows have no header line, so their numbering starts at one.
    first_row = 1 if extension == "sql" else 2
    for row_number, row in enumerate(rows, start=first_row):
        try:
            db.add(_build_venta(row, current_user.id_usuario))
            ventas_creadas += 1
        except RowValidationError as exc:
            if len(errores) < MAX_REPORTED_ERRORS:
                errores.append({"fila": row_number, "error": str(exc)})
        except (TypeError, ValueError):
            if len(errores) < MAX_REPORTED_ERRORS:
                errores.append({"fila": row_number, "error": "la fila tiene valores no validos"})

    if ventas_creadas:
        db.add(models.CargaArchivo(id_usuario=current_user.id_usuario, sha256=file_hash))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise _duplicate_upload_error() from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Error al guardar el archivo de ventas.")
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar el archivo completo.",
        ) from exc

    rechazadas = len(rows) - ventas_creadas
    return {
        "message": f"Procesamiento exitoso: {ventas_creadas} registros cargados.",
        "registros_leidos": len(rows),
        "registros_cargados": ventas_creadas,
        "filas_rechazadas": rechazadas,
        "errores": errores,
    }


@router.delete("/clear-history")
def clear_history(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Delete all sales rows owned by the authenticated user."""
    try:
        deleted = (
            db.query(models.Venta)
            .filter(models.Venta.id_usuario == current_user.id_usuario)
            .delete(synchronize_session=False)
        )
        # Purged files must be loadable again.
        db.query(models.CargaArchivo).filter(
            models.CargaArchivo.id_usuario == current_user.id_usuario
        ).delete(synchronize_session=False)
        db.commit()
        if deleted == 0:
            return {
                "status": "success",
                "message": "El historial ya se encontraba vacio.",
            }
        return {
            "status": "success",
            "message": f"Historial purgado. Se eliminaron {deleted} registros.",
            "id_usuario": current_user.id_usuario,
        }
    except Exception as exc:
        db.rollback()
        logger.exception("Error al depurar el historial del usuario.")
        raise HTTPException(
            status_code=500,
            detail="No se pudo depurar el historial.",
        ) from exc
