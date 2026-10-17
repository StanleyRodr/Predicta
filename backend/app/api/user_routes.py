"""Authentication and profile endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import security
from app.core.database import get_db
from app.core.rate_limit import limiter
from app.models import models
from app.schemas import schemas
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)) -> models.Usuario:
    """Create a new user account."""
    if user_service.get_user_by_email(db, email=user.correo_electronico):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electronico ya se encuentra registrado.",
        )
    if user_service.get_user_by_username(db, username=user.nombre_usuario):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya se encuentra registrado.",
        )
    return user_service.create_user(db=db, user=user)


@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate a user and return a JWT access token.

    Limited to 5 attempts per minute per IP to mitigate brute force.
    """
    user = user_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales invalidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = security.create_access_token(data={"sub": str(user.id_usuario)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def read_my_profile(current_user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
    """Return the authenticated user's profile."""
    return current_user


@router.put("/me", response_model=schemas.UserResponse)
def update_my_profile(
    user_data: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> models.Usuario:
    """Update the authenticated user's username and/or email."""
    if user_data.correo_electronico and user_data.correo_electronico != current_user.correo_electronico:
        if user_service.get_user_by_email(db, email=user_data.correo_electronico):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo correo electronico ya esta en uso.",
            )
        current_user.correo_electronico = user_data.correo_electronico

    if user_data.nombre_usuario and user_data.nombre_usuario != current_user.nombre_usuario:
        if user_service.get_user_by_username(db, username=user_data.nombre_usuario):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo nombre de usuario ya esta en uso.",
            )
        current_user.nombre_usuario = user_data.nombre_usuario

    db.commit()
    db.refresh(current_user)
    return current_user
