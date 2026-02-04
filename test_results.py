import sqlite3
import random

DB = "mpp.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

# Récupérer tous les matchs
matchs = c.execute("SELECT id, journee_id, equipe_dom, equipe_ext FROM matchs").fetchall()

for m in matchs:
    match_id = m[0]
    journee_id = m[1]
    equipe_dom = m[2]
    equipe_ext = m[3]

    # Générer des scores aléatoires réalistes (0 à 5 buts)
    score_dom = random.randint(0, 5)
    score_ext = random.randint(0, 5)

    # Insérer ou mettre à jour les résultats
    c.execute("""
        INSERT OR REPLACE INTO results(match_id, score_dom, score_ext)
        VALUES (?, ?, ?)
    """, (match_id, score_dom, score_ext))

conn.commit()
conn.close()
print("Résultats aléatoires insérés pour toutes les journées !")
