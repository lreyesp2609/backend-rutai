from resend import Resend
from ...database.config import settings

resend_client = Resend(settings.resend_api_key)


def enviar_email_recuperacion(email_destino: str, token: str):
    reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
    subject = "Recuperación de contraseña"
    html = f"""
    <p>Hola,</p>
    <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
    <p>Haz clic en el siguiente enlace para continuar:</p>
    <p><a href=\"{reset_url}\">{reset_url}</a></p>
    <p>Si no solicitaste este cambio, ignora este correo.</p>
    """

    return resend_client.emails.send(
        from_="onboarding@resend.dev",
        to=email_destino,
        subject=subject,
        html=html
    )
