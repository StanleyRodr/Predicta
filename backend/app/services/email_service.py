"""Outgoing e-mail: the only module that talks to SMTP.

``EMAIL_BACKEND=console`` logs each message instead of sending it (development
and tests). ``smtp`` opens a connection with STARTTLS and logs in, so any
provider works with environment variables alone (Brevo in production).

Routes queue messages with ``send_in_background``: the response does not wait
for the provider, its timing reveals nothing, and a delivery failure is logged
instead of turning into a 500.
"""

import smtplib
import ssl
from email.message import EmailMessage

from fastapi import BackgroundTasks
from loguru import logger

from app.core.config import settings

SMTP_TIMEOUT_SECONDS = 15
DEFAULT_SENDER = "Predicta <no-responder@localhost>"


def build_message(to: str, subject: str, text: str) -> EmailMessage:
    """Plain-text message from ``EMAIL_FROM`` to ``to``."""
    message = EmailMessage()
    message["From"] = settings.email_from or DEFAULT_SENDER
    message["To"] = to
    message["Subject"] = subject
    message.set_content(text)
    return message


def _deliver(message: EmailMessage) -> None:
    """Hand the message to the configured backend; tests replace this function."""
    if settings.email_backend == "console":
        # Decoded text, not the MIME form: quoted-printable would split the link.
        logger.info(
            "Correo (EMAIL_BACKEND=console)\nPara: {}\nAsunto: {}\n\n{}",
            message["To"],
            message["Subject"],
            message.get_content(),
        )
        return
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST no está configurado.")
    context = ssl.create_default_context()
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
        smtp.starttls(context=context)
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)


def send_email(to: str, subject: str, text: str) -> None:
    """Send one plain-text e-mail now; raises if the backend fails."""
    _deliver(build_message(to, subject, text))


def _send_logging_failures(to: str, subject: str, text: str) -> None:
    try:
        send_email(to, subject, text)
    except Exception:  # noqa: BLE001 - a provider failure must never reach the client
        logger.exception("No se pudo enviar el correo '{}'.", subject)


def send_in_background(tasks: BackgroundTasks, to: str, subject: str, text: str) -> None:
    """Queue the e-mail to go out after the response is sent."""
    tasks.add_task(_send_logging_failures, to, subject, text)


# --------------------------------------------------------------- templates


def verification_link(token: str) -> str:
    """Frontend page that confirms the address; the token travels in the fragment."""
    return f"{settings.frontend_url}/verificar-correo#token={token}"


def verification_email(nombre_usuario: str, token: str, hours: int) -> tuple[str, str]:
    """Subject and body of the link that confirms a new account."""
    text = (
        f"Hola, {nombre_usuario}:\n\n"
        "Para activar tu cuenta de Predicta, abre este enlace:\n\n"
        f"{verification_link(token)}\n\n"
        f"El enlace sirve una sola vez y vence en {hours} horas.\n"
        "Si no creaste esta cuenta, ignora este correo.\n"
    )
    return "Confirma tu correo en Predicta", text


def email_change_confirmation(nombre_usuario: str, token: str, hours: int) -> tuple[str, str]:
    """Subject and body sent to the new address of an account."""
    text = (
        f"Hola, {nombre_usuario}:\n\n"
        "Pediste usar este correo en tu cuenta de Predicta. Para confirmarlo, abre este enlace:\n\n"
        f"{verification_link(token)}\n\n"
        f"El enlace sirve una sola vez y vence en {hours} horas. "
        "Hasta que lo abras, tu cuenta sigue usando el correo anterior.\n"
        "Si no lo pediste, ignora este correo.\n"
    )
    return "Confirma tu nuevo correo en Predicta", text


def email_change_notice(nombre_usuario: str, new_email: str) -> tuple[str, str]:
    """Subject and body sent to the current address when a change is requested."""
    text = (
        f"Hola, {nombre_usuario}:\n\n"
        f"Se pidió cambiar el correo de tu cuenta a {new_email}. "
        "El cambio se aplica solo cuando alguien abra el enlace enviado a ese correo.\n\n"
        "Si no fuiste tú, cambia tu contraseña.\n"
    )
    return "Se pidió cambiar el correo de tu cuenta de Predicta", text


def reset_link(token: str) -> str:
    """Frontend page that sets a new password; the token travels in the fragment."""
    return f"{settings.frontend_url}/restablecer-contrasena#token={token}"


def password_reset_email(nombre_usuario: str, token: str, minutes: int) -> tuple[str, str]:
    """Subject and body of the link that sets a new password."""
    text = (
        f"Hola, {nombre_usuario}:\n\n"
        "Para elegir una contraseña nueva en Predicta, abre este enlace:\n\n"
        f"{reset_link(token)}\n\n"
        f"El enlace sirve una sola vez y vence en {minutes} minutos. "
        "Al usarlo se cierran todas las sesiones abiertas.\n"
        "Si no lo pediste, ignora este correo: tu contraseña no cambia.\n"
    )
    return "Restablece tu contraseña de Predicta", text


def password_changed_notice(nombre_usuario: str) -> tuple[str, str]:
    """Subject and body sent after the password changes from the profile."""
    text = (
        f"Hola, {nombre_usuario}:\n\n"
        "La contraseña de tu cuenta de Predicta acaba de cambiar y se cerraron las demás sesiones.\n\n"
        "Si no fuiste tú, pide un enlace en \"¿Olvidaste tu contraseña?\" desde la página de inicio de sesión.\n"
    )
    return "Tu contraseña de Predicta cambió", text


def account_locked_notice(nombre_usuario: str, token: str, minutes: int, lock_minutes: int) -> tuple[str, str]:
    """Subject and body sent when wrong passwords lock the account."""
    text = (
        f"Hola, {nombre_usuario}:\n\n"
        f"Hubo varios intentos de entrar a tu cuenta de Predicta con una contraseña incorrecta, "
        f"así que la bloqueamos {lock_minutes} minutos.\n\n"
        "Si fuiste tú y no recuerdas la contraseña, o si no fuiste tú, elige una nueva con este enlace. "
        "Al usarlo se quita el bloqueo:\n\n"
        f"{reset_link(token)}\n\n"
        f"El enlace sirve una sola vez y vence en {minutes} minutos.\n"
    )
    return "Bloqueamos tu cuenta de Predicta por seguridad", text
