"""ETL endpoints for ingesting sales data from external files.

Parsing and validation live in ``etl_service``. Every row is assigned to the
authenticated user.
"""

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import column_mapping, etl_service

router = APIRouter(prefix="/etl", tags=["ETL"])


def _file_extension(file: UploadFile) -> str:
    """Return the lowercase extension, or answer 400 for a missing or unsupported one."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo vacio.")
    extension = file.filename.rsplit(".", 1)[-1].lower()
    if extension not in etl_service.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no compatible. Usa: {', '.join(sorted(etl_service.ALLOWED_EXTENSIONS))}.",
        )
    return extension


def _parse_mapping(raw: str | None) -> dict[str, Any] | None:
    """Decode the ``mapeo`` form field; a missing field means exact column names."""
    if raw is None:
        return None
    try:
        mapping = json.loads(raw)
    except ValueError:
        mapping = None
    if not isinstance(mapping, dict):
        raise HTTPException(status_code=400, detail="El mapeo de columnas no es un JSON válido.")
    return mapping


def _http_error(exc: Exception, failure_detail: str) -> HTTPException:
    """Translate an ETL error into the response the user sees; unknown errors are logged."""
    if isinstance(exc, etl_service.FileTooLargeError):
        return HTTPException(status_code=413, detail=exc.detail)
    if isinstance(exc, etl_service.DuplicateUploadError):
        return HTTPException(
            status_code=409,
            detail="Este archivo ya fue cargado. Purga el historial si deseas cargarlo de nuevo.",
        )
    if isinstance(exc, etl_service.FileValidationError):
        return HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {exc.detail}")
    if isinstance(exc, (etl_service.UnreadableFileError, column_mapping.MappingValidationError)):
        return HTTPException(status_code=400, detail=exc.detail)
    logger.exception(failure_detail)
    return HTTPException(status_code=500, detail=failure_detail)


# Declared as plain functions so FastAPI runs this blocking work in its
# threadpool instead of stalling the event loop for every other request.
@router.post("/analizar-columnas", response_model=schemas.ColumnAnalysis)
def analizar_columnas(
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Propose which column of the file holds each field; nothing is stored."""
    extension = _file_extension(file)
    try:
        contents, _ = etl_service.read_limited(file.file)
        return etl_service.analyze_columns(extension, contents)
    except Exception as exc:
        raise _http_error(exc, "No se pudo analizar el archivo.") from exc


@router.post("/upload-ventas", response_model=schemas.UploadResponse)
def upload_ventas(
    file: UploadFile = File(...),
    mapeo: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Ingest sales rows from a CSV, XLSX, or SQL file.

    The file is detected by extension. ``mapeo`` is an optional JSON object
    ``{rol: columna}``; without it the file must use the exact column names.
    All rows are assigned to the authenticated user.
    """
    extension = _file_extension(file)
    mapping = _parse_mapping(mapeo)
    try:
        contents, file_hash = etl_service.read_limited(file.file)
        result: dict[str, Any] = etl_service.load_sales(
            db, current_user.id_usuario, extension, contents, file_hash, mapping
        )
    except Exception as exc:
        raise _http_error(exc, "No se pudo guardar el archivo completo.") from exc

    return {
        "message": f"Procesamiento exitoso: {result['registros_cargados']} registros cargados.",
        **result,
    }


@router.delete("/clear-history", response_model=schemas.ClearHistoryResponse)
def clear_history(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> dict:
    """Delete all sales rows owned by the authenticated user."""
    try:
        deleted = etl_service.clear_sales(db, current_user.id_usuario)
    except Exception as exc:
        logger.exception("Error al depurar el historial del usuario.")
        raise HTTPException(
            status_code=500,
            detail="No se pudo depurar el historial.",
        ) from exc
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
