"""Authentication, e-mail verification and profile endpoints."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core import security
from app.core.database import get_db
from app.core.rate_limit import (
    CONFIRM_LINK_LIMIT,
    LOGIN_LIMIT,
    REGISTER_LIMIT,
    RESEND_VERIFICATION_LIMIT,
    limiter,
)
from app.models import models
from app.schemas import schemas
from app.services import email_service, token_service, user_service

router = APIRouter(prefix="/users", tags=["Users"])

# Two requests can pass the duplicate checks at once; the unique constraints
# catch the second one, which gets the same 400 as a sequential duplicate.
DUPLICATE_ACCOUNT = "El correo electronico o el nombre de usuario ya se encuentra registrado."
EMAIL_NOT_VERIFIED = "Verifica tu correo antes de iniciar sesión."
# Same answer whether the account exists, is verified or not: it reveals nothing.
RESEND_ANSWER = "Si el correo tiene una cuenta sin verificar, te enviamos un enlace nuevo."
INVALID_LINK = "El enlace no es válido o ya venció."
EMAIL_CONFIRMED = "Correo confirmado. Ya puedes iniciar sesión."
PASSWORD_REQUIRED_FOR_EMAIL = "Escribe tu contraseña actual para cambiar el correo."  # noqa: S105 - user-facing message, not a secret
WRONG_CURRENT_PASSWORD = "La contraseña actual no es correcta."  # noqa: S105 - user-facing message, not a secret
EMAIL_TAKEN = "El nuevo correo electronico ya esta en uso."
VERIFICATION_HOURS = int(token_service.VERIFICATION_LIFETIME.total_seconds() // 3600)


def _send_verification(
    tasks: BackgroundTasks, db: Session, user: models.Usuario, to: str, *, change: bool
) -> None:
    """Issue a verification token for ``user`` and queue its link to ``to``; the caller commits."""
    token = token_service.issue(
        db, user.id_usuario, token_service.VERIFICATION, token_service.VERIFICATION_LIFETIME
    )
    template = email_service.email_change_confirmation if change else email_service.verification_email
    subject, text = template(user.nombre_usuario, token, VERIFICATION_HOURS)
    email_service.send_in_background(tasks, to, subject, text)


@router.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(REGISTER_LIMIT)
def register_user(
    request: Request,
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> models.Usuario:
    """Create an unverified account and e-mail the link that activates it."""
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
    try:
        created = user_service.create_user(db=db, user=user)
    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=DUPLICATE_ACCOUNT) from exc
    _send_verification(background_tasks, db, created, created.correo_electronico, change=False)
    db.commit()
    db.refresh(created)
    return created


@router.post("/login")
@limiter.limit(LOGIN_LIMIT)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    """Authenticate a verified user and return a JWT access token.

    Limited to 5 attempts per minute per IP to mitigate brute force. The right
    password on an unverified account answers 403.
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
    if not user.correo_verificado:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=EMAIL_NOT_VERIFIED)

    access_token = security.create_access_token(data={"sub": str(user.id_usuario)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/verificacion/reenviar", response_model=schemas.MessageResponse)
@limiter.limit(RESEND_VERIFICATION_LIMIT)
def resend_verification(
    request: Request,
    payload: schemas.ResendVerificationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> dict:
    """Send a new link to an unverified account; the answer never says which case applied."""
    user = user_service.get_user_by_email(db, email=payload.correo_electronico)
    if user is not None and not user.correo_verificado:
        _send_verification(background_tasks, db, user, user.correo_electronico, change=False)
        db.commit()
    return {"message": RESEND_ANSWER}


@router.post("/verificacion/confirmar", response_model=schemas.MessageResponse)
@limiter.limit(CONFIRM_LINK_LIMIT)
def confirm_verification(
    request: Request,
    payload: schemas.TokenRequest,
    db: Session = Depends(get_db),
) -> dict:
    """Confirm the address of the link: activate the account or apply the pending e-mail."""
    token = token_service.consume(db, payload.token, token_service.VERIFICATION)
    user = user_service.get_user_by_id(db, token.id_usuario) if token else None
    if user is None:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=INVALID_LINK)
    if not user_service.confirm_email(db, user):
        db.commit()  # the token stays used and the stale pending address is dropped
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_TAKEN)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_TAKEN) from exc
    return {"message": EMAIL_CONFIRMED}


@router.get("/me", response_model=schemas.UserResponse)
def read_my_profile(current_user: models.Usuario = Depends(get_current_user)) -> models.Usuario:
    """Return the authenticated user's profile."""
    return current_user


def _check_email_change(
    db: Session, user: models.Usuario, new_email: str, password: str | None
) -> None:
    """Refuse an e-mail change without the right current password or to a taken address."""
    if not password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=PASSWORD_REQUIRED_FOR_EMAIL)
    if not security.verify_password(password, user.contrasena_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=WRONG_CURRENT_PASSWORD)
    if user_service.email_in_use(db, new_email, except_user_id=user.id_usuario):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=EMAIL_TAKEN)


@router.put("/me", response_model=schemas.UserResponse)
def update_my_profile(
    user_data: schemas.UserUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user),
) -> models.Usuario:
    """Update the username at once; a new e-mail waits until its link is opened.

    Changing the e-mail needs the current password. The new address goes to
    ``correo_pendiente`` and gets the confirmation link; the current address
    gets a notice. Login keeps using the current address until then.
    """
    new_email = user_data.correo_electronico
    if new_email == current_user.correo_electronico.lower():
        new_email = None
    if new_email is not None:
        _check_email_change(db, current_user, new_email, user_data.password_actual)

    if user_data.nombre_usuario and user_data.nombre_usuario != current_user.nombre_usuario:
        if user_service.get_user_by_username(db, username=user_data.nombre_usuario):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nuevo nombre de usuario ya esta en uso.",
            )
        current_user.nombre_usuario = user_data.nombre_usuario

    if new_email is not None:
        current_user.correo_pendiente = new_email
        _send_verification(background_tasks, db, current_user, new_email, change=True)
        subject, text = email_service.email_change_notice(current_user.nombre_usuario, new_email)
        email_service.send_in_background(background_tasks, current_user.correo_electronico, subject, text)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        background_tasks.tasks.clear()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=DUPLICATE_ACCOUNT) from exc
    db.refresh(current_user)
    return current_user
