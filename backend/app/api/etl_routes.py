"""ETL endpoints for ingesting sales data from external files.

Supported formats: CSV, XLSX, and SQL ``INSERT INTO`` statements.
Each endpoint enforces user-level data isolation.
"""

import csv
import io
import re
from datetime import UTC, datetime

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


def _coerce_amount(value: object) -> float:
    """Convert a raw cell value to a float, defaulting to 0.0 on failure."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.0


def _coerce_date(value: object) -> datetime.date:
    """Parse a raw cell into a date; fall back to today on failure."""
    try:
        return pd.to_datetime(value).date()
    except (TypeError, ValueError):
        return datetime.now(UTC).date()


def _build_venta(row: dict, user_id: int) -> models.Venta:
    """Translate a raw row dict into a ``Venta`` ORM instance."""
    return models.Venta(
        id_usuario=user_id,
        producto=str(row.get("producto", "Sin Nombre")).strip(),
        monto=_coerce_amount(row.get("monto", 0)),
        categoria=str(row.get("categoria", "General")).capitalize(),
        fecha_venta=_coerce_date(row.get("fecha")),
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

    ventas_creadas = 0

    if extension == "xlsx":
        df = pd.read_excel(io.BytesIO(contents))
        for _, row in df.iterrows():
            db.add(_build_venta(row.to_dict(), current_user.id_usuario))
            ventas_creadas += 1

    elif extension == "csv":
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))
        for row in reader:
            db.add(_build_venta(row, current_user.id_usuario))
            ventas_creadas += 1

    else:  # sql
        # Best-effort parser for simple "INSERT INTO tabla VALUES (...);" lines.
        # Intended for the educational seed files, not for arbitrary SQL dumps.
        sql_text = contents.decode("utf-8")
        pattern = re.compile(r"VALUES\s*\((.*?)\);", re.IGNORECASE)
        for match in pattern.findall(sql_text):
            values = [v.strip().strip("'\"") for v in match.split(",")]
            if len(values) < 3:
                continue
            row = {"producto": values[0], "monto": values[1], "categoria": values[2]}
            db.add(_build_venta(row, current_user.id_usuario))
            ventas_creadas += 1

    db.commit()
    return {"message": f"Procesamiento exitoso: {ventas_creadas} registros cargados."}


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
