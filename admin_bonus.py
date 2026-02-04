import os
import psycopg2

# ------------------------
# --- Connexion PostgreSQL ---
# ------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()

# --- Résultats officiels ---
vrai_buteur = "Sulc"
vrai_champion = "Chez Tati t'as tout"

# --- Calcul points bonus ---
c.execute("SELECT user_id, meilleur_buteur, champion FROM bonus")
rows = c.fetchall()

for user_id, meilleur_buteur, champion in rows:
    points = 0
    if meilleur_buteur == vrai_buteur:
        points += 5
    if champion == vrai_champion:
        points += 5
    c.execute(
        "UPDATE bonus SET points=%s WHERE user_id=%s",
        (points, user_id)
    )

conn.commit()
conn.close()

print("Points bonus calculés et mis à jour !")
