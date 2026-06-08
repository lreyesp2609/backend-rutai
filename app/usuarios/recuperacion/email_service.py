import resend
from ...database.config import settings

resend.api_key = settings.resend_api_key


def enviar_email_recuperacion(email_destino: str, token: str):
    reset_url = f"{settings.frontend_url.rstrip('/static')}/login/reset-password?token={token}"
    
    try:
        params = {
            "from": "onboarding@resend.dev",
            "to": email_destino,
            "subject": "Recuperación de contraseña - RutAI",
            "html": f"""
            <p>Hola,</p>
            <p>Recibimos una solicitud para restablecer tu contraseña.</p>
            <p>Haz clic aquí (válido 30 minutos):</p>
            <p><a href="{reset_url}">{reset_url}</a></p>
            <p>Si no solicitaste este cambio, ignora este correo.</p>
            """
        }
        return resend.Emails.send(params)
    except AttributeError:
        from resend import Resend
        client = Resend(settings.resend_api_key)
        return client.emails.send(
            from_="onboarding@resend.dev",
            to=email_destino,
            subject="Recuperación de contraseña - RutAI",
            html=params["html"]
        )
