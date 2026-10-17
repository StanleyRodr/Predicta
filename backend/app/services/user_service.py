"""Business logic for user-related operations.

Keeps route handlers thin by isolating persistence and security
operations from HTTP concerns.
"""

from sqlalchemy.orm import Session

from app.core import security
from app.models import models
from app.schemas import schemas

DEFAULT_USER_ROLE_ID = 2  # "Usuario" (Administrador is id=1)


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

    New users are assigned the default ``Usuario`` role (id=2).
    Promote to ``Administrador`` directly in the database if needed.
    """
    db_user = models.Usuario(
        nombre_usuario=user.nombre_usuario,
        correo_electronico=user.correo_electronico,
        contrasena_hash=security.get_password_hash(user.password),
        id_rol=DEFAULT_USER_ROLE_ID,
    )
    db.add(db_user)
    db.commit()
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
