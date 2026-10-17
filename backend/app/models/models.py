"""SQLAlchemy ORM models for the Predicta database.

All models inherit from :class:`app.core.database.Base`. Schema changes
must be made via Alembic migrations - never edit this file to alter
an existing table once migrations are in place.
"""

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
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

    rol: Mapped["Rol | None"] = relationship("Rol", lazy="joined")
    ventas: Mapped[list["Venta"]] = relationship(
        "Venta", back_populates="dueno", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Usuario {self.nombre_usuario}>"


class Archivo(Base):
    """Metadata for an uploaded data file processed by the ETL pipeline."""

    __tablename__ = "archivos"

    id_archivo: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE")
    )
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    ruta_servidor: Mapped[str] = mapped_column(Text, nullable=False)
    estado_proceso: Mapped[str] = mapped_column(String(20), default="Pendiente")
    filas_procesadas: Mapped[int] = mapped_column(Integer, default=0)
    fecha_subida: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class Venta(Base):
    """A single sales transaction ingested from a user-uploaded file.

    This is the unified sales table (the previous ``ventas_procesadas``
    table has been removed - the project uses a single, simpler schema).
    """

    __tablename__ = "ventas"

    id_venta: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), index=True
    )
    producto: Mapped[str] = mapped_column(String(150), nullable=False)
    monto: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(100))
    fecha_venta: Mapped[datetime] = mapped_column(
        Date, default=lambda: datetime.now(timezone.utc).date(), index=True
    )

    dueno: Mapped["Usuario"] = relationship("Usuario", back_populates="ventas")

    __table_args__ = (
        Index("idx_ventas_usuario_fecha", "id_usuario", "fecha_venta"),
        Index("idx_ventas_categoria", "categoria"),
    )

    def __repr__(self) -> str:
        return f"<Venta {self.id_venta} ${self.monto}>"


class Prediccion(Base):
    """Stored forecast produced by the ML pipeline."""

    __tablename__ = "predicciones"

    id_prediccion: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE")
    )
    producto_referencia: Mapped[str] = mapped_column(String(150), nullable=False)
    cantidad_proyectada: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    fecha_proyeccion: Mapped[datetime] = mapped_column(Date, nullable=False)
    precision_estimada: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
