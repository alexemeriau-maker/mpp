import psycopg2
from psycopg2.extras import execute_values
from werkzeug.security import generate_password_hash

# === CONFIG CONNECTION ===
DB_HOST = "ton_host"       # ex: your-project.neon.tech
DB_PORT = 5432
DB_NAME = "defaultdb"      # Neon te donne le nom de la db
DB_USER = "ton_user"
DB_PASSWORD = "ton_password"

conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
c = conn.cursor()

# ------------------------
# --- Création des tables ---
# ------------------------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    prenom TEXT,
    nom TEXT,
    email TEXT UNIQUE,
    password_hash TEXT,
    x2_used INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS journees (
    id SERIAL PRIMARY KEY,
    nom TEXT,
    date_debut TIMESTAMP,
    verrou TIMESTAMP,
    mail_rappel_envoye BOOLEAN DEFAULT FALSE,
    mail_verrou_envoye BOOLEAN DEFAULT FALSE
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS matchs (
    id SERIAL PRIMARY KEY,
    journee_id INTEGER REFERENCES journees(id),
    equipe_dom TEXT,
    equipe_ext TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS pronos (
    user_id INTEGER REFERENCES users(id),
    match_id INTEGER REFERENCES matchs(id),
    score_dom INTEGER,
    score_ext INTEGER,
    PRIMARY KEY(user_id, match_id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS x2 (
    user_id INTEGER REFERENCES users(id),
    journee_id INTEGER REFERENCES journees(id),
    PRIMARY KEY(user_id)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS bonus (
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    meilleur_buteur TEXT,
    champion TEXT,
    points INTEGER DEFAULT 0
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS results (
    match_id INTEGER PRIMARY KEY REFERENCES matchs(id),
    score_dom INTEGER,
    score_ext INTEGER
)
""")

# ------------------------
# --- Données test ---
# ------------------------
# Utilisateurs
users = [("Alexis", "Emeriau", "alex.emeriau@gmail.com", generate_password_hash("Abline"))]
execute_values(c, """
INSERT INTO users (prenom, nom, email, password_hash)
VALUES %s ON CONFLICT (email) DO NOTHING
""", users)

# Journées
journees = [
    ("Journée 1", "2026-02-06 00:00", "2026-02-06 20:45"),
    ("Journée 2", "2026-02-13 00:00", "2026-02-13 19:00"),
    ("Journée 3", "2026-02-20 00:00", "2026-02-20 20:45"),
    ("Journée 4", "2026-02-27 00:00", "2026-02-27 20:45"),
]
execute_values(c, """
INSERT INTO journees (nom, date_debut, verrou)
VALUES %s
""", journees)

# Équipes
equipes = [
    "Chez Tati t'as tout", "FC Sotocard", "Champion d'Europe", "Vallée de Kersaudy",
    "L'ours pyrénéen", "Moussetoir", "Alex Périensse", "OSS 117"
]

# Matchs aller (exemple J1-J2)
matchs_aller = [
    (1, equipes[0], equipes[1]), (1, equipes[2], equipes[3]),
    (1, equipes[4], equipes[5]), (1, equipes[6], equipes[7]),
    (2, equipes[1], equipes[6]), (2, equipes[7], equipes[4]),
    (2, equipes[5], equipes[2]), (2, equipes[3], equipes[0])
]

execute_values(c, """
INSERT INTO matchs (journee_id, equipe_dom, equipe_ext)
VALUES %s
""", matchs_aller)

conn.commit()
conn.close()
print("Base PostgreSQL initialisée sur Neon.tech avec données test !")
