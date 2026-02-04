import sqlite3

conn = sqlite3.connect("mpp.db")
c = conn.cursor()

# Afficher toutes les journées
jours = c.execute("SELECT * FROM journees").fetchall()
print("Journées :")
print(jours)

# Afficher tous les matchs
matchs = c.execute("SELECT * FROM matchs").fetchall()
print("Matchs :")
print(matchs)

conn.close()
