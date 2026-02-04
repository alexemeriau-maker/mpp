from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
from functools import wraps
from mailer import send_mail
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = "mpp-secret-key"
DB = "mpp.db"

# -------------------
# DB
# -------------------

def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def now():
    return datetime.now()

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        return f(*args, **kwargs)
    return wrap

# -------------------
# AUTH
# -------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = db().execute(
            "SELECT id, password_hash FROM users WHERE email=?",
            (email,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            return redirect("/")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# -------------------
# HOME
# -------------------

@app.route("/")
@login_required
def home():
    journees = db().execute(
        "SELECT * FROM journees ORDER BY id"
    ).fetchall()
    return render_template("home.html", journees=journees)

# -------------------
# JOURNÉE
# -------------------

@app.route("/journee/<int:jid>", methods=["GET", "POST"])
@login_required
def journee(jid):
    conn = db()

    journee = conn.execute(
        "SELECT * FROM journees WHERE id=?",
        (jid,)
    ).fetchone()

    if not journee:
        return "Journée introuvable", 404

    verrouille = now() >= datetime.fromisoformat(journee["verrou"])

    # -------------------
    # SAVE PRONOS
    # -------------------
    if request.method == "POST" and not verrouille:
        matchs = conn.execute(
            "SELECT id FROM matchs WHERE journee_id=?",
            (jid,)
        ).fetchall()

        for m in matchs:
            sd = request.form.get(f"dom_{m['id']}")
            se = request.form.get(f"ext_{m['id']}")

            if sd is None or se is None:
                continue

            try:
                sd = int(sd)
                se = int(se)
                if sd < 0 or se < 0:
                    continue
            except ValueError:
                continue

            conn.execute("""
                INSERT OR REPLACE INTO pronos(user_id, match_id, score_dom, score_ext)
                VALUES (?,?,?,?)
            """, (session["user_id"], m["id"], sd, se))

        conn.commit()

        # Email confirmation
        user = conn.execute(
            "SELECT prenom, email FROM users WHERE id=?",
            (session["user_id"],)
        ).fetchone()

        if user and user["email"]:
            send_mail(
                user["email"],
                f"MPP – Pronostics validés ({journee['nom']})",
                f"""Salut {user['prenom']} 👋

        Tes pronostics pour {journee['nom']} ont bien été enregistrés ✅

        ⚽ Tu pourras voir les pronos des autres joueurs après le verrouillage.
        🔥 Pense à utiliser ton bonus X2 si ce n'est pas déjà fait !

        Bonne chance 🍀
        MPP
        """
            )

    # -------------------
    # MATCHS + PRONOS + RESULTS + POINTS
    # -------------------
    rows = conn.execute("""
    SELECT 
        m.id AS match_id,
        m.equipe_dom,
        m.equipe_ext,
        p.score_dom AS prono_dom,
        p.score_ext AS prono_ext,
        r.score_dom AS real_dom,
        r.score_ext AS real_ext,
        CASE
            WHEN r.score_dom IS NULL THEN NULL

            -- 3 pts : score exact
            WHEN p.score_dom = r.score_dom 
            AND p.score_ext = r.score_ext
            THEN 3

            -- 2 pts : bonne différence de buts
            WHEN (p.score_dom - p.score_ext) = (r.score_dom - r.score_ext)
            THEN 2

            -- 1 pt : bonne issue (victoire / nul / défaite)
            WHEN (p.score_dom - p.score_ext) * (r.score_dom - r.score_ext) > 0
                OR (p.score_dom = p.score_ext AND r.score_dom = r.score_ext)
            THEN 1

            ELSE 0
        END AS points
    FROM matchs m
    LEFT JOIN pronos p 
        ON p.match_id = m.id AND p.user_id = ?
    LEFT JOIN results r 
        ON r.match_id = m.id
    WHERE m.journee_id = ?
    ORDER BY m.id
    """, (session["user_id"], jid)).fetchall()

    # -------------------
    # X2
    # -------------------
    x2_current = conn.execute("""
        SELECT 1 FROM x2 WHERE user_id=? AND journee_id=?
    """, (session["user_id"], jid)).fetchone()

    x2_other = conn.execute("""
        SELECT j.id, j.nom
        FROM x2 x
        JOIN journees j ON j.id = x.journee_id
        WHERE x.user_id=? AND x.journee_id != ?
    """, (session["user_id"], jid)).fetchone()

    x2_mult = 2 if x2_current else 1

    return render_template(
        "journee.html",
        journee=journee,
        matchs=rows,
        verrouille=verrouille,
        x2_current=x2_current,
        x2_other=x2_other,
        x2_mult=x2_mult
    )

# -------------------
# X2 ON / OFF
# -------------------

@app.route("/x2/on/<int:jid>", methods=["POST"])
@login_required
def x2_on(jid):
    conn = db()
    verrou = conn.execute(
        "SELECT verrou FROM journees WHERE id=?",
        (jid,)
    ).fetchone()["verrou"]

    if now() < datetime.fromisoformat(verrou):
        conn.execute(
            "INSERT OR IGNORE INTO x2(user_id, journee_id) VALUES (?,?)",
            (session["user_id"], jid)
        )
        conn.commit()

    return redirect(f"/journee/{jid}")

@app.route("/x2/off/<int:jid>", methods=["POST"])
@login_required
def x2_off(jid):
    conn = db()
    verrou = conn.execute(
        "SELECT verrou FROM journees WHERE id=?",
        (jid,)
    ).fetchone()["verrou"]

    if now() < datetime.fromisoformat(verrou):
        conn.execute(
            "DELETE FROM x2 WHERE user_id=? AND journee_id=?",
            (session["user_id"], jid)
        )
        conn.commit()

    return redirect(f"/journee/{jid}")

# -------------------
# BONUS
# -------------------
@app.route("/bonus", methods=["GET", "POST"])
@login_required
def bonus():
    DEBUT_COMPET = datetime(2026, 2, 6, 20, 45)  # date avant laquelle on peut pronostiquer
    verrouille = now() >= DEBUT_COMPET

    conn = db()
    c = conn.cursor()
    if request.method == "POST" and not verrouille:
        # Stocke juste les choix de l'utilisateur
        c.execute("""
            INSERT OR REPLACE INTO bonus(user_id, meilleur_buteur, champion)
            VALUES (?,?,?)
        """, (session["user_id"], request.form["buteur"], request.form["champion"]))
        conn.commit()

    b = c.execute("SELECT * FROM bonus WHERE user_id=?", (session["user_id"],)).fetchone()
    return render_template("bonus.html", bonus=b, verrouille=verrouille)

# -------------------
# CLASSEMENT
# -------------------
@app.route("/classement")
@login_required
def classement():
    conn = db()
    rows = conn.execute("""
        SELECT
            u.prenom || ' ' || u.nom AS joueur,
            COALESCE(SUM(
                CASE
                    WHEN r.score_dom IS NULL THEN 0

                    WHEN p.score_dom = r.score_dom 
                    AND p.score_ext = r.score_ext
                    THEN 3

                    WHEN (p.score_dom - p.score_ext) = (r.score_dom - r.score_ext)
                    THEN 2

                    WHEN (p.score_dom - p.score_ext) * (r.score_dom - r.score_ext) > 0
                        OR (p.score_dom = p.score_ext AND r.score_dom = r.score_ext)
                    THEN 1

                    ELSE 0
                END
            ) * CASE WHEN x.user_id IS NOT NULL THEN 2 ELSE 1 END, 0) AS points_matchs,
            COALESCE(b.points, 0) AS points_bonus,
            COALESCE(SUM(
                CASE
                    WHEN r.score_dom IS NULL THEN 0

                    WHEN p.score_dom = r.score_dom 
                    AND p.score_ext = r.score_ext
                    THEN 3

                    WHEN (p.score_dom - p.score_ext) = (r.score_dom - r.score_ext)
                    THEN 2

                    WHEN (p.score_dom - p.score_ext) * (r.score_dom - r.score_ext) > 0
                        OR (p.score_dom = p.score_ext AND r.score_dom = r.score_ext)
                    THEN 1

                    ELSE 0
                END
            ) * CASE WHEN x.user_id IS NOT NULL THEN 2 ELSE 1 END, 0) + COALESCE(b.points, 0) AS total
        FROM users u
        LEFT JOIN pronos p ON u.id = p.user_id
        LEFT JOIN results r ON p.match_id = r.match_id
        LEFT JOIN matchs m ON p.match_id = m.id
        LEFT JOIN x2 x ON x.user_id = u.id AND x.journee_id = m.journee_id
        LEFT JOIN bonus b ON b.user_id = u.id
        GROUP BY u.id
        ORDER BY total DESC
    """).fetchall()
    return render_template("classement.html", rows=rows)

# -------------------
# RUN
# -------------------

if __name__ == "__main__":
    app.run(debug=True)
