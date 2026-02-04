import sqlite3
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta

# --- CONFIG SMTP ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL = "alex.emeriau@gmail.com"        # ton email
PASSWORD = "nhzb aoyx rued spfp"      # mot de passe ou token d'application

def send_mail(to, subject, body):
    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as s:
        s.starttls()
        s.login(EMAIL, PASSWORD)
        s.send_message(msg)

def notify_users(message, subject):
    conn = sqlite3.connect("mpp.db")
    c = conn.cursor()
    users = c.execute("SELECT email FROM users WHERE email IS NOT NULL").fetchall()
    for u in users:
        send_mail(u[0], subject, message)
    conn.close()

def main():
    now = datetime.now()
    conn = sqlite3.connect("mpp.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    journees = c.execute("SELECT * FROM journees").fetchall()
    for j in journees:
        verrou = datetime.fromisoformat(j["verrou"])

        # --- On commence à vérifier seulement 20 minutes avant ---
        if now < verrou - timedelta(minutes=20):
            continue

        # --- Rappel 15 minutes avant verrou ---
        if j["mail_rappel_envoye"] == 0 and verrou - timedelta(minutes=15) <= now < verrou:
            notify_users(
                f"⏰ Il te reste 15 minutes pour valider tes pronostics pour {j['nom']} !",
                f"MPP – rappel pronostics {j['nom']}"
            )
            c.execute("UPDATE journees SET mail_rappel_envoye=1 WHERE id=?", (j["id"],))
            print(f"Mail rappel envoyé pour {j['nom']}")

        # --- Verrouillage ---
        if j["mail_verrou_envoye"] == 0 and now >= verrou:
            notify_users(
                f"🔒 Les pronostics pour {j['nom']} sont maintenant verrouillés. Bonne chance 🍀",
                f"MPP – pronostics verrouillés {j['nom']}"
            )
            c.execute("UPDATE journees SET mail_verrou_envoye=1 WHERE id=?", (j["id"],))
            print(f"Mail verrou envoyé pour {j['nom']}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
