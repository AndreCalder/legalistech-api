import mandrill
import os

mandrill_client = mandrill.Mandrill(os.getenv("MAILCHIMP_TRANSACTIONAL_KEY"))

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

    message = {
        "subject": "Código de verificación de Legalistech",
        "from_email": os.getenv("MAIL_DEFAULT_SENDER"),
        "to": [{"email": to_email, "type": "to"}],
        "html": html,
        "text": text,
        "headers": {"Reply-To": os.getenv("MAIL_DEFAULT_SENDER")},
        "auto_text": True
    }

    return mandrill_client.messages.send(message=message)



def notify_admin_new_contact(name: str, last_name: str, email: str, phone: str, message_text: str):
    admin_email = os.getenv("MAILCHIMP_ADMIN_NOTIFY_EMAIL", "test@milegalistech.com")

    subject = "📬 Nuevo contacto desde el formulario de MiLegalistech"

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: auto; background: #f9f9f9; padding: 30px; border-radius: 8px;">
          <h2 style="color: #132956;">Nuevo contacto registrado</h2>
          <p><strong>Nombre:</strong> {name} {last_name}</p>
          <p><strong>Email:</strong> {email}</p>
          <p><strong>Teléfono:</strong> {phone}</p>
          <p><strong>Mensaje:</strong></p>
          <blockquote style="background: #fff; padding: 15px; border-left: 5px solid #132956;">{message_text}</blockquote>
        </div>
      </body>
    </html>
    """

    text = (
        f"Nuevo contacto registrado:\n\n"
        f"Nombre: {name} {last_name}\n"
        f"Email: {email}\n"
        f"Teléfono: {phone}\n"
        f"Mensaje:\n{message_text}"
    )

    message = {
        "subject": subject,
        "from_email": os.getenv("MAIL_DEFAULT_SENDER"),
        "to": [{"email": admin_email, "type": "to"}],
        "html": html,
        "text": text,
        "headers": {"Reply-To": os.getenv("MAIL_DEFAULT_SENDER")},
        "auto_text": True
    }

    return mandrill_client.messages.send(message=message)

