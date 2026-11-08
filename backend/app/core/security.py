"""Authentication and password hashing utilities.

Implements JWT token generation/validation and bcrypt password hashing
for the Predicta authentication system. Hashes are standard ``$2b$`` bcrypt
strings, so the ones created earlier through passlib keep validating.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# JWT configuration: the secret is required by ``Settings``.
SECRET_KEY: str = settings.secret_key
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.access_token_expire_minutes

# bcrypt: cost factor 12 is a sensible default for 2024+ hardware.
BCRYPT_ROUNDS = 12
# bcrypt reads at most 72 bytes; longer passwords are rejected by the schemas.
MAX_PASSWORD_BYTES = 72


def create_access_token(data: dict[str, Any]) -> str:
    """Build a signed JWT containing the given payload and an expiration claim.

    Args:
        data: Claims to embed in the token. Typically ``{"sub": "<user_id>"}``.

    Returns:
        The encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if ``plain_password`` matches the stored bcrypt hash.

    A password over 72 bytes or a malformed hash never matches.
    """
    password = plain_password.encode("utf-8")
    if len(password) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(password, hashed_password.encode("utf-8"))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash for the given plaintext password.

    Raises:
        ValueError: If the password is longer than 72 bytes in UTF-8.
    """
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError("La contraseña supera los 72 bytes.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("ascii")


__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "ALGORITHM",
    "MAX_PASSWORD_BYTES",
    "SECRET_KEY",
    "create_access_token",
    "get_password_hash",
    "verify_password",
]
