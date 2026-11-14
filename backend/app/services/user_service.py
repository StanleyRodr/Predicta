"""Business logic for user-related operations.

Keeps route handlers thin by isolating persistence and security
operations from HTTP concerns.
"""

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import security
from app.models import models
from app.schemas import schemas

# Seeded by migration 0001; looked up by name, never by its id.
DEFAULT_USER_ROLE_NAME = "Usuario"


class MissingRoleError(RuntimeError):
    """The default role is not in the ``roles`` table; run the migrations."""


def get_role_by_name(db: Session, name: str) -> models.Rol | None:
    """Return the role with the given name, or None if not found."""
    return db.query(models.Rol).filter(models.Rol.nombre_rol == name).first()


def get_user_by_email(db: Session, email: str) -> models.Usuario | None:
    """Return the user with the given email, or None if not found.

    The comparison ignores case and surrounding spaces, so ``Ana@x.com`` finds
    the account stored as ``ana@x.com``.
    """
    normalized = email.strip().lower()
    return (
        db.query(models.Usuario)
        .filter(func.lower(models.Usuario.correo_electronico) == normalized)
        .first()
    )


def get_user_by_username(db: Session, username: str) -> models.Usuario | None:
    """Return the user with the given username, or None if not found."""
    return (
        db.query(models.Usuario)
        .filter(models.Usuario.nombre_usuario == username)
        .first()
    )


def get_user_by_id(db: Session, user_id: int) -> models.Usuario | None:
    """Return the user with the given primary key, or None if not found."""
    return (
        db.query(models.Usuario).filter(models.Usuario.id_usuario == user_id).first()
    )


def create_user(db: Session, user: schemas.UserCreate) -> models.Usuario:
    """Persist a new user with a bcrypt-hashed password.

    New users get the ``Usuario`` role, found by name. Promote to
    ``Administrador`` directly in the database if needed.

    Raises:
        MissingRoleError: If the default role does not exist.
        sqlalchemy.exc.IntegrityError: If the email or username was taken
            concurrently; the session is rolled back first.
    """
    role = get_role_by_name(db, DEFAULT_USER_ROLE_NAME)
    if role is None:
        raise MissingRoleError(f"El rol '{DEFAULT_USER_ROLE_NAME}' no existe.")
    db_user = models.Usuario(
        nombre_usuario=user.nombre_usuario,
        correo_electronico=user.correo_electronico,
        contrasena_hash=security.get_password_hash(user.password),
        id_rol=role.id_rol,
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise
    db.refresh(db_user)
    return db_user


class InvalidCredentialsError(Exception):
    """Unknown e-mail or wrong password; the client cannot tell which."""


class AccountLockedError(Exception):
    """Too many wrong passwords; ``just_locked`` is True on the attempt that locked it."""

    def __init__(self, user: models.Usuario, *, just_locked: bool) -> None:
        super().__init__("Cuenta bloqueada")
        self.user = user
        self.just_locked = just_locked


class WrongPasswordError(Exception):
    """The current password given does not match."""


class SamePasswordError(Exception):
    """The new password equals the current one."""


def is_locked(user: models.Usuario) -> bool:
    return user.bloqueado_hasta is not None and security.as_utc(user.bloqueado_hasta) > security.utcnow()


def authenticate_user(db: Session, email: str, password: str) -> models.Usuario:
    """Return the user for valid credentials, counting wrong passwords.

    The OAuth2 form's ``username`` is the e-mail. Checks, in order: unknown
    e-mail (bcrypt still runs against a fixed hash, so timing reveals
    nothing), active lockout, wrong password (``MAX_FAILED_LOGINS`` in a row
    lock the account for ``LOCKOUT``). Success sets the counter to zero.

    Raises:
        InvalidCredentialsError: Unknown e-mail or wrong password.
        AccountLockedError: The account is locked, even if the password is right.
    """
    user = get_user_by_email(db, email=email)
    if user is None:
        security.verify_password(password, security.DUMMY_HASH)
        raise InvalidCredentialsError
    if is_locked(user):
        raise AccountLockedError(user, just_locked=False)
    if not security.verify_password(password, user.contrasena_hash):
        user.intentos_fallidos = (user.intentos_fallidos or 0) + 1
        if user.intentos_fallidos >= security.MAX_FAILED_LOGINS:
            user.intentos_fallidos = 0
            user.bloqueado_hasta = security.utcnow() + security.LOCKOUT
            db.commit()
            raise AccountLockedError(user, just_locked=True)
        db.commit()
        raise InvalidCredentialsError
    if user.intentos_fallidos or user.bloqueado_hasta is not None:
        user.intentos_fallidos = 0
        user.bloqueado_hasta = None
        db.commit()
    return user


def _set_password(user: models.Usuario, password: str) -> None:
    """Store the new hash and close every session issued before; the caller commits."""
    user.contrasena_hash = security.get_password_hash(password)
    user.version_token = (user.version_token or 0) + 1


def change_password(db: Session, user: models.Usuario, current: str, new: str) -> None:
    """Replace the password after checking the current one; older sessions stop working.

    Raises:
        WrongPasswordError: ``current`` does not match.
        SamePasswordError: ``new`` equals the current password.
    """
    if not security.verify_password(current, user.contrasena_hash):
        raise WrongPasswordError
    if security.verify_password(new, user.contrasena_hash):
        raise SamePasswordError
    _set_password(user, new)
    db.commit()
    db.refresh(user)


def reset_password(db: Session, user: models.Usuario, new: str) -> None:
    """Apply a reset link: new password, every session closed, lockout lifted.

    Opening a link sent to the address proves it belongs to the user, so the
    e-mail counts as verified too. The caller commits.
    """
    _set_password(user, new)
    user.intentos_fallidos = 0
    user.bloqueado_hasta = None
    user.correo_verificado = True


def email_in_use(db: Session, email: str, except_user_id: int | None = None) -> bool:
    """True if another account uses ``email`` as its address or as its pending one."""
    normalized = email.strip().lower()
    query = db.query(models.Usuario).filter(
        (func.lower(models.Usuario.correo_electronico) == normalized)
        | (func.lower(models.Usuario.correo_pendiente) == normalized)
    )
    if except_user_id is not None:
        query = query.filter(models.Usuario.id_usuario != except_user_id)
    return db.query(query.exists()).scalar() is True


def confirm_email(db: Session, user: models.Usuario) -> bool:
    """Apply a verification link to ``user``; the caller commits.

    A pending address replaces the current one. Returns False, and drops the
    pending address, when another account took it in the meantime.
    """
    if user.correo_pendiente:
        pending = user.correo_pendiente
        user.correo_pendiente = None
        if get_user_by_email(db, pending) is not None:
            return False
        user.correo_electronico = pending
    user.correo_verificado = True
    return True
