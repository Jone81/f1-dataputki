"""Testit muunnosfunktioille (ei vaadi verkkoyhteyttä)."""

from src.transform import (
    lap_time_to_seconds,
    transform_constructors,
    transform_drivers,
    transform_race_results,
)


def tee_kisa(round_nro, driver_id="norris", points=25, grid=2, position: str | None = "1"):
    """Apufunktio: yksi osakilpailu tuloksineen API:n muodossa."""
    return {
        "round": str(round_nro),
        "Results": [
            {
                "Driver": {"driverId": driver_id},
                "Constructor": {"constructorId": "mclaren"},
                "grid": str(grid),
                "position": position,
                "status": "Finished",
                "laps": "58",
                "points": str(points),
                "FastestLap": {"Time": {"time": "1:20.500"}},
            }
        ],
    }


def test_lap_time_to_seconds_muuntaa_sekunneiksi():
    assert lap_time_to_seconds("1:20.450") == 80.45


def test_lap_time_to_seconds_virheellinen_arvo_palauttaa_none():
    assert lap_time_to_seconds(None) is None
    assert lap_time_to_seconds("abc") is None


def test_race_results_poistaa_duplikaatit():
    kisat = [tee_kisa(1), tee_kisa(1)]
    df = transform_race_results(kisat)
    assert len(df) == 1


def test_race_results_poistaa_rivit_ilman_sijoitusta():
    kisat = [tee_kisa(1, position="1"), tee_kisa(2, position=None)]
    df = transform_race_results(kisat)
    assert list(df["round"]) == [1]


def test_race_results_sijoitusmuutos_ja_varikkolahto():
    # grid=0 (varikkolähtö) -> käytetään lähtöruutuna 20, jolloin nousu sijalle 10 on +10
    kisat = [tee_kisa(1, grid=5, position="2"), tee_kisa(2, grid=0, position="10")]
    df = transform_race_results(kisat)
    assert list(df["positions_gained"]) == [3, 10]


def test_race_results_liukuva_keskiarvo():
    pisteet = [10, 0, 20, 10, 0, 25]
    kisat = [tee_kisa(i, points=p) for i, p in enumerate(pisteet, start=1)]
    df = transform_race_results(kisat)
    odotettu = [10.0, 5.0, 10.0, 10.0, 8.0, 11.0]
    assert list(df["rolling_points_5"]) == odotettu


def test_race_results_kumulatiiviset_pisteet_kuljettajittain():
    kisat = [
        tee_kisa(1, driver_id="norris", points=18),
        tee_kisa(2, driver_id="norris", points=25),
        tee_kisa(1, driver_id="piastri", points=15),
    ]
    df = transform_race_results(kisat)
    assert list(df[df["driver_id"] == "norris"]["cumulative_points"]) == [18.0, 43.0]
    assert list(df[df["driver_id"] == "piastri"]["cumulative_points"]) == [15.0]


def test_race_results_rikastaa_aika_ajodatalla():
    kisat = [tee_kisa(1, driver_id="norris", grid=3, position="1")]
    aika_ajot = [
        {
            "round": "1",
            "QualifyingResults": [
                {
                    "Driver": {"driverId": "norris"},
                    "position": "1",
                    "Q1": "1:16.000",
                    "Q2": "1:15.500",
                    "Q3": "1:15.000",
                }
            ],
        }
    ]
    df = transform_race_results(kisat, aika_ajot)
    assert df.loc[0, "quali_position"] == 1
    assert df.loc[0, "quali_time_sec"] == 75.0


def test_drivers_laskee_ian():
    raaka = [
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
    ]
    df = transform_drivers(raaka, today="2025-11-13")
    assert df.loc[0, "age"] == 26.0
    assert df.loc[0, "permanent_number"] == 4


def test_constructors_laskee_pisteet_per_kilpailu():
    raaka = [
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
    ]
    df = transform_constructors(raaka, total_races=24)
    assert df.loc[0, "points_per_race"] == 25.0
