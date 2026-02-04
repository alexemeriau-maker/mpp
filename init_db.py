import os
import psycopg2
from werkzeug.security import generate_password_hash
from psycopg2.extras import execute_values

# ------------------------
# --- Connexion PostgreSQL ---
# ------------------------

DATABASE_URL = "postgresql://fly-user:JCTDYtQS0rRthh4l5O01LrYT@pgbouncer.ey5qn0yd34808zmw.flympg.net:5432/fly-db"

conn = psycopg2.connect(DATABASE_URL)
c = conn.cursor()

# ------------------------
# --- Supprimer anciennes tables ---
# ------------------------
tables = ["pronos", "x2", "bonus", "results", "matchs", "journees", "users"]
for t in tables:
    c.execute(f"DROP TABLE IF EXISTS {t} CASCADE")

# ------------------------
# --- Création des tables ---
# ------------------------
c.execute("""
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    prenom TEXT,
    nom TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    x2_used INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE journees (
    id SERIAL PRIMARY KEY,
    nom TEXT,
    date_debut TIMESTAMP,
    verrou TIMESTAMP,
    mail_rappel_envoye INTEGER DEFAULT 0,
    mail_verrou_envoye INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE matchs (
    id SERIAL PRIMARY KEY,
    journee_id INTEGER REFERENCES journees(id) ON DELETE CASCADE,
    equipe_dom TEXT,
    equipe_ext TEXT
)
""")

c.execute("""
CREATE TABLE pronos (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    match_id INTEGER REFERENCES matchs(id) ON DELETE CASCADE,
    score_dom INTEGER,
    score_ext INTEGER,
    PRIMARY KEY(user_id, match_id)
)
""")

c.execute("""
CREATE TABLE x2 (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    journee_id INTEGER REFERENCES journees(id) ON DELETE CASCADE,
    PRIMARY KEY(user_id, journee_id)
)
""")

c.execute("""
CREATE TABLE bonus (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    meilleur_buteur TEXT,
    champion TEXT,
    points INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE results (
    match_id INTEGER PRIMARY KEY REFERENCES matchs(id) ON DELETE CASCADE,
    score_dom INTEGER,
    score_ext INTEGER
)
""")

# ------------------------
# --- Utilisateurs test ---
# ------------------------
users = [
    ("Alexis", "Emeriau", "alex.emeriau@gmail.com", generate_password_hash("Abline"))
]
execute_values(c,
    "INSERT INTO users (prenom, nom, email, password_hash) VALUES %s",
    users
)

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
        VALUES (%s, %s, %s, %s, 0, 0)
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
# --- Matchs retour ---
# ------------------------
matchs_retour = [(m[0]+7, m[2], m[1]) for m in matchs_aller]
all_matchs = matchs_aller + matchs_retour

execute_values(c,
    "INSERT INTO matchs (journee_id, equipe_dom, equipe_ext) VALUES %s",
    all_matchs
)

# ------------------------
# --- Commit & Close ---
# ------------------------
conn.commit()
conn.close()

print("Base PostgreSQL Fly.io initialisée avec 14 journées et 4 matchs par journée (aller-retour) !")
