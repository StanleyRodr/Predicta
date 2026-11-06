"""Track loaded file hashes to reject identical re-uploads.

Revision ID: 0004_cargas_archivo
Revises: 0003_align_models
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_cargas_archivo"
down_revision: str | None = "0003_align_models"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cargas_archivo",
        sa.Column("id_carga", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "fecha_carga",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_carga"),
        sa.UniqueConstraint("id_usuario", "sha256", name="uq_cargas_usuario_sha256"),
    )


def downgrade() -> None:
    op.drop_table("cargas_archivo")
