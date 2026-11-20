"""SQLite-tietokanta: taulujen luonti, tallennus ja luku."""

import sqlite3

DB_PATH = "f1.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS constructors (
    constructor_id  TEXT PRIMARY KEY,
    team_name       TEXT NOT NULL,
    nationality     TEXT,
    standing_pos    INTEGER,
    points          REAL,
    wins            INTEGER,
    points_per_race REAL
);
CREATE TABLE IF NOT EXISTS drivers (
    driver_id        TEXT PRIMARY KEY,
    code             TEXT,
    name             TEXT NOT NULL,
    nationality      TEXT,
    birth_date       TEXT,
    age              REAL,
    permanent_number INTEGER,
    constructor_id   TEXT REFERENCES constructors(constructor_id)
);
CREATE TABLE IF NOT EXISTS races (
    round        INTEGER PRIMARY KEY,
    race_name    TEXT NOT NULL,
    circuit_name TEXT,
    country      TEXT,
    locality     TEXT,
    race_date    TEXT
);
CREATE TABLE IF NOT EXISTS race_results (
    round             INTEGER REFERENCES races(round),
    driver_id         TEXT REFERENCES drivers(driver_id),
    constructor_id    TEXT REFERENCES constructors(constructor_id),
    grid              INTEGER,
    position          INTEGER,
    quali_position    INTEGER,
    quali_time_sec    REAL,
    status            TEXT,
    finished          INTEGER,
    laps              INTEGER,
    points            REAL,
    fastest_lap_sec   REAL,
    positions_gained  INTEGER,
    rolling_points_5  REAL,
    cumulative_points REAL,
    PRIMARY KEY (round, driver_id)
);
"""


def get_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def save_all(constructors, drivers, races, race_results, db_path=DB_PATH):
    """Tyhjentää taulut ja tallentaa uuden datan (putki on ajettavissa uudelleen)."""
    conn = get_connection(db_path)
    # Pudotetaan vanhat taulut käänteisessä viitejärjestyksessä
    for table in ("race_results", "drivers", "races", "constructors"):
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.executescript(SCHEMA)
    constructors.to_sql("constructors", conn, if_exists="append", index=False)
    drivers.to_sql("drivers", conn, if_exists="append", index=False)
    races.to_sql("races", conn, if_exists="append", index=False)
    race_results.to_sql("race_results", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()


def load_race_results(db_path=DB_PATH):
    """Hakee kilpailutulokset yhdistettynä kuljettajiin, talleihin ja osakilpailuihin."""
    import pandas as pd

    query = """
        SELECT r.*,
               d.name AS driver_name,
               d.code AS driver_code,
               d.nationality AS driver_nationality,
               d.age,
               d.permanent_number,
               c.team_name,
               c.points AS team_points,
               c.wins AS team_wins,
               c.standing_pos AS team_standing_pos,
               c.points_per_race AS team_points_per_race,
               ra.race_name,
               ra.circuit_name,
               ra.country,
               ra.race_date
        FROM race_results r
        JOIN drivers d ON d.driver_id = r.driver_id
        JOIN constructors c ON c.constructor_id = r.constructor_id
        JOIN races ra ON ra.round = r.round
        ORDER BY r.round, r.position
    """
    conn = get_connection(db_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
