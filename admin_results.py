import os
import psycopg2
from psycopg2.extras import RealDictCursor

# ------------------------
# --- Connexion PostgreSQL ---
# ------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
c = conn.cursor()

def show_matchs(journee_id):
    """Affiche les matchs d'une journée"""
    c.execute("""
        SELECT id, equipe_dom, equipe_ext
        FROM matchs
        WHERE journee_id=%s
        ORDER BY id
    """, (journee_id,))
    matchs = c.fetchall()

    if not matchs:
        print("❌ Aucun match pour cette journée")
        return []

    print(f"\n📅 Journée {journee_id}")
    for m in matchs:
        print(f"ID {m['id']} : {m['equipe_dom']} vs {m['equipe_ext']}")
    return matchs

def set_results(journee_id, results_dict):
    """Insère ou met à jour les résultats réels"""
    for match_id, (sd, se) in results_dict.items():
        c.execute("""
            INSERT INTO results (match_id, score_dom, score_ext)
            VALUES (%s, %s, %s)
            ON CONFLICT (match_id)
            DO UPDATE SET score_dom = EXCLUDED.score_dom,
                          score_ext = EXCLUDED.score_ext
        """, (match_id, sd, se))

    conn.commit()
    print(f"\n✅ Résultats enregistrés pour la J{journee_id}")

def main():
    # 🔴 À MODIFIER ICI
    journee_id = 1

    matchs = show_matchs(journee_id)
    if not matchs:
        return

    # 🧪 RÉSULTATS (exemple)
    # ➜ match_id : (score_dom, score_ext)
    results = { matchs[0]["id"]: (0, 0),
                matchs[1]["id"]: (0, 0), 
                matchs[2]["id"]: (0, 0), 
                matchs[3]["id"]: (0, 0) }
    set_results(journee_id, results)

if __name__ == "__main__":
    main()
