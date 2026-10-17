"""ETL endpoints for ingesting sales data from external files.

Supported formats: CSV, XLSX, and SQL ``INSERT INTO`` statements.
Each endpoint enforces user-level data isolation.
"""

import csv
import io
import math
import re
from datetime import UTC, date, datetime
from typing import Any

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models

router = APIRouter(prefix="/etl", tags=["ETL"])

ALLOWED_EXTENSIONS = {"csv", "xlsx", "sql"}
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_REPORTED_ERRORS = 20
REQUIRED_COLUMNS = {"producto", "monto", "fecha"}


def _is_missing(value: object) -> bool:
    """Return whether a parsed cell is empty or represents a missing value."""
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _parse_amount(value: object) -> float:
    """Parse a finite amount or raise a validation error."""
    if _is_missing(value) or (isinstance(value, str) and not value.strip()):
        raise ValueError("el monto es obligatorio")

    normalized = str(value).strip().replace(",", ".")
    try:
        amount = float(normalized)
    except (TypeError, ValueError) as exc:
        raise ValueError("el monto no es numerico") from exc
    if not math.isfinite(amount):
        raise ValueError("el monto debe ser finito")
    return amount


def _parse_date(value: object, *, allow_missing: bool = False) -> date:
    """Parse a date or raise a validation error."""
    if _is_missing(value):
        if allow_missing:
            return datetime.now(UTC).date()
        raise ValueError("la fecha es obligatoria")

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError("la fecha no es valida")
    return parsed.date()


def _decode_text(contents: bytes) -> str:
    """Decode common CSV/SQL encodings without replacing invalid bytes."""
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return contents.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("el archivo no usa una codificacion compatible")


def _normalize_row(row: dict[Any, Any]) -> dict[str, Any]:
    """Normalize headers so files with surrounding spaces remain usable."""
    return {
        str(key).strip().lower().replace(" ", "_"): value for key, value in row.items()
    }


def _parse_csv(contents: bytes) -> list[dict[str, Any]]:
    """Parse comma, semicolon, or tab-delimited CSV content."""
    text = _decode_text(contents)
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    headers = {
        str(header).strip().lower().replace(" ", "_")
        for header in reader.fieldnames or []
    }
    missing = REQUIRED_COLUMNS - headers
    if missing:
        raise ValueError(f"faltan columnas requeridas: {', '.join(sorted(missing))}")
    return [_normalize_row(row) for row in reader]


def _parse_sql(contents: bytes) -> list[dict[str, Any]]:
    """Parse simple educational INSERT lines without executing SQL."""
    sql_text = _decode_text(contents)
    pattern = re.compile(r"VALUES\s*\((.*?)\);", re.IGNORECASE)
    rows = []
    for match in pattern.findall(sql_text):
        values = [value.strip().strip("'\"") for value in match.split(",")]
        if len(values) < 3:
            continue
        rows.append(
            {
                "producto": values[0],
                "monto": values[1],
                "categoria": values[2],
                "fecha": values[3] if len(values) > 3 else None,
            }
        )
    return rows


def _build_venta(
    row: dict[str, Any], user_id: int, *, allow_missing_date: bool = False
) -> models.Venta:
    """Validate and translate a raw row into a ``Venta`` ORM instance."""
    producto = row.get("producto")
    if _is_missing(producto) or not str(producto).strip():
        raise ValueError("el producto es obligatorio")

    return models.Venta(
        id_usuario=user_id,
        producto=str(producto).strip(),
        monto=_parse_amount(row.get("monto")),
        categoria=(str(row.get("categoria")).strip() if not _is_missing(row.get("categoria")) else "General"),
        fecha_venta=_parse_date(row.get("fecha"), allow_missing=allow_missing_date),
    )


@router.post("/upload-ventas")
async def upload_ventas(
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

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Archivo demasiado grande (max {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
        )

    try:
        if extension == "xlsx":
            rows = [
                _normalize_row(row)
                for row in pd.read_excel(io.BytesIO(contents)).to_dict(orient="records")
            ]
            headers = set(rows[0]) if rows else set()
            missing = REQUIRED_COLUMNS - headers
            if missing:
                raise ValueError(f"faltan columnas requeridas: {', '.join(sorted(missing))}")
            allow_missing_date = False
        elif extension == "csv":
            rows = _parse_csv(contents)
            allow_missing_date = False
        else:
            rows = _parse_sql(contents)
            allow_missing_date = True
    except (UnicodeDecodeError, ValueError, OSError) as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {exc}") from exc

    errores: list[dict[str, Any]] = []
    ventas_creadas = 0
    for row_number, row in enumerate(rows, start=2):
        try:
            db.add(
                _build_venta(
                    row,
                    current_user.id_usuario,
                    allow_missing_date=allow_missing_date,
                )
            )
            ventas_creadas += 1
        except (TypeError, ValueError) as exc:
            if len(errores) < MAX_REPORTED_ERRORS:
                errores.append({"fila": row_number, "error": str(exc)})

    try:
        db.commit()
    except Exception as exc:
        db.rollback()
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
