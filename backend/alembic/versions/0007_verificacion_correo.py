"""E-mail verification: delete every account, add verification columns and link tokens.

Revision ID: 0007_verificacion_correo
Revises: 0006_producto_normalizado

Every existing user is deleted first (they were test accounts, decision of
2026-11-11). ``ON DELETE CASCADE`` removes their sales, upload hashes and saved
predictions too; roles stay. ``usuarios`` gains ``correo_verificado`` and
``correo_pendiente``; ``tokens_usuario`` stores the SHA-256 of single-use link
tokens.

``downgrade`` drops the new table and columns. It cannot bring the deleted
accounts or their data back.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_verificacion_correo"
down_revision: str | None = "0006_producto_normalizado"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("DELETE FROM usuarios")

    op.add_column(
        "usuarios",
        sa.Column("correo_verificado", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("usuarios", sa.Column("correo_pendiente", sa.String(length=100), nullable=True))
    op.create_unique_constraint("uq_usuarios_correo_pendiente", "usuarios", ["correo_pendiente"])

    op.create_table(
        "tokens_usuario",
        sa.Column("id_token", sa.Integer(), nullable=False),
        sa.Column("id_usuario", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("usado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("tipo IN ('verificacion', 'restablecer')", name="ck_tokens_usuario_tipo"),
        sa.ForeignKeyConstraint(["id_usuario"], ["usuarios.id_usuario"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id_token"),
        sa.UniqueConstraint("token_hash", name="uq_tokens_usuario_hash"),
    )
    op.create_index("ix_tokens_usuario_id_usuario", "tokens_usuario", ["id_usuario"])


def downgrade() -> None:
    op.drop_index("ix_tokens_usuario_id_usuario", table_name="tokens_usuario")
    op.drop_table("tokens_usuario")
    op.drop_constraint("uq_usuarios_correo_pendiente", "usuarios", type_="unique")
    op.drop_column("usuarios", "correo_pendiente")
    op.drop_column("usuarios", "correo_verificado")
