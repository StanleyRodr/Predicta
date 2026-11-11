"""Pydantic schemas for request validation and response serialization.

These schemas are the contract between the API and its clients. They
also drive the auto-generated OpenAPI documentation at ``/docs``.
"""

import re
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

# Field limits. frontend/src/lib/fieldLimits.ts repeats them and
# tests/test_field_limits_contract.py fails if the two files disagree.
MIN_USERNAME_LENGTH = 3
MAX_USERNAME_LENGTH = 50
MAX_EMAIL_LENGTH = 100
MIN_PASSWORD_LENGTH = 8
# bcrypt ignores everything past 72 bytes, so longer passwords are refused.
MAX_PASSWORD_BYTES = 72
MAX_CATEGORY_LENGTH = 100
MAX_PRODUCT_LENGTH = 150

# Password policy: at least 8 chars, one uppercase, one lowercase, one digit.
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$")
PASSWORD_HINT = "Minimo 8 caracteres, una mayuscula, una minuscula y un digito."  # noqa: S105 - user-facing message, not a secret
PASSWORD_TOO_LONG = "La contraseña no puede superar 72 bytes (las letras con tilde ocupan 2)."  # noqa: S105 - user-facing message, not a secret
# Letters (accented included), digits, space, dot, hyphen and underscore.
USERNAME_PATTERN = re.compile(r"^[\w .\-]+$")
USERNAME_HINT = (
    "El nombre de usuario solo admite letras, dígitos, espacios, punto, guion y guion bajo."
)
EMAIL_TOO_LONG = f"El correo electrónico no puede superar {MAX_EMAIL_LENGTH} caracteres."
CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f]")
# Same rule as a regex for Query/Path parameters.
NO_CONTROL_CHARACTERS = r"^[^\x00-\x1f\x7f]*$"
CONTROL_CHARACTERS_FOUND = "El texto contiene caracteres de control no permitidos."
PRODUCT_NEEDS_CATEGORY = "Para filtrar por producto, elige también su categoría."


def _strip(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _clean_email(value: object) -> object:
    """Trim and lowercase, so one mailbox maps to one account."""
    return value.strip().lower() if isinstance(value, str) else value


def _check_email_length(value: str) -> str:
    if len(value) > MAX_EMAIL_LENGTH:
        raise ValueError(EMAIL_TOO_LONG)
    return value


def _check_username(value: str) -> str:
    if not USERNAME_PATTERN.match(value):
        raise ValueError(USERNAME_HINT)
    return value


def _reject_control_characters(value: str | None) -> str | None:
    if value is not None and CONTROL_CHARACTERS.search(value):
        raise ValueError(CONTROL_CHARACTERS_FOUND)
    return value


Email = Annotated[EmailStr, BeforeValidator(_clean_email), AfterValidator(_check_email_length)]
Username = Annotated[
    str,
    BeforeValidator(_strip),
    Field(min_length=MIN_USERNAME_LENGTH, max_length=MAX_USERNAME_LENGTH),
    AfterValidator(_check_username),
]


def validate_new_password(value: str) -> str:
    """Apply the password policy; reused by every schema that sets a password."""
    if len(value.encode("utf-8")) > MAX_PASSWORD_BYTES:
        raise ValueError(PASSWORD_TOO_LONG)
    _reject_control_characters(value)
    if not PASSWORD_PATTERN.match(value):
        raise ValueError(PASSWORD_HINT)
    return value


class UserBase(BaseModel):
    """Shared fields for any user representation."""

    nombre_usuario: Username
    correo_electronico: Email


class UserCreate(UserBase):
    """Payload accepted by ``POST /users/register``."""

    password: str

    @field_validator("password")
    @classmethod
    def _validate_password_strength(cls, value: str) -> str:
        return validate_new_password(value)


class UserResponse(BaseModel):
    """User representation returned by the API (never includes the password)."""

    id_usuario: int
    nombre_usuario: str
    correo_electronico: str
    id_rol: int | None
    fecha_registro: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Payload accepted by ``PUT /users/me`` for profile updates."""

    nombre_usuario: Username | None = None
    correo_electronico: Email | None = None


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


# ---------------------------------------------------------------- statistics


class GlobalMetrics(BaseModel):
    total_ingresos: float
    cantidad_operaciones: int
    ticket_promedio: float
    venta_mas_alta: float


class GlobalStatsResponse(BaseModel):
    """Response of ``GET /analytics/stats``."""

    usuario: str
    metricas_globales: GlobalMetrics


class CategoryMetric(BaseModel):
    categoria: str
    ingresos_totales: float
    cantidad_ventas: int
    ticket_promedio: float


class CategoryStatsResponse(BaseModel):
    """Response of ``GET /analytics/stats/categories``."""

    usuario: str
    analisis_por_categoria: list[CategoryMetric]


class ProductListResponse(BaseModel):
    """Response of ``GET /analytics/productos``: one category's products by name."""

    usuario: str
    categoria: str
    productos: list[str]


class TemporalMetric(BaseModel):
    fecha: str = Field(..., description="YYYY-MM-DD.")
    ingresos: float
    ventas_realizadas: int


class TemporalStatsResponse(BaseModel):
    """Response of ``GET /analytics/stats/temporal``."""

    usuario: str
    evolucion_diaria: list[TemporalMetric]


# ---------------------------------------------------------------- forecasts


class DailyMetrics(BaseModel):
    r2: float | None
    mape: float | None
    mae: float | None = Field(None, description="Error absoluto medio, en dinero o unidades.")
    rmse: float | None


class Interval(BaseModel):
    inferior: float
    superior: float


class DailyIntervals(BaseModel):
    monto: Interval
    cantidad: Interval


class DailyMetricsByTarget(BaseModel):
    monto: DailyMetrics
    cantidad: DailyMetrics


class DailyForecastResponse(BaseModel):
    """Response of ``GET /analytics/predict``; it never stores anything."""

    usuario: str
    proxima_fecha: str = Field(..., description="YYYY-MM-DD.")
    monto_predicho: float
    cantidad_predicha: float
    monto_original_crudo: float
    intervalos_prediccion: DailyIntervals
    metricas: DailyMetricsByTarget
    mensaje: str


class MonthTotals(BaseModel):
    periodo: str = Field(..., description="YYYY-MM.")
    monto: float
    cantidad: float


class ProjectedValue(BaseModel):
    prediccion: float
    inferior: float = Field(..., description="Límite inferior del intervalo de predicción del 95 %.")
    superior: float = Field(..., description="Límite superior del intervalo de predicción del 95 %.")


class ProjectedMonth(BaseModel):
    periodo: str = Field(..., description="YYYY-MM.")
    extrapolacion: bool = Field(..., description="Verdadero desde el mes 7: extrapolación sin validar.")
    monto: ProjectedValue
    cantidad: ProjectedValue


class ValidationMetrics(BaseModel):
    """Errors on months the model did not see; null when they cannot be computed."""

    r2: float | None
    mape: float | None
    mae: float | None = Field(None, description="Error absoluto medio, en dinero o unidades.")
    rmse: float | None
    wape: float | None
    mase: float | None
    mejora_vs_referencia: float | None = Field(
        None, description="Reducción porcentual del WAPE frente al mejor modelo simple."
    )
    referencia: Literal["ultimo_valor", "mismo_mes_anio_anterior", "promedio_movil_3"] | None
    origenes: int = Field(..., description="Meses evaluados sin que el modelo los viera.")


class ValidationMetricsByTarget(BaseModel):
    monto: ValidationMetrics
    cantidad: ValidationMetrics


class MonthlyForecastResponse(BaseModel):
    """Response of ``GET /analytics/forecast``; it never stores anything."""

    usuario: str
    categoria: str | None = Field(None, description="Nulo: todas las categorías.")
    producto: str | None = Field(None, description="Nulo: todos los productos de la categoría.")
    modelo: Literal["tendencia", "tendencia_estacional"]
    horizonte_aplicado: int
    meses_observados: int
    advertencias: list[str] = Field(
        default_factory=list, description="Cada motivo que limita la proyección, uno por elemento."
    )
    advertencia: str | None = Field(None, description="Los mismos motivos unidos en un solo texto.")
    historial: list[MonthTotals]
    mes_parcial: MonthTotals | None = Field(
        None, description="Último mes, todavía incompleto: se proyecta y no entra en el ajuste."
    )
    proyeccion: list[ProjectedMonth]
    metricas: ValidationMetricsByTarget


class SavePredictionRequest(BaseModel):
    """Body of ``POST /analytics/predicciones``; the server recomputes the values."""

    categoria: str | None = Field(
        None, max_length=MAX_CATEGORY_LENGTH, description="Nulo: todas las categorías."
    )
    producto: str | None = Field(
        None, max_length=MAX_PRODUCT_LENGTH, description="Requiere categoria. Nulo: todos sus productos."
    )

    @field_validator("categoria", "producto")
    @classmethod
    def _no_control_characters(cls, value: str | None) -> str | None:
        return _reject_control_characters(value)

    @model_validator(mode="after")
    def product_needs_category(self) -> "SavePredictionRequest":
        if self.producto is not None and self.categoria is None:
            raise ValueError(PRODUCT_NEEDS_CATEGORY)
        return self


class SavedPoint(BaseModel):
    fecha_proyeccion: date
    extrapolacion: bool | None
    monto_proyectado: float | None
    monto_inferior: float | None
    monto_superior: float | None
    cantidad_proyectada: float
    cantidad_inferior: float | None
    cantidad_superior: float | None


class SavedBatch(BaseModel):
    """One saved projection: every projected month stored together."""

    lote: str
    tipo: Literal["mensual", "diaria"]
    categoria: str | None
    producto: str | None
    modelo: str | None
    horizonte: int | None
    r2_validacion: float | None
    wape_validacion: float | None
    fecha_creacion: datetime
    puntos: list[SavedPoint]


class SavedBatchPage(BaseModel):
    """Response of ``GET /analytics/predicciones``, newest batch first."""

    usuario: str
    total_lotes: int
    pagina_actual: int
    total_paginas: int
    lotes: list[SavedBatch]


# ---------------------------------------------------------------- ETL


class UploadRowError(BaseModel):
    fila: int
    error: str


ColumnRole = Literal["producto", "categoria", "monto", "precio_unitario", "cantidad", "fecha"]


class ColumnProposal(BaseModel):
    """The header proposed for one role, or the tied headers when none was chosen."""

    columna: str | None
    origen: Literal["exacto", "sinonimo"] | None
    candidatos: list[str]


class ColumnAnalysis(BaseModel):
    """Response of ``POST /etl/analizar-columnas``."""

    columnas: list[str]
    muestra: list[dict[str, str | None]]
    propuesta: dict[ColumnRole, ColumnProposal]
    faltantes: list[ColumnRole]


class UploadResponse(BaseModel):
    """Response of ``POST /etl/upload-ventas``."""

    message: str
    registros_leidos: int
    registros_cargados: int
    filas_rechazadas: int
    errores: list[UploadRowError]


class ClearHistoryResponse(BaseModel):
    """Response of ``DELETE /etl/clear-history``."""

    status: Literal["success"]
    message: str
    id_usuario: int | None = None
