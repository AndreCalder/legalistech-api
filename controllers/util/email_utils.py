from flask_mail import Message
from controllers.util.email_config import configure_mail, mail
import os

def send_pin_email(to_email: str, pin_code: str, user_id: str):
    link = f"{os.getenv('FRONTEND_VERIFY_URL', 'http://localhost:3000')}/verify?uid={user_id}"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f9f9f9; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 8px;">
          <h2 style="color: #132956;">Verifica tu cuenta</h2>
          <p>Hola <strong>{to_email}</strong>,</p>
          <p>Tu código de verificación es:</p>
          <p style="font-size: 1.8em; font-weight: bold; text-align: center; letter-spacing: 3px;">{pin_code}</p>
          <p>Puedes verificar tu cuenta usando este código o haciendo clic en el siguiente botón:</p>
          <div style="text-align: center; margin: 20px 0;">
            <a href="{link}" style="background-color: #132956; color: white; padding: 12px 20px; border-radius: 5px; text-decoration: none;">Verificar Cuenta</a>
          </div>
          <p>Este código expirará en 10 minutos.</p>
          <hr style="margin-top: 30px;">
          <p style="font-size: 0.85em; color: #888;">Este mensaje fue enviado a: {to_email}</p>
        </div>
      </body>
    </html>
    """

    text = (
        f"Hola,\n\n"
        f"Gracias por registrarte en Legalistech.\n"
        f"Tu código de verificación es: {pin_code}\n\n"
        f"También puedes verificar usando este enlace: {link}\n"
        f"Este código expirará en 10 minutos.\n\n"
        f"— Equipo Legalistech"
    )

    msg = Message(
        subject="Código de verificación de Legalistech",
        sender=os.getenv("MAIL_DEFAULT_SENDER"),  # ✅ now loaded from .env
        recipients=[to_email],
        body=text,
        html=html
    )

    mail.send(msg)
