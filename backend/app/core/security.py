"""Authentication and password hashing utilities.

Implements JWT token generation/validation and bcrypt password hashing
for the Predicta authentication system. Hashes are standard ``$2b$`` bcrypt
strings, so the ones created earlier through passlib keep validating.
"""

import secrets
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

# Lockout and password-reset timing (task 043).
MAX_FAILED_LOGINS = 10
LOCKOUT_MINUTES = 15
RESET_TOKEN_MINUTES = 30
LOCKOUT = timedelta(minutes=LOCKOUT_MINUTES)
RESET_TOKEN_LIFETIME = timedelta(minutes=RESET_TOKEN_MINUTES)


def utcnow() -> datetime:
    """Current time in UTC; the one clock tests replace."""
    return datetime.now(UTC)


def as_utc(moment: datetime) -> datetime:
    """SQLite returns naive datetimes; they were stored in UTC."""
    return moment if moment.tzinfo else moment.replace(tzinfo=UTC)


def create_access_token(data: dict[str, Any]) -> str:
    """Build a signed JWT containing the given payload and an expiration claim.

    Args:
        data: Claims to embed in the token. Typically ``{"sub": "<user_id>"}``.

    Returns:
        The encoded JWT string.
    """
    to_encode = data.copy()
    expire = utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
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


def token_for(user_id: int, version: int) -> str:
    """Access token whose "ver" must match the user's version_token to be accepted."""
    return create_access_token({"sub": str(user_id), "ver": version})


# Checked against when the e-mail has no account, so a 401 takes the same
# bcrypt time whether the account exists or not (audit finding S-22).
DUMMY_HASH = get_password_hash(secrets.token_urlsafe(16))


__all__ = [
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "ALGORITHM",
    "DUMMY_HASH",
    "LOCKOUT",
    "LOCKOUT_MINUTES",
    "MAX_FAILED_LOGINS",
    "MAX_PASSWORD_BYTES",
    "RESET_TOKEN_LIFETIME",
    "RESET_TOKEN_MINUTES",
    "SECRET_KEY",
    "as_utc",
    "create_access_token",
    "get_password_hash",
    "token_for",
    "utcnow",
    "verify_password",
]
