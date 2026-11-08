"""Business logic for user-related operations.

Keeps route handlers thin by isolating persistence and security
operations from HTTP concerns.
"""

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
    """Return the user with the given email, or None if not found."""
    return db.query(models.Usuario).filter(models.Usuario.correo_electronico == email).first()


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


def authenticate_user(db: Session, email: str, password: str) -> models.Usuario | None:
    """Return the user if credentials are valid, otherwise None.

    Looks up by email (the OAuth2 form's ``username`` field is
    semantically an email in this project).
    """
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not security.verify_password(password, user.contrasena_hash):
        return None
    return user
