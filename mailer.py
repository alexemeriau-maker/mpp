import smtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

EMAIL = "alex.emeriau@gmail.com"
PASSWORD = "nhzb aoyx rued spfp"   # IMPORTANT

def send_mail(to, subject, body):
    msg = EmailMessage()
    msg["From"] = f"MPP 🏆 <{EMAIL}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.send_message(msg)
