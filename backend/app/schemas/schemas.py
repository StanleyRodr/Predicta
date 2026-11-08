"""Pydantic schemas for request validation and response serialization.

These schemas are the contract between the API and its clients. They
also drive the auto-generated OpenAPI documentation at ``/docs``.
"""

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

# Password policy: at least 8 chars, one uppercase, one lowercase, one digit.
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")
PASSWORD_HINT = "Minimo 8 caracteres, una mayuscula, una minuscula y un digito."


class UserBase(BaseModel):
    """Shared fields for any user representation."""

    nombre_usuario: str = Field(..., min_length=3, max_length=50)
    correo_electronico: EmailStr


class UserCreate(UserBase):
    """Payload accepted by ``POST /users/register``."""

    password: str

    @field_validator("password")
    @classmethod
    def _validate_password_strength(cls, value: str) -> str:
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(PASSWORD_HINT)
        return value


class UserResponse(UserBase):
    """User representation returned by the API (never includes the password)."""

    id_usuario: int
    id_rol: int | None
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Payload accepted by ``PUT /users/me`` for profile updates."""

    nombre_usuario: str | None = Field(None, min_length=3, max_length=50)
    correo_electronico: EmailStr | None = None


class SeriesPoint(BaseModel):
    """Totals of one observed month or day; periods without sales are absent."""

    periodo: str = Field(..., description="YYYY-MM con granularidad mes; YYYY-MM-DD con dia.")
    anio: int
    mes: int = Field(..., ge=1, le=12)
    dia: int | None = Field(None, description="Nulo con granularidad mes.")
    categoria: str | None = Field(None, description="Solo con por_categoria=true.")
    ingresos: float
    cantidad: float
    ventas_realizadas: int


class SeriesResponse(BaseModel):
    """Response of ``GET /analytics/stats/series``."""

    usuario: str
    granularidad: Literal["mes", "dia"]
    categoria: str | None = Field(
        None, description="Nombre de la categoría filtrada, tal como se muestra."
    )
    por_categoria: bool
    puntos: list[SeriesPoint]


class SaleRecord(BaseModel):
    """One sale as listed by ``GET /analytics/ventas``."""

    id: int
    producto: str
    monto: float
    categoria: str | None
    fecha: str = Field(..., description="YYYY-MM-DD HH:MM:SS.")


class SalesPageResponse(BaseModel):
    """Response of ``GET /analytics/ventas``."""

    usuario: str
    total_registros: int
    pagina_actual: int
    total_paginas: int
    registros: list[SaleRecord]
