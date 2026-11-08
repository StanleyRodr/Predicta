"""Store saved forecasts as batches of projected periods.

Revision ID: 0005_predicciones_lotes
Revises: 0004_cargas_archivo

Existing rows are next-day forecasts that ``/predict`` stored on every request.
They are kept as ``tipo = 'diaria'``, each in its own batch ``legado-<id>``.
``precision_estimada`` becomes ``r2_validacion`` as a float, because an
out-of-sample R² can be far below the -999.99 a DECIMAL(5, 2) holds.

``downgrade`` drops the batch columns and narrows the types back; it fails if a
saved value no longer fits DECIMAL(10, 2) or an R² falls outside DECIMAL(5, 2).
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0005_predicciones_lotes"
down_revision: str | None = "0004_cargas_archivo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_DECIMALS = ("monto_inferior", "monto_superior", "cantidad_inferior", "cantidad_superior")


def upgrade() -> None:
    op.add_column("predicciones", sa.Column("lote", sa.String(length=40), nullable=True))
    op.add_column(
        "predicciones",
        sa.Column("tipo", sa.String(length=10), server_default="mensual", nullable=False),
    )
    op.add_column("predicciones", sa.Column("categoria", sa.String(length=100), nullable=True))
    for column in NEW_DECIMALS:
        op.add_column("predicciones", sa.Column(column, sa.DECIMAL(12, 2), nullable=True))
    op.add_column("predicciones", sa.Column("modelo", sa.String(length=30), nullable=True))
    op.add_column("predicciones", sa.Column("horizonte", sa.Integer(), nullable=True))
    op.add_column("predicciones", sa.Column("extrapolacion", sa.Boolean(), nullable=True))
    op.add_column("predicciones", sa.Column("wape_validacion", sa.Float(), nullable=True))

    # Every row stored so far is a next-day forecast saved by a GET request.
    op.execute(
        "UPDATE predicciones SET tipo = 'diaria', "
        "lote = 'legado-' || CAST(id_prediccion AS VARCHAR)"
    )
    op.alter_column("predicciones", "lote", existing_type=sa.String(length=40), nullable=False)

    op.alter_column(
        "predicciones",
        "precision_estimada",
        new_column_name="r2_validacion",
        type_=sa.Float(),
        existing_type=sa.DECIMAL(5, 2),
        existing_nullable=True,
    )
    for column, nullable in (("monto_proyectado", True), ("cantidad_proyectada", False)):
        op.alter_column(
            "predicciones",
            column,
            type_=sa.DECIMAL(12, 2),
            existing_type=sa.DECIMAL(10, 2),
            existing_nullable=nullable,
        )
    op.create_check_constraint("ck_predicciones_tipo", "predicciones", "tipo IN ('mensual', 'diaria')")
    op.create_index("idx_predicciones_usuario_lote", "predicciones", ["id_usuario", "lote"])


def downgrade() -> None:
    op.drop_index("idx_predicciones_usuario_lote", table_name="predicciones")
    op.drop_constraint("ck_predicciones_tipo", "predicciones", type_="check")
    for column, nullable in (("monto_proyectado", True), ("cantidad_proyectada", False)):
        op.alter_column(
            "predicciones",
            column,
            type_=sa.DECIMAL(10, 2),
            existing_type=sa.DECIMAL(12, 2),
            existing_nullable=nullable,
        )
    op.alter_column(
        "predicciones",
        "r2_validacion",
        new_column_name="precision_estimada",
        type_=sa.DECIMAL(5, 2),
        existing_type=sa.Float(),
        existing_nullable=True,
    )
    for column in ("wape_validacion", "extrapolacion", "horizonte", "modelo", *NEW_DECIMALS, "categoria", "tipo", "lote"):
        op.drop_column("predicciones", column)
