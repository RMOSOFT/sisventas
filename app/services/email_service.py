import smtplib
from email.message import EmailMessage
from app.core.config import settings


def send_email(to_email: str, subject: str, html: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email
    msg.set_content("Tu cliente de correo no soporta HTML.")
    msg.add_alternative(html, subtype="html")

    host = settings.SMTP_HOST
    port = int(settings.SMTP_PORT)

    # ✅ Puerto 465 = SSL directo
    if port == 465:
        with smtplib.SMTP_SSL(host, port) as smtp:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.send_message(msg)
        return

    # ✅ Puerto 587 = STARTTLS
    with smtplib.SMTP(host, port) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)

"""
def send_email(to_email: str, subject: str, html: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email
    msg.set_content("Tu cliente de correo no soporta HTML.")
    msg.add_alternative(html, subtype="html")

    with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)

"""