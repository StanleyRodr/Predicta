"""ETL endpoints for ingesting sales data from external files.

Parsing and validation live in ``etl_service``. Every row is assigned to the
authenticated user.
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import models
from app.services import etl_service

router = APIRouter(prefix="/etl", tags=["ETL"])


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
    if extension not in etl_service.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no compatible. Usa: {', '.join(sorted(etl_service.ALLOWED_EXTENSIONS))}.",
        )

    try:
        contents, file_hash = etl_service.read_limited(file.file)
        result: dict[str, Any] = etl_service.load_sales(
            db, current_user.id_usuario, extension, contents, file_hash
        )
    except etl_service.FileTooLargeError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except etl_service.DuplicateUploadError as exc:
        raise HTTPException(
            status_code=409,
            detail="Este archivo ya fue cargado. Purga el historial si deseas cargarlo de nuevo.",
        ) from exc
    except etl_service.FileValidationError as exc:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo: {exc}") from exc
    except etl_service.UnreadableFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error al guardar el archivo de ventas.")
        raise HTTPException(
            status_code=500,
            detail="No se pudo guardar el archivo completo.",
        ) from exc

    return {
        "message": f"Procesamiento exitoso: {result['registros_cargados']} registros cargados.",
        **result,
    }


@router.delete("/clear-history")
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
