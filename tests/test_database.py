"""Testit tietokantamoduulille (väliaikainen SQLite-tiedosto)."""

import sqlite3

import pytest

from src import database
from src.transform import (
    transform_constructors,
    transform_drivers,
    transform_race_results,
    transform_races,
)


def tee_testidata():
    tallit = transform_constructors(
        [
            {
                "position": "1",
                "points": "600",
                "wins": "8",
                "Constructor": {
                    "constructorId": "mclaren",
                    "name": "McLaren",
                    "nationality": "British",
                },
            }
        ],
        total_races=3,
    )
    kuljettajat = transform_drivers(
        [
            {
                "Driver": {
                    "driverId": "norris",
                    "code": "NOR",
                    "givenName": "Lando",
                    "familyName": "Norris",
                    "dateOfBirth": "1999-11-13",
                    "nationality": "British",
                    "permanentNumber": "4",
                },
                "Constructors": [{"constructorId": "mclaren"}],
            }
        ],
        today="2025-11-13",
    )
    osakilpailut = transform_races(
        [
            {
                "round": str(n),
                "raceName": f"Grand Prix {n}",
                "date": f"2025-03-0{n}",
                "Circuit": {
                    "circuitName": f"Circuit {n}",
                    "Location": {"country": "Australia", "locality": "Melbourne"},
                },
            }
            for n in (1, 2, 3)
        ]
    )
    tulokset = transform_race_results(
        [
            {
                "round": str(n),
                "Results": [
                    {
                        "Driver": {"driverId": "norris"},
                        "Constructor": {"constructorId": "mclaren"},
                        "grid": "2",
                        "position": "1",
                        "status": "Finished",
                        "laps": "58",
                        "points": "25",
                        "FastestLap": {"Time": {"time": "1:20.000"}},
                    }
                ],
            }
            for n in (1, 2, 3)
        ]
    )
    return tallit, kuljettajat, osakilpailut, tulokset


@pytest.fixture
def tietokanta(tmp_path):
    polku = str(tmp_path / "testi.db")
    database.save_all(*tee_testidata(), db_path=polku)
    return polku


def test_save_all_luo_kaikki_taulut(tietokanta):
    conn = sqlite3.connect(tietokanta)
    taulut = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert {"constructors", "drivers", "races", "race_results"} <= taulut


def test_load_race_results_palauttaa_rivit_ja_sarakkeet(tietokanta):
    df = database.load_race_results(tietokanta)
    assert len(df) == 3
    for sarake in ("driver_name", "team_name", "age", "race_name", "positions_gained", "rolling_points_5"):
        assert sarake in df.columns


def test_viiteavain_estaa_tuntemattoman_tallin(tietokanta):
    conn = database.get_connection(tietokanta)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO drivers (driver_id, name, constructor_id) VALUES ('testi', 'Testi Kuski', 'tuntematon')"
        )
    conn.close()


def test_uudelleenajo_ei_kasvata_rivimaaraa(tietokanta):
    database.save_all(*tee_testidata(), db_path=tietokanta)
    assert len(database.load_race_results(tietokanta)) == 3
