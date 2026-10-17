"""Pydantic schemas for request validation and response serialization.

These schemas are the contract between the API and its clients. They
also drive the auto-generated OpenAPI documentation at ``/docs``.
"""

import re
from datetime import datetime

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
