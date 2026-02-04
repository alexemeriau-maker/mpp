DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS journees;
DROP TABLE IF EXISTS matchs;
DROP TABLE IF EXISTS pronos;
DROP TABLE IF EXISTS bonus;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE journees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT,
    date_debut DATETIME,
    verrou DATETIME
);

CREATE TABLE matchs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    journee_id INTEGER,
    equipe_dom TEXT,
    equipe_ext TEXT
);

CREATE TABLE pronos (
    user_id INTEGER,
    match_id INTEGER,
    score_dom INTEGER,
    score_ext INTEGER,
    PRIMARY KEY(user_id, match_id)
);

CREATE TABLE bonus (
    user_id INTEGER PRIMARY KEY,
    meilleur_buteur TEXT,
    champion TEXT,
    points INTEGER DEFAULT 0
);
