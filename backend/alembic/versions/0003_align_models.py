"""Align the schema with the ORM models.

Revision ID: 0003_align_models
Revises: 0002_schema_predicciones

Databases created before Alembic were stamped at an earlier revision and differ
from what 0001 and 0002 build: other constraint names, missing indexes, and a
timestamp ``fecha_venta``. ``upgrade`` therefore tolerates both starting points
and leaves them identical. ``fecha_venta`` loses any time of day it held.

``downgrade`` returns to the schema 0001 and 0002 build. It does not restore
legacy differences, the time of day, or ``ventas_procesadas``.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_align_models"
down_revision: str | None = "0002_schema_predicciones"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _count(query: str) -> int:
    return op.get_bind().execute(sa.text(query)).scalar_one()


def _require_no_rows(query: str, problem: str) -> None:
    """Stop before a change that would otherwise discard or reject data."""
    rows = _count(query)
    if rows:
        raise RuntimeError(f"{problem}: {rows} rows. Resolve them and run this again.")


def _check_existing_data() -> None:
    _require_no_rows(
        "SELECT count(*) FROM predicciones WHERE id_usuario IS NULL",
        "predicciones without id_usuario",
    )
    _require_no_rows(
        "SELECT count(*) FROM ventas WHERE id_usuario IS NULL OR fecha_venta IS NULL",
        "ventas without id_usuario or fecha_venta",
    )
    if _count("SELECT count(*) FROM pg_tables WHERE tablename = 'ventas_procesadas'"):
        _require_no_rows(
            "SELECT count(*) FROM ventas_procesadas",
            "ventas_procesadas still holds data",
        )


def upgrade() -> None:
    _check_existing_data()

    # Legacy table with no remaining use; emptiness was checked above.
    op.execute("DROP TABLE IF EXISTS ventas_procesadas")

    # The primary key already indexes this column.
    op.execute("DROP INDEX IF EXISTS ix_roles_id_rol")

    # Unique indexes replace the separate constraints. They are created before
    # the constraints are dropped so uniqueness is enforced at every step.
    op.execute("CREATE INDEX IF NOT EXISTS ix_usuarios_id_usuario ON usuarios (id_usuario)")
    op.execute("DROP INDEX IF EXISTS ix_usuarios_nombre_usuario")
    op.create_index("ix_usuarios_nombre_usuario", "usuarios", ["nombre_usuario"], unique=True)
    op.execute("DROP INDEX IF EXISTS ix_usuarios_correo_electronico")
    op.create_index(
        "ix_usuarios_correo_electronico", "usuarios", ["correo_electronico"], unique=True
    )
    for constraint in (
        "uq_usuarios_nombre",
        "uq_usuarios_correo",
        "usuarios_nombre_usuario_key",
        "usuarios_correo_electronico_key",
    ):
        op.execute(f"ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS {constraint}")
    op.execute("ALTER TABLE usuarios ALTER COLUMN fecha_registro TYPE timestamptz")
    op.execute("ALTER TABLE usuarios ALTER COLUMN fecha_registro SET DEFAULT now()")
    op.execute("ALTER TABLE usuarios ALTER COLUMN fecha_registro SET NOT NULL")

    op.execute("ALTER TABLE ventas ALTER COLUMN producto TYPE varchar(150)")
    op.execute("ALTER TABLE ventas ALTER COLUMN categoria TYPE varchar(100)")
    op.execute("ALTER TABLE ventas ALTER COLUMN fecha_venta TYPE date USING fecha_venta::date")
    op.execute("ALTER TABLE ventas ALTER COLUMN fecha_venta SET NOT NULL")
    op.execute("ALTER TABLE ventas ALTER COLUMN id_usuario SET NOT NULL")
    op.execute("ALTER TABLE ventas DROP CONSTRAINT IF EXISTS ventas_id_usuario_fkey")
    op.create_foreign_key(
        "ventas_id_usuario_fkey",
        "ventas",
        "usuarios",
        ["id_usuario"],
        ["id_usuario"],
        ondelete="CASCADE",
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_ventas_id_venta ON ventas (id_venta)")
    # Every sales query filters by user first, so the composite index covers both.
    for index in (
        "ix_ventas_id_usuario",
        "ix_ventas_fecha_venta",
        "ix_ventas_usuario_fecha",
        "ix_ventas_categoria",
    ):
        op.execute(f"DROP INDEX IF EXISTS {index}")
    op.create_index("idx_ventas_usuario_fecha", "ventas", ["id_usuario", "fecha_venta"])
    op.create_index("idx_ventas_categoria", "ventas", ["categoria"])

    op.execute("ALTER TABLE predicciones ALTER COLUMN fecha_creacion TYPE timestamptz")
    op.execute("ALTER TABLE predicciones ALTER COLUMN fecha_creacion SET DEFAULT now()")
    op.execute("ALTER TABLE predicciones ALTER COLUMN fecha_creacion SET NOT NULL")
    op.execute("ALTER TABLE predicciones ALTER COLUMN id_usuario SET NOT NULL")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_predicciones_id_prediccion ON predicciones (id_prediccion)"
    )
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
