import sqlite3

DB = "mpp.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

# --- Résultats officiels ---
vrai_buteur = "Sulc"
vrai_champion = "Chez Tati t'as tout"

# --- Calcul points bonus ---
rows = c.execute("SELECT user_id, meilleur_buteur, champion FROM bonus").fetchall()
for r in rows:
    points = 0
    if r[1] == vrai_buteur:
        points += 5
    if r[2] == vrai_champion:
        points += 5
    c.execute("UPDATE bonus SET points=? WHERE user_id=?", (points, r[0]))

conn.commit()
conn.close()
print("Points bonus calculés et mis à jour !")
