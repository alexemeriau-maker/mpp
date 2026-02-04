import sqlite3

DB = "mpp.db"

def show_matchs(journee_id):
    """Affiche les matchs d'une journée"""
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    matchs = c.execute("""
        SELECT id, equipe_dom, equipe_ext
        FROM matchs
        WHERE journee_id=?
        ORDER BY id
    """, (journee_id,)).fetchall()

    conn.close()

    if not matchs:
        print("❌ Aucun match pour cette journée")
        return []

    print(f"\n📅 Journée {journee_id}")
    for m in matchs:
        print(f"ID {m['id']} : {m['equipe_dom']} vs {m['equipe_ext']}")
    return matchs


def set_results(journee_id, results_dict):
    """Insère les résultats réels"""
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    for match_id, (sd, se) in results_dict.items():
        c.execute("""
            INSERT OR REPLACE INTO results (match_id, score_dom, score_ext)
            VALUES (?, ?, ?)
        """, (match_id, sd, se))

    conn.commit()
    conn.close()

    print(f"\n✅ Résultats enregistrés pour la J{journee_id}")


def main():
    # 🔴 À MODIFIER ICI
    journee_id = 1

    matchs = show_matchs(journee_id)
    if not matchs:
        return

    # 🧪 RÉSULTATS (exemple)
    # ➜ match_id : (score_dom, score_ext)
    results = {
        matchs[0]["id"]: (0, 0),
        matchs[1]["id"]: (0, 0),
        matchs[2]["id"]: (0, 0),
        matchs[3]["id"]: (0, 0),
    }

    set_results(journee_id, results)


if __name__ == "__main__":
    main()
