"""Parsing, validation, and loading of sales files.

Supported formats: CSV, XLSX, and SQL ``INSERT INTO`` statements. SQL is only
parsed, never executed. Every error raised here carries a message that is safe
to show to the user.
"""

import csv
import hashlib
import io
import math
import re
import zipfile
from datetime import date, datetime
from typing import Any, BinaryIO

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import models
from app.services import column_mapping
from app.services.category_service import normalize_category, normalize_product
from app.services.errors import UserFacingError

ALLOWED_EXTENSIONS = {"csv", "xlsx", "sql"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_XLSX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB
MAX_ROWS = settings.max_upload_rows
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
DIGITS_ONLY = re.compile(r"\d+")
SAMPLE_ROWS = 5


class RowValidationError(UserFacingError):
    """A row problem whose message is safe to show to the user."""


class FileValidationError(UserFacingError):
    """A file problem whose message is safe to show to the user."""


class FileTooLargeError(UserFacingError):
    """The file, its expanded content, or its row count exceeds a limit."""


class UnreadableFileError(UserFacingError):
    """The file could not be parsed; the cause is logged, not shown."""


class DuplicateUploadError(ValueError):
    """The same file content was already loaded by this user."""


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


def _parse_number(value: object, label: str, round_to: int | None = 2) -> float:
    """Read a number using comma thousands and point decimals.

    A comma followed by one or two digits stays accepted as a legacy decimal.
    Spreadsheet cells that are already numeric skip this text handling.
    ``round_to=None`` keeps full precision for values that are multiplied later.
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
    return number if round_to is None else round(number, round_to)


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
    # pandas reads a bare number as nanoseconds since 1970 and "15" as a day
    # of the current month, so plain numbers are never dates.
    is_number = isinstance(value, (int, float, np.integer, np.floating)) and not isinstance(
        value, (date, datetime)
    )
    if is_number or (isinstance(value, str) and DIGITS_ONLY.fullmatch(value.strip())):
        raise RowValidationError("la fecha no es valida")

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


def _normalize_header(header: object) -> str:
    """Strip, lowercase, and join words with ``_``; this is the header the API exposes."""
    return str(header).strip().lower().replace(" ", "_")


def _normalize_row(row: dict[Any, Any]) -> dict[str, Any]:
    """Normalize headers so files with surrounding spaces remain usable."""
    return {_normalize_header(key): value for key, value in row.items()}


def _require_columns(headers: set[str]) -> None:
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise FileValidationError(
            f"faltan columnas requeridas: {', '.join(sorted(missing))}"
        )


Table = tuple[list[str], list[dict[str, Any]]]


def _parse_csv(contents: bytes) -> Table:
    """Parse comma, semicolon, or tab-delimited CSV content into headers and rows."""
    text = _decode_text(contents)
    try:
        sniffed = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except csv.Error:
        sniffed = csv.excel
    # The sniffer only sees the first 8 KB: when no escaped quote ("") appears
    # there it guesses doublequote=False, and every later quoted field with an
    # escaped quote is cut short or merged with the next row. Escaped quotes are
    # always read as RFC 4180 defines them; only the delimiter comes from the sample.
    reader = csv.DictReader(io.StringIO(text), delimiter=sniffed.delimiter, quotechar='"', doublequote=True)
    headers = [_normalize_header(header) for header in reader.fieldnames or []]
    return headers, [_normalize_row(row) for row in reader]


def _check_xlsx_size(contents: bytes) -> None:
    """Reject archives that declare more data than they can safely expand to."""
    with zipfile.ZipFile(io.BytesIO(contents)) as archive:
        declared_size = sum(item.file_size for item in archive.infolist())
    if declared_size > MAX_XLSX_UNCOMPRESSED_BYTES:
        raise FileTooLargeError("El contenido del archivo XLSX es demasiado grande.")


def _parse_xlsx(contents: bytes) -> Table:
    """Parse the first sheet of an XLSX file, reading at most one row past the limit."""
    _check_xlsx_size(contents)
    frame = pd.read_excel(io.BytesIO(contents), nrows=MAX_ROWS + 1)
    headers = [_normalize_header(header) for header in frame.columns]
    return headers, [_normalize_row(row) for row in frame.to_dict(orient="records")]


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


def _parse_sql(contents: bytes) -> Table:
    """Parse ``INSERT ... VALUES`` statements without executing any SQL.

    Headers are the declared column lists, merged in order of first appearance
    (or ``SQL_DEFAULT_COLUMNS``), never the keys of short value tuples.
    """
    sql_text = _decode_text(contents)
    headers: list[str] = []
    rows: list[dict[str, Any]] = []
    for statement in SQL_INSERT.finditer(sql_text):
        declared = statement.group(1)
        columns = (
            [name.strip().strip("`\"[]").lower() for name in declared.split(",")]
            if declared
            else list(SQL_DEFAULT_COLUMNS)
        )
        for header in (_normalize_header(column) for column in columns):
            if header not in headers:
                headers.append(header)
        for values in _read_sql_tuples(sql_text, statement.end()):
            rows.append(_normalize_row(dict(zip(columns, values, strict=False))))
    return headers, rows


def build_venta(row: dict[str, Any], user_id: int) -> models.Venta:
    """Validate and translate a raw row into a ``Venta`` ORM instance."""
    producto = row.get("producto")
    if _is_missing(producto) or not str(producto).strip():
        raise RowValidationError("el producto es obligatorio")
    product_name = normalize_product(str(producto))
    if len(product_name) > MAX_PRODUCT_LENGTH:
        raise RowValidationError("el producto supera el largo maximo")

    # An empty spreadsheet cell arrives as NaN, which must not become "Nan".
    raw_category = row.get("categoria")
    category = normalize_category(None if _is_missing(raw_category) else raw_category)
    if category is not None and len(category) > MAX_CATEGORY_LENGTH:
        raise RowValidationError("la categoria supera el largo maximo")

    if "monto" not in row and "precio_unitario" in row:
        quantity = _parse_quantity(row.get("cantidad"))
        amount = _derive_amount(row["precio_unitario"], quantity)
    else:
        amount = _parse_amount(row.get("monto"))
        quantity = _parse_quantity(row.get("cantidad"))

    return models.Venta(
        id_usuario=user_id,
        producto=product_name,
        monto=amount,
        cantidad=quantity,
        categoria=category,
        fecha_venta=_parse_date(row.get("fecha")),
    )


def _derive_amount(unit_price: object, quantity: float) -> float:
    """Return ``round(unit_price * quantity, 2)``; only the product is rounded."""
    if _is_blank(unit_price):
        raise RowValidationError("el precio unitario es obligatorio")
    amount = round(_parse_number(unit_price, "el precio unitario", round_to=None) * quantity, 2)
    if amount <= 0:
        raise RowValidationError("el precio unitario por la cantidad debe ser mayor que cero")
    if amount > MAX_DECIMAL_VALUE:
        raise RowValidationError("el monto supera el maximo permitido")
    return amount


def read_limited(stream: BinaryIO) -> tuple[bytes, str]:
    """Read in chunks, aborting past the limit, and return bytes plus SHA-256."""
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    total = 0
    while chunk := stream.read(READ_CHUNK_BYTES):
        total += len(chunk)
        if total > MAX_UPLOAD_BYTES:
            raise FileTooLargeError(
                f"Archivo demasiado grande (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB)."
            )
        digest.update(chunk)
        chunks.append(chunk)
    return b"".join(chunks), digest.hexdigest()


def read_table(extension: str, contents: bytes) -> Table:
    """Parse a file into headers and rows; only controlled messages leave this function."""
    try:
        if extension == "xlsx":
            headers, rows = _parse_xlsx(contents)
        elif extension == "csv":
            headers, rows = _parse_csv(contents)
        else:
            headers, rows = _parse_sql(contents)
    except (FileValidationError, FileTooLargeError):
        raise
    except Exception as exc:
        logger.warning("Archivo de ventas ilegible: {}", exc)
        raise UnreadableFileError("No se pudo leer el archivo.") from exc

    if len(rows) > MAX_ROWS:
        raise FileTooLargeError(f"El archivo supera el maximo de {MAX_ROWS:,} filas.")
    return headers, rows


def read_rows(extension: str, contents: bytes) -> list[dict[str, Any]]:
    """Parse a file and return only its rows."""
    return read_table(extension, contents)[1]


def _sample_text(value: object) -> str | None:
    """Render a raw cell for the preview: blanks become ``None``, dates ``YYYY-MM-DD``."""
    if _is_blank(value):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat() if value.time() == datetime.min.time() else value.isoformat(sep=" ")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (float, np.floating)) and float(value).is_integer():
        return str(int(value))
    return str(value).strip()


def analyze_columns(extension: str, contents: bytes) -> dict[str, Any]:
    """Return the file's headers, a short sample, and the proposed mapping."""
    headers, rows = read_table(extension, contents)
    proposal = column_mapping.propose_mapping(headers)
    assigned = {role: entry["columna"] for role, entry in proposal.items()}
    return {
        "columnas": headers,
        "muestra": [
            {header: _sample_text(row.get(header)) for header in headers}
            for row in rows[:SAMPLE_ROWS]
        ],
        "propuesta": proposal,
        "faltantes": column_mapping.missing_roles(assigned),
    }


def _mapped_rows(
    extension: str, contents: bytes, mapping: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Read the file and rename its columns to roles.

    Without a mapping, CSV and XLSX must use the exact names; SQL reports a
    missing column as a row error instead.
    """
    headers, rows = read_table(extension, contents)
    if mapping is None:
        if extension != "sql":
            _require_columns(set(headers))
        return rows
    validated = column_mapping.validate_mapping(mapping, headers)
    return column_mapping.apply_mapping(rows, validated)


def load_sales(
    db: Session,
    user_id: int,
    extension: str,
    contents: bytes,
    file_hash: str,
    mapeo: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate every row, store the valid ones in one transaction, and report the rest."""
    already_loaded = (
        db.query(models.CargaArchivo.id_carga)
        .filter(
            models.CargaArchivo.id_usuario == user_id,
            models.CargaArchivo.sha256 == file_hash,
        )
        .first()
    )
    if already_loaded:
        raise DuplicateUploadError

    rows = _mapped_rows(extension, contents, mapeo)

    errores: list[dict[str, Any]] = []
    ventas_creadas = 0
    # SQL rows have no header line, so their numbering starts at one.
    first_row = 1 if extension == "sql" else 2
    for row_number, row in enumerate(rows, start=first_row):
        try:
            db.add(build_venta(row, user_id))
            ventas_creadas += 1
        except RowValidationError as exc:
            if len(errores) < MAX_REPORTED_ERRORS:
                errores.append({"fila": row_number, "error": exc.detail})
        except (TypeError, ValueError):
            if len(errores) < MAX_REPORTED_ERRORS:
                errores.append({"fila": row_number, "error": "la fila tiene valores no validos"})

    if ventas_creadas:
        db.add(models.CargaArchivo(id_usuario=user_id, sha256=file_hash))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateUploadError from exc
    except Exception:
        db.rollback()
        raise

    return {
        "registros_leidos": len(rows),
        "registros_cargados": ventas_creadas,
        "filas_rechazadas": len(rows) - ventas_creadas,
        "errores": errores,
    }


def clear_sales(db: Session, user_id: int) -> int:
    """Delete the user's sales and upload hashes; return how many sales were deleted."""
    try:
        deleted = (
            db.query(models.Venta)
            .filter(models.Venta.id_usuario == user_id)
            .delete(synchronize_session=False)
        )
        # Purged files must be loadable again.
        db.query(models.CargaArchivo).filter(
            models.CargaArchivo.id_usuario == user_id
        ).delete(synchronize_session=False)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return deleted
