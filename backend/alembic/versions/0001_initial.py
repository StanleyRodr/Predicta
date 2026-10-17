"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2025-07-28 00:00:00.000000

Creates the base Predicta schema:
- roles, usuarios, ventas, archivos, predicciones
- indexes for common query patterns
- seed data for the two base roles
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Roles
    op.create_table(
        "roles",
        sa.Column("id_rol", sa.Integer(), nullable=False),
        sa.Column("nombre_rol", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id_rol"),
        sa.UniqueConstraint("nombre_rol", name="uq_roles_nombre_rol"),
    )
    op.create_index("ix_roles_id_rol", "roles", ["id_rol"])

    # Users
    op.create_table(
        "usuarios",
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("nombre_usuario", sa.String(length=50), nullable=False),
        sa.Column("correo_electronico", sa.String(length=100), nullable=False),
        sa.Column("contrasena_hash", sa.Text(), nullable=False),
        sa.Column("id_rol", sa.Integer(), nullable=True),
        sa.Column("fecha_registro", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id_rol"], ["roles.id_rol"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id_usuario"),
        sa.UniqueConstraint("correo_electronico", name="uq_usuarios_correo"),
        sa.UniqueConstraint("nombre_usuario", name="uq_usuarios_nombre"),
    )
    op.create_index("ix_usuarios_id_usuario", "usuarios", ["id_usuario"])
    op.create_index("ix_usuarios_nombre_usuario", "usuarios", ["nombre_usuario"])
    op.create_index("ix_usuarios_correo_electronico", "usuarios", ["correo_electronico"])

    # Sales (unified single table - replaces the previous ventas_procesadas)
    op.create_table(
        "ventas",
        sa.Column("id_venta", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("producto", sa.String(length=150), nullable=False),
        sa.Column("monto", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("categoria", sa.String(length=100), nullable=True),
        sa.Column("fecha_venta", sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_venta"),
    )
    op.create_index("ix_ventas_id_venta", "ventas", ["id_venta"])
    op.create_index("ix_ventas_id_usuario", "ventas", ["id_usuario"])
    op.create_index("ix_ventas_fecha_venta", "ventas", ["fecha_venta"])
    op.create_index("ix_ventas_categoria", "ventas", ["categoria"])
    op.create_index("ix_ventas_usuario_fecha", "ventas", ["id_usuario", "fecha_venta"])

    # Files (ETL metadata)
    op.create_table(
        "archivos",
        sa.Column("id_archivo", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=True),
        sa.Column("nombre_original", sa.String(length=255), nullable=False),
        sa.Column("ruta_servidor", sa.Text(), nullable=False),
        sa.Column("estado_proceso", sa.String(length=20), server_default="Pendiente", nullable=False),
        sa.Column("filas_procesadas", sa.Integer(), nullable=True),
        sa.Column("fecha_subida", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_archivo"),
    )
    op.create_index("ix_archivos_id_archivo", "archivos", ["id_archivo"])

    # Predictions (history of forecasts produced)
    op.create_table(
        "predicciones",
        sa.Column("id_prediccion", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=True),
        sa.Column("producto_referencia", sa.String(length=150), nullable=False),
        sa.Column("cantidad_proyectada", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("fecha_proyeccion", sa.Date(), nullable=False),
        sa.Column("precision_estimada", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_prediccion"),
    )
    op.create_index("ix_predicciones_id_prediccion", "predicciones", ["id_prediccion"])

    # Seed: base roles
    op.execute(
        "INSERT INTO roles (nombre_rol) VALUES ('Administrador'), ('Usuario') "
        "ON CONFLICT (nombre_rol) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_index("ix_predicciones_id_prediccion", table_name="predicciones")
    op.drop_table("predicciones")
    op.drop_index("ix_archivos_id_archivo", table_name="archivos")
    op.drop_table("archivos")
    op.drop_index("ix_ventas_usuario_fecha", table_name="ventas")
    op.drop_index("ix_ventas_categoria", table_name="ventas")
    op.drop_index("ix_ventas_fecha_venta", table_name="ventas")
    op.drop_index("ix_ventas_id_usuario", table_name="ventas")
    op.drop_index("ix_ventas_id_venta", table_name="ventas")
    op.drop_table("ventas")
    op.drop_index("ix_usuarios_correo_electronico", table_name="usuarios")
    op.drop_index("ix_usuarios_nombre_usuario", table_name="usuarios")
    op.drop_index("ix_usuarios_id_usuario", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_index("ix_roles_id_rol", table_name="roles")
    op.drop_table("roles")
