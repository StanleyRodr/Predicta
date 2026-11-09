"""Normalize stored product names and record the product of saved forecasts.

Revision ID: 0006_producto_normalizado
Revises: 0005_predicciones_lotes

``ventas.producto`` is rewritten with ``normalize_product`` (single spaces,
each word capitalized, accents kept), the rule ingestion applies from now on, so product
filters can match by equality. ``predicciones.producto`` stores the product of
a saved projection; null means every product of its category.

``downgrade`` drops ``predicciones.producto``. It cannot restore the original
spelling of product names.
"""

import string
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_producto_normalizado"
down_revision: str | None = "0005_predicciones_lotes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _normalize_product(value: str) -> str:
    # Frozen copy of app.services.category_service.normalize_product.
    return string.capwords(value)


def upgrade() -> None:
    op.add_column("predicciones", sa.Column("producto", sa.String(length=150), nullable=True))

    bind = op.get_bind()
    ventas = sa.table("ventas", sa.column("producto", sa.String(150)))
    names = [row[0] for row in bind.execute(sa.select(ventas.c.producto).distinct())]
    for name in names:
        normalized = _normalize_product(name)
        if normalized != name:
            bind.execute(
                ventas.update().where(ventas.c.producto == name).values(producto=normalized)
            )


def downgrade() -> None:
    op.drop_column("predicciones", "producto")
