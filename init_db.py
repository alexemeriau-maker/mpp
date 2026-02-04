import sqlite3
from werkzeug.security import generate_password_hash

DB = "mpp.db"
conn = sqlite3.connect(DB)
c = conn.cursor()

# ------------------------
# --- Supprimer anciennes tables ---
# ------------------------
tables = ["users", "journees", "matchs", "pronos", "x2", "bonus", "results"]
for t in tables:
    c.execute(f"DROP TABLE IF EXISTS {t}")

# ------------------------
# --- Création des tables ---
# ------------------------
c.execute("""
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prenom TEXT,
    nom TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    x2_used INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE journees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    date_debut TEXT,
    verrou TEXT,
    mail_rappel_envoye INTEGER DEFAULT 0,
    mail_verrou_envoye INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE matchs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journee_id INTEGER,
    equipe_dom TEXT,
    equipe_ext TEXT
)
""")

c.execute("""
CREATE TABLE pronos (
    user_id INTEGER,
    match_id INTEGER,
    score_dom INTEGER,
    score_ext INTEGER,
    PRIMARY KEY(user_id, match_id)
)
""")

c.execute("""
CREATE TABLE x2 (
    user_id INTEGER,
    journee_id INTEGER,
    PRIMARY KEY(user_id, journee_id)
)
""")

c.execute("""
CREATE TABLE bonus (
    user_id INTEGER PRIMARY KEY,
    meilleur_buteur TEXT,
    champion TEXT,
    points INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE results (
    match_id INTEGER PRIMARY KEY,
    score_dom INTEGER,
    score_ext INTEGER
)
""")

# Supprimer les données existantes
c.execute("DELETE FROM pronos")
c.execute("DELETE FROM x2")
c.execute("DELETE FROM bonus")
c.execute("DELETE FROM results")
c.execute("DELETE FROM matchs")
c.execute("DELETE FROM journees")
c.execute("DELETE FROM users")

# Réinitialiser les séquences
for table in ["users", "matchs", "pronos", "journees", "bonus", "x2", "results"]:
    c.execute(f"DELETE FROM sqlite_sequence WHERE name='{table}'")

# ------------------------
# --- Utilisateurs test ---
# ------------------------
users = [
    ("Alexis", "Emeriau", "alex.emeriau@gmail.com", generate_password_hash("Abline"))
]
c.executemany("INSERT INTO users (prenom, nom, email, password_hash) VALUES (?,?,?,?)", users)

# ------------------------
# --- Journées ---
# ------------------------
journees = [
    ("Journée 1", "2026-02-06 00:00", "2026-02-06 20:45"),
    ("Journée 2", "2026-02-13 00:00", "2026-02-13 19:00"),
    ("Journée 3", "2026-02-20 00:00", "2026-02-20 20:45"),
    ("Journée 4", "2026-02-27 00:00", "2026-02-27 20:45"),
    ("Journée 5", "2026-03-08 00:00", "2026-03-08 20:45"),
    ("Journée 6", "2026-03-15 00:00", "2026-03-15 20:45"),
    ("Journée 7", "2026-03-22 00:00", "2026-03-22 20:45"),
    ("Journée 8", "2026-04-05 00:00", "2026-04-05 20:45"),
    ("Journée 9", "2026-04-12 00:00", "2026-04-12 20:45"),
    ("Journée 10", "2026-04-19 00:00", "2026-04-19 20:45"),
    ("Journée 11", "2026-04-26 00:00", "2026-04-26 20:45"),
    ("Journée 12", "2026-05-03 00:00", "2026-05-03 20:45"),
    ("Journée 13", "2026-05-09 00:00", "2026-05-09 21:00"),
    ("Journée 14", "2026-05-16 00:00", "2026-05-16 21:00")
]

for i, j in enumerate(journees):
    c.execute("""
        INSERT INTO journees (id, nom, date_debut, verrou, mail_rappel_envoye, mail_verrou_envoye)
        VALUES (?,?,?,?,0,0)
    """, (i+1, j[0], j[1], j[2]))

# ------------------------
# --- Équipes ---
# ------------------------
equipes = [
    "Chez Tati t'as tout",
    "FC Sotocard",
    "Champion d'Europe",
    "Vallée de Kersaudy",
    "L'ours pyrénéen",
    "Moussetoir",
    "Alex Périensse",
    "OSS 117"
]

# ------------------------
# --- Matchs aller ---
# ------------------------
matchs_aller = [
    # J1
    (1, equipes[0], equipes[1]),
    (1, equipes[2], equipes[3]),
    (1, equipes[4], equipes[5]),
    (1, equipes[6], equipes[7]),
    # J2
    (2, equipes[1], equipes[6]),
    (2, equipes[7], equipes[4]),
    (2, equipes[5], equipes[2]),
    (2, equipes[3], equipes[0]),
    # J3
    (3, equipes[2], equipes[7]),
    (3, equipes[4], equipes[1]),
    (3, equipes[6], equipes[0]),
    (3, equipes[5], equipes[3]),
    # J4
    (4, equipes[0], equipes[4]),
    (4, equipes[1], equipes[2]),
    (4, equipes[7], equipes[5]),
    (4, equipes[3], equipes[6]),
    # J5
    (5, equipes[2], equipes[0]),
    (5, equipes[4], equipes[6]),
    (5, equipes[7], equipes[3]),
    (5, equipes[5], equipes[1]),
    # J6
    (6, equipes[0], equipes[5]),
    (6, equipes[1], equipes[7]),
    (6, equipes[4], equipes[3]),
    (6, equipes[6], equipes[2]),
    # J7
    (7, equipes[2], equipes[4]),
    (7, equipes[7], equipes[0]),
    (7, equipes[5], equipes[6]),
    (7, equipes[3], equipes[1])
]

# ------------------------
# --- Matchs retour (inverse domicile/extérieur) ---
# ------------------------
matchs_retour = [(m[0]+7, m[2], m[1]) for m in matchs_aller]

# Tous les matchs
all_matchs = matchs_aller + matchs_retour
c.executemany("INSERT INTO matchs (journee_id, equipe_dom, equipe_ext) VALUES (?,?,?)", all_matchs)

# ------------------------
# --- Commit & Close ---
# ------------------------
conn.commit()
conn.close()

print("Base mpp.db créée avec 14 journées et 4 matchs par journée (aller-retour) !")
