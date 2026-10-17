"""Add sale quantities, prediction amounts, and remove unused file metadata.

Revision ID: 0002_schema_cantidad_predicciones
Revises: 0001_initial
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_schema_cantidad_predicciones"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("ventas") as batch_op:
        batch_op.add_column(
            sa.Column(
                "cantidad",
                sa.Numeric(precision=10, scale=2),
                nullable=False,
                server_default=sa.text("1"),
            )
        )
        batch_op.create_check_constraint(
            "ck_ventas_cantidad_no_negativa",
            "cantidad >= 0",
        )
        batch_op.alter_column("cantidad", server_default=None)

    # Nullable preserves legacy prediction rows that predate amount storage.
    with op.batch_alter_table("predicciones") as batch_op:
        batch_op.add_column(
            sa.Column("monto_proyectado", sa.Numeric(precision=10, scale=2), nullable=True)
        )

    op.drop_index("ix_archivos_id_archivo", table_name="archivos")
    op.drop_table("archivos")


def downgrade() -> None:
    op.create_table(
        "archivos",
        sa.Column("id_archivo", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("nombre_original", sa.String(length=255), nullable=False),
        sa.Column("ruta_servidor", sa.Text(), nullable=False),
        sa.Column("estado_proceso", sa.String(length=20), server_default="Pendiente", nullable=False),
        sa.Column("filas_procesadas", sa.Integer(), server_default="0", nullable=True),
        sa.Column("fecha_subida", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_archivo"),
    )
    op.create_index("ix_archivos_id_archivo", "archivos", ["id_archivo"])
    with op.batch_alter_table("predicciones") as batch_op:
        batch_op.drop_column("monto_proyectado")
    with op.batch_alter_table("ventas") as batch_op:
        batch_op.drop_constraint("ck_ventas_cantidad_no_negativa", type_="check")
        batch_op.drop_column("cantidad")
