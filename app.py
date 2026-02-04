from flask import Flask, render_template, request, redirect, session
from datetime import datetime
from functools import wraps
from mailer import send_mail
from werkzeug.security import check_password_hash, generate_password_hash
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "mpp-secret-key"

# -------------------
# DB UTIL
# -------------------
DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    """Retourne une connexion et un curseur RealDictCursor"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    cursor = conn.cursor()
    return conn, cursor

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
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        prenom = request.form["prenom"]
        nom = request.form["nom"]
        email = request.form["email"]
        password = request.form["password"]

        conn, cursor = db()
        try:
            cursor.execute(
                "INSERT INTO users (prenom, nom, email, password_hash) VALUES (%s, %s, %s, %s)",
                (prenom, nom, email, generate_password_hash(password))
            )
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.close()
            return render_template("register.html", error="Email déjà utilisé")
        conn.close()
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn, cursor = db()
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE email=%s",
            (email,)
        )
        user = cursor.fetchone()
        conn.close()

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
    conn, cursor = db()
    cursor.execute("SELECT * FROM journees ORDER BY id")
    journees = cursor.fetchall()
    conn.close()
    return render_template("home.html", journees=journees)

# -------------------
# JOURNÉE
# -------------------
@app.route("/journee/<int:jid>", methods=["GET", "POST"])
@login_required
def journee(jid):
    conn, cursor = db()
    cursor.execute("SELECT * FROM journees WHERE id=%s", (jid,))
    journee = cursor.fetchone()
    if not journee:
        conn.close()
        return "Journée introuvable", 404

    verrouille = now() >= journee["verrou"]

    # SAVE PRONOS
    if request.method == "POST" and not verrouille:
        cursor.execute("SELECT id FROM matchs WHERE journee_id=%s", (jid,))
        matchs = cursor.fetchall()

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

            cursor.execute("""
                INSERT INTO pronos(user_id, match_id, score_dom, score_ext)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id, match_id)
                DO UPDATE SET score_dom = EXCLUDED.score_dom, score_ext = EXCLUDED.score_ext
            """, (session["user_id"], m["id"], sd, se))

        conn.commit()

        # Email confirmation
        cursor.execute("SELECT prenom, email FROM users WHERE id=%s", (session["user_id"],))
        user = cursor.fetchone()
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

    # MATCHS + PRONOS + RESULTS + POINTS
    cursor.execute("""
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
                WHEN p.score_dom = r.score_dom AND p.score_ext = r.score_ext THEN 3
                WHEN (p.score_dom - p.score_ext) = (r.score_dom - r.score_ext) THEN 2
                WHEN (p.score_dom - p.score_ext) * (r.score_dom - r.score_ext) > 0
                    OR (p.score_dom = p.score_ext AND r.score_dom = r.score_ext) THEN 1
                ELSE 0
            END AS points
        FROM matchs m
        LEFT JOIN pronos p ON p.match_id = m.id AND p.user_id = %s
        LEFT JOIN results r ON r.match_id = m.id
        WHERE m.journee_id = %s
        ORDER BY m.id
    """, (session["user_id"], jid))
    rows = cursor.fetchall()

    # X2
    cursor.execute("SELECT 1 FROM x2 WHERE user_id=%s AND journee_id=%s", (session["user_id"], jid))
    x2_current = cursor.fetchone()
    cursor.execute("""
        SELECT j.id, j.nom
        FROM x2 x
        JOIN journees j ON j.id = x.journee_id
        WHERE x.user_id=%s AND x.journee_id != %s
    """, (session["user_id"], jid))
    x2_other = cursor.fetchone()
    x2_mult = 2 if x2_current else 1

    conn.close()

    return render_template("journee.html",
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
    conn, cursor = db()
    cursor.execute("SELECT verrou FROM journees WHERE id=%s", (jid,))
    verrou = cursor.fetchone()["verrou"]
    if now() < verrou:
        cursor.execute("""
            INSERT INTO x2(user_id, journee_id) VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """, (session["user_id"], jid))
        conn.commit()
    conn.close()
    return redirect(f"/journee/{jid}")

@app.route("/x2/off/<int:jid>", methods=["POST"])
@login_required
def x2_off(jid):
    conn, cursor = db()
    cursor.execute("SELECT verrou FROM journees WHERE id=%s", (jid,))
    verrou = cursor.fetchone()["verrou"]
    if now() < verrou:
        cursor.execute("DELETE FROM x2 WHERE user_id=%s AND journee_id=%s", (session["user_id"], jid))
        conn.commit()
    conn.close()
    return redirect(f"/journee/{jid}")

# -------------------
# BONUS
# -------------------
@app.route("/bonus", methods=["GET", "POST"])
@login_required
def bonus():
    DEBUT_COMPET = datetime(2026, 2, 6, 20, 45)
    verrouille = now() >= DEBUT_COMPET

    conn, cursor = db()
    if request.method == "POST" and not verrouille:
        cursor.execute("""
            INSERT INTO bonus(user_id, meilleur_buteur, champion)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id)
            DO UPDATE SET meilleur_buteur = EXCLUDED.meilleur_buteur,
                          champion = EXCLUDED.champion
        """, (session["user_id"], request.form["buteur"], request.form["champion"]))
        conn.commit()

    cursor.execute("SELECT * FROM bonus WHERE user_id=%s", (session["user_id"],))
    b = cursor.fetchone()
    conn.close()
    return render_template("bonus.html", bonus=b, verrouille=verrouille)

# -------------------
# CLASSEMENT
# -------------------
@app.route("/classement")
@login_required
def classement():
    conn, cursor = db()
    cursor.execute("""
        SELECT
            u.prenom || ' ' || u.nom AS joueur,
            COALESCE(SUM(
                CASE
                    WHEN r.score_dom IS NULL THEN 0
                    WHEN p.score_dom = r.score_dom AND p.score_ext = r.score_ext THEN 3
                    WHEN (p.score_dom - p.score_ext) = (r.score_dom - r.score_ext) THEN 2
                    WHEN (p.score_dom - p.score_ext) * (r.score_dom - r.score_ext) > 0
                        OR (p.score_dom = p.score_ext AND r.score_dom = r.score_ext) THEN 1
                    ELSE 0
                END
            ) * CASE WHEN x.user_id IS NOT NULL THEN 2 ELSE 1 END, 0) AS points_matchs,
            COALESCE(b.points, 0) AS points_bonus,
            COALESCE(SUM(
                CASE
                    WHEN r.score_dom IS NULL THEN 0
                    WHEN p.score_dom = r.score_dom AND p.score_ext = r.score_ext THEN 3
                    WHEN (p.score_dom - p.score_ext) = (r.score_dom - r.score_ext) THEN 2
                    WHEN (p.score_dom - p.score_ext) * (r.score_dom - r.score_ext) > 0
                        OR (p.score_dom = p.score_ext AND r.score_dom = r.score_ext) THEN 1
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
    """)
    rows = cursor.fetchall()
    conn.close()
    return render_template("classement.html", rows=rows)

# -------------------
# RUN
# -------------------
if __name__ == "__main__":
    app.run(debug=True)
