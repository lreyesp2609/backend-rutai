import resend
from ...database.config import settings

resend.api_key = settings.resend_api_key


def enviar_email_recuperacion(email_destino: str, token: str):
    reset_url = f"{settings.frontend_url.rstrip('/')}/reset-password.html?token={token}"
    
    params = {
        "from": "onboarding@resend.dev",
        "to": email_destino,
        "subject": "Recuperación de contraseña - RutAI",
        "html": f"""
        <p>Hola,</p>
        <p>Recibimos una solicitud para restablecer tu contraseña.</p>
        <p>Haz clic en el siguiente enlace (válido por 30 minutos):</p>
        <p><a href="{reset_url}">{reset_url}</a></p>
        <p>Si no solicitaste este cambio, ignora este correo.</p>
        """
    }
    
    return resend.Emails.send(params)
