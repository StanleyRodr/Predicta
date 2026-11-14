"""Session revocation and account lockout columns.

Revision ID: 0008_contrasenas_bloqueo
Revises: 0007_verificacion_correo

``usuarios.version_token`` travels in every JWT as ``ver``; changing or
resetting the password raises it and older tokens stop working.
``intentos_fallidos`` counts wrong passwords in a row and ``bloqueado_hasta``
holds the end of a lockout. Existing rows start at 0 and unlocked.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008_contrasenas_bloqueo"
down_revision: str | None = "0007_verificacion_correo"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("usuarios", sa.Column("version_token", sa.Integer(), server_default="0", nullable=False))
    op.add_column("usuarios", sa.Column("intentos_fallidos", sa.Integer(), server_default="0", nullable=False))
    op.add_column("usuarios", sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("usuarios", "bloqueado_hasta")
    op.drop_column("usuarios", "intentos_fallidos")
    op.drop_column("usuarios", "version_token")
