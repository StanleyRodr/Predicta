"""Single-use link tokens (e-mail verification, password reset).

The raw token goes only into the e-mail; the database keeps its SHA-256. A new
token of one type replaces the user's earlier unused ones of that type. A
consumed, expired or unknown token gives ``None`` without saying which.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from app.core import security
from app.models import models

VERIFICATION = "verificacion"
PASSWORD_RESET = "restablecer"  # noqa: S105 - token type name, not a secret
TOKEN_TYPES = {VERIFICATION, PASSWORD_RESET}

VERIFICATION_LIFETIME = timedelta(hours=24)
TOKEN_BYTES = 32
# token_urlsafe(32) gives 43 characters; anything far longer is not ours.
MAX_TOKEN_LENGTH = 128


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now() -> datetime:
    return security.utcnow()


def issue(db: Session, user_id: int, tipo: str, lifetime: timedelta) -> str:
    """Create a token for ``user_id`` and return it in clear; the caller commits.

    Earlier unused tokens of the same type and user stop working.
    """
    if tipo not in TOKEN_TYPES:
        raise ValueError(f"Tipo de token desconocido: {tipo}")
    db.execute(
        delete(models.TokenUsuario).where(
            models.TokenUsuario.id_usuario == user_id,
            models.TokenUsuario.tipo == tipo,
            models.TokenUsuario.usado_en.is_(None),
        )
    )
    raw = secrets.token_urlsafe(TOKEN_BYTES)
    db.add(
        models.TokenUsuario(
            id_usuario=user_id,
            tipo=tipo,
            token_hash=hash_token(raw),
            expira_en=_now() + lifetime,
        )
    )
    db.flush()
    return raw


def consume(db: Session, raw: str, tipo: str) -> models.TokenUsuario | None:
    """Mark a valid token as used and return it; the caller commits.

    Returns ``None`` for an unknown, expired, already used or other-type token.
    The update only matches an unused row, so two requests cannot both use it.
    """
    if not raw or len(raw) > MAX_TOKEN_LENGTH:
        return None
    token = (
        db.query(models.TokenUsuario)
        .filter(models.TokenUsuario.token_hash == hash_token(raw), models.TokenUsuario.tipo == tipo)
        .first()
    )
    now = _now()
    if token is None or token.usado_en is not None or security.as_utc(token.expira_en) <= now:
        return None
    result = db.execute(
        update(models.TokenUsuario)
        .where(models.TokenUsuario.id_token == token.id_token, models.TokenUsuario.usado_en.is_(None))
        .values(usado_en=now)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        return None
    db.refresh(token)
    return token
