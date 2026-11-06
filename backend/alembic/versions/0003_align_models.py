"""Align indexes and nullability with the ORM models.

Revision ID: 0003_align_models
Revises: 0002_schema_predicciones
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_align_models"
down_revision: str | None = "0002_schema_predicciones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _require_prediction_owners() -> None:
    """Stop before NOT NULL so ownerless predictions are never deleted silently."""
    orphans = op.get_bind().execute(
        sa.text("SELECT count(*) FROM predicciones WHERE id_usuario IS NULL")
    ).scalar_one()
    if orphans:
        raise RuntimeError(
            f"predicciones has {orphans} rows without id_usuario; "
            "resolve them before running this migration."
        )


def upgrade() -> None:
    _require_prediction_owners()

    # The primary key already indexes this column.
    op.drop_index("ix_roles_id_rol", table_name="roles")

    # Unique indexes replace the separate constraints. They are created before
    # the constraints are dropped so uniqueness is enforced at every step.
    op.drop_index("ix_usuarios_nombre_usuario", table_name="usuarios")
    op.create_index("ix_usuarios_nombre_usuario", "usuarios", ["nombre_usuario"], unique=True)
    op.drop_constraint("uq_usuarios_nombre", "usuarios", type_="unique")
    op.drop_index("ix_usuarios_correo_electronico", table_name="usuarios")
    op.create_index(
        "ix_usuarios_correo_electronico", "usuarios", ["correo_electronico"], unique=True
    )
    op.drop_constraint("uq_usuarios_correo", "usuarios", type_="unique")

    op.execute("ALTER INDEX ix_ventas_usuario_fecha RENAME TO idx_ventas_usuario_fecha")
    op.execute("ALTER INDEX ix_ventas_categoria RENAME TO idx_ventas_categoria")
    # Every sales query filters by user first, so the composite index covers both.
    op.drop_index("ix_ventas_id_usuario", table_name="ventas")
    op.drop_index("ix_ventas_fecha_venta", table_name="ventas")

    op.alter_column("predicciones", "id_usuario", existing_type=sa.Integer(), nullable=False)
    op.create_index("ix_predicciones_id_usuario", "predicciones", ["id_usuario"])


def downgrade() -> None:
    op.drop_index("ix_predicciones_id_usuario", table_name="predicciones")
    op.alter_column("predicciones", "id_usuario", existing_type=sa.Integer(), nullable=True)

    op.create_index("ix_ventas_fecha_venta", "ventas", ["fecha_venta"])
    op.create_index("ix_ventas_id_usuario", "ventas", ["id_usuario"])
    op.execute("ALTER INDEX idx_ventas_categoria RENAME TO ix_ventas_categoria")
    op.execute("ALTER INDEX idx_ventas_usuario_fecha RENAME TO ix_ventas_usuario_fecha")

    op.create_unique_constraint("uq_usuarios_correo", "usuarios", ["correo_electronico"])
    op.drop_index("ix_usuarios_correo_electronico", table_name="usuarios")
    op.create_index("ix_usuarios_correo_electronico", "usuarios", ["correo_electronico"])
    op.create_unique_constraint("uq_usuarios_nombre", "usuarios", ["nombre_usuario"])
    op.drop_index("ix_usuarios_nombre_usuario", table_name="usuarios")
    op.create_index("ix_usuarios_nombre_usuario", "usuarios", ["nombre_usuario"])

    op.create_index("ix_roles_id_rol", "roles", ["id_rol"])
