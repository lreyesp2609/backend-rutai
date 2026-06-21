import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ...database.config import settings
import os
import logging

logger = logging.getLogger(__name__)

def enviar_email_recuperacion(email_destino: str, token: str):
    reset_url = f"{settings.frontend_url.rstrip('/static')}/login/reset-password?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Recuperación de contraseña - RutAI"
    msg["From"] = f"RutAI <{os.getenv('GMAIL_USER')}>"
    msg["To"] = email_destino

    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 480px; 
                margin: auto; padding: 32px;">
        <h2 style="color: #1D9E75;">Restablecer contraseña</h2>
        <p>Hola, recibimos una solicitud para restablecer tu contraseña.</p>
        <p>Haz clic en el botón (válido por 30 minutos):</p>
        <a href="{reset_url}"
           style="display:inline-block; margin: 16px 0; padding: 12px 24px;
                  background:#1D9E75; color:#fff; border-radius:8px;
                  text-decoration:none; font-weight:600;">
            Restablecer contraseña
        </a>
        <p style="color:#888; font-size:13px;">
            Si no solicitaste este cambio, ignora este correo.
        </p>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(os.getenv("GMAIL_USER"), os.getenv("GMAIL_APP_PASSWORD"))
            server.sendmail(os.getenv("GMAIL_USER"), email_destino, msg.as_string())
        logger.info(f"✅ Email enviado a {email_destino}")
    except Exception as e:
        logger.error(f"❌ Error enviando email: {e}")
        raise
