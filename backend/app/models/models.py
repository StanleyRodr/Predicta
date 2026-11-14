"""SQLAlchemy ORM models for the Predicta database.

All models inherit from :class:`app.core.database.Base`. Schema changes
must be made via Alembic migrations - never edit this file to alter
an existing table once migrations are in place.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Rol(Base):
    """User role. Drives authorization via ``require_role`` decorator."""

    __tablename__ = "roles"

    id_rol: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre_rol: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Rol {self.nombre_rol}>"


class Usuario(Base):
    """Application user. Owns sales records and uploaded files."""

    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre_usuario: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    correo_electronico: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    contrasena_hash: Mapped[str] = mapped_column(Text, nullable=False)
    id_rol: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("roles.id_rol", ondelete="SET NULL")
    )
    fecha_registro: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # Login is refused until a link sent to the address has been opened.
    correo_verificado: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    # A requested new address; it replaces correo_electronico once confirmed.
    correo_pendiente: Mapped[str | None] = mapped_column(String(100))
    # Travels in every JWT as "ver"; raising it closes every open session.
    version_token: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    # Wrong passwords in a row; MAX_FAILED_LOGINS locks the account until bloqueado_hasta.
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    rol: Mapped["Rol | None"] = relationship("Rol", lazy="joined")
    ventas: Mapped[list["Venta"]] = relationship(
        "Venta", back_populates="dueno", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("correo_pendiente", name="uq_usuarios_correo_pendiente"),
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.nombre_usuario}>"


class TokenUsuario(Base):
    """Single-use link token; only its SHA-256 is stored.

    ``tipo`` is ``verificacion`` (confirm an e-mail address) or ``restablecer``
    (password reset, task 043). Managed only through ``token_service``.
    """

    __tablename__ = "tokens_usuario"

    id_token: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_tokens_usuario_hash"),
        CheckConstraint("tipo IN ('verificacion', 'restablecer')", name="ck_tokens_usuario_tipo"),
    )


class Venta(Base):
    """A single sales transaction ingested from a user-uploaded file.

    This is the unified sales table (the previous ``ventas_procesadas``
    table has been removed - the project uses a single, simpler schema).
    """

    __tablename__ = "ventas"

    id_venta: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE")
    )
    producto: Mapped[str] = mapped_column(String(150), nullable=False)
    monto: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    cantidad: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=1
    )
    categoria: Mapped[str | None] = mapped_column(String(100))
    fecha_venta: Mapped[date] = mapped_column(
        Date, default=lambda: datetime.now(UTC).date()
    )

    dueno: Mapped["Usuario"] = relationship("Usuario", back_populates="ventas")

    __table_args__ = (
        CheckConstraint("cantidad >= 0", name="ck_ventas_cantidad_no_negativa"),
        Index("idx_ventas_usuario_fecha", "id_usuario", "fecha_venta"),
        Index("idx_ventas_categoria", "categoria"),
    )

    def __repr__(self) -> str:
        return f"<Venta {self.id_venta} ${self.monto}>"


class CargaArchivo(Base):
    """Fingerprint of a loaded file, used to reject identical re-uploads."""

    __tablename__ = "cargas_archivo"

    id_carga: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE")
    )
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    fecha_carga: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("id_usuario", "sha256", name="uq_cargas_usuario_sha256"),
    )


class Prediccion(Base):
    """One projected period of a forecast the user chose to save.

    Rows saved together share ``lote``. ``tipo`` is ``mensual`` for saved monthly
    projections and ``diaria`` for next-day forecasts stored before saving became
    explicit. A null ``categoria`` means the projection covers every category; a
    null ``producto`` means it covers every product of ``categoria``.
    """

    __tablename__ = "predicciones"

    id_prediccion: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), index=True
    )
    lote: Mapped[str] = mapped_column(String(40), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False, server_default="mensual")
    categoria: Mapped[str | None] = mapped_column(String(100))
    producto: Mapped[str | None] = mapped_column(String(150))
    producto_referencia: Mapped[str] = mapped_column(String(150), nullable=False)
    fecha_proyeccion: Mapped[date] = mapped_column(Date, nullable=False)
    monto_proyectado: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2))
    monto_inferior: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2))
    monto_superior: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2))
    cantidad_proyectada: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    cantidad_inferior: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2))
    cantidad_superior: Mapped[Decimal | None] = mapped_column(DECIMAL(12, 2))
    modelo: Mapped[str | None] = mapped_column(String(30))
    horizonte: Mapped[int | None] = mapped_column(Integer)
    extrapolacion: Mapped[bool | None] = mapped_column(Boolean)
    # Out-of-sample R² can be far below zero, so it is not a bounded decimal.
    r2_validacion: Mapped[float | None] = mapped_column(Float)
    wape_validacion: Mapped[float | None] = mapped_column(Float)
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("tipo IN ('mensual', 'diaria')", name="ck_predicciones_tipo"),
        Index("idx_predicciones_usuario_lote", "id_usuario", "lote"),
    )
