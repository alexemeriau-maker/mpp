import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("DATABASE_URL non définie")

conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
cur = conn.cursor()

print("\n=== USERS ===")
cur.execute("SELECT id, prenom, nom, email FROM users ORDER BY id")
for u in cur.fetchall():
    print(u)

print("\n=== JOURNEES ===")
cur.execute("SELECT id, nom, verrou FROM journees ORDER BY id")
for j in cur.fetchall():
    print(j)

print("\n=== MATCHS ===")
cur.execute("""
    SELECT m.id, j.nom AS journee, m.equipe_dom, m.equipe_ext
    FROM matchs m
    JOIN journees j ON j.id = m.journee_id
    ORDER BY m.id
""")
for m in cur.fetchall():
    print(m)

print("\n=== PRONOS ===")
cur.execute("""
    SELECT
        u.prenom,
        u.nom,
        m.equipe_dom,
        m.equipe_ext,
        p.score_dom,
        p.score_ext
    FROM pronos p
    JOIN users u ON u.id = p.user_id
    JOIN matchs m ON m.id = p.match_id
    ORDER BY u.id, m.id
""")
for p in cur.fetchall():
    print(p)

print("\n=== X2 ===")
cur.execute("""
    SELECT u.prenom, u.nom, j.nom AS journee
    FROM x2
    JOIN users u ON u.id = x2.user_id
    JOIN journees j ON j.id = x2.journee_id
""")
for x in cur.fetchall():
    print(x)

print("\n=== BONUS ===")
cur.execute("""
    SELECT u.prenom, u.nom, b.meilleur_buteur, b.champion, b.points
    FROM bonus b
    JOIN users u ON u.id = b.user_id
""")
for b in cur.fetchall():
    print(b)

print("\n=== RESULTS ===")
cur.execute("""
    SELECT m.equipe_dom, m.equipe_ext, r.score_dom, r.score_ext
    FROM results r
    JOIN matchs m ON m.id = r.match_id
""")
for r in cur.fetchall():
    print(r)

conn.close()
print("\n✅ Lecture de la base terminée")
