"""SQLAlchemy ORM models for the Predicta database.

All models inherit from :class:`app.core.database.Base`. Schema changes
must be made via Alembic migrations - never edit this file to alter
an existing table once migrations are in place.
"""

from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    CheckConstraint,
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


class Prediccion(Base):
    """Stored forecast produced by the ML pipeline."""

    __tablename__ = "predicciones"

    id_prediccion: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    id_usuario: Mapped[int] = mapped_column(
        Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), index=True
    )
    producto_referencia: Mapped[str] = mapped_column(String(150), nullable=False)
    cantidad_proyectada: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    monto_proyectado: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    fecha_proyeccion: Mapped[date] = mapped_column(Date, nullable=False)
    precision_estimada: Mapped[Decimal | None] = mapped_column(DECIMAL(5, 2))
    fecha_creacion: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
