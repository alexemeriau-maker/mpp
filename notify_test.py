import sqlite3
from datetime import datetime, timedelta
from mailer import send_mail  # ton fichier mailer.py

# ----------------------
# Connexion à la DB
# ----------------------
DB = "mpp.db"
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# ----------------------
# Créer une journée test
# ----------------------
now = datetime.now()
verrou_test = (now + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M")  # verrou dans 1 minute

# Supprime si déjà existante
c.execute("DELETE FROM journees WHERE nom='Test Journée'")
conn.commit()

# Insère la journée test avec colonnes mail
c.execute("""
    INSERT INTO journees (nom, date_debut, verrou, mail_rappel_envoye, mail_verrou_envoye)
    VALUES (?, ?, ?, 0, 0)
""", ("Journée 1", now.strftime("%Y-%m-%d %H:%M"), verrou_test))
conn.commit()

# ----------------------
# Fonction de notification
# ----------------------
def notify():
    journees = c.execute("SELECT * FROM journees").fetchall()
    for j in journees:
        verrou = datetime.strptime(j["verrou"], "%Y-%m-%d %H:%M")
        # 15 minutes avant le verrou → rappel
        if j["mail_rappel_envoye"] == 0 and now >= verrou - timedelta(minutes=15) and now < verrou:
            print(f"[TEST] Envoi rappel pour {j['nom']}")
            send_mail(
                "alex.emeriau@gmail.com",  # remplace par ton mail
                f"MPP – rappel pronos {j['nom']}",
                f"⏰ Il te reste 15 minutes pour valider tes pronostics pour {j['nom']} !"
            )
            c.execute("UPDATE journees SET mail_rappel_envoye=1 WHERE id=?", (j["id"],))
            conn.commit()
        # Moment du verrou → verrouillage
        elif j["mail_verrou_envoye"] == 0 and now >= verrou:
            print(f"[TEST] Envoi mail verrouillage pour {j['nom']}")
            send_mail(
                "alex.emeriau@gmail.com",  # remplace par ton mail
                f"MPP – pronostics verrouillés {j['nom']}",
                f"🔒 Les pronostics pour {j['nom']} sont maintenant verrouillés. Bonne chance 🍀"
            )
            c.execute("UPDATE journees SET mail_verrou_envoye=1 WHERE id=?", (j["id"],))
            conn.commit()

# ----------------------
# Appel de la fonction
# ----------------------
notify()

print("Test de notification terminé.")
conn.close()
