"""Shared FastAPI dependencies (auth guards, role checks)."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY
from app.models import models
from app.services import user_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudieron validar las credenciales.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.Usuario:
    """Resolve the ``Usuario`` from the ``Authorization: Bearer`` token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise CREDENTIALS_EXCEPTION
        user_id = int(sub)
    except (JWTError, ValueError):
        raise CREDENTIALS_EXCEPTION from None

    user = user_service.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user


def require_role(role_name: str) -> Callable[..., models.Usuario]:
    """Return a dependency that enforces the given role on the current user.

    Usage:
        @router.delete(
            "/admin/users/{id}",
            dependencies=[Depends(require_role("Administrador"))],
        )
    """

    def _check(current_user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
        user_role_name = current_user.rol.nombre_rol if current_user.rol else None
        if user_role_name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Esta operacion requiere el rol '{role_name}'.",
            )
        return current_user

    return _check
