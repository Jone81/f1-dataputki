"""Datan sisäänluku: hakee Formula 1 -kauden datan avoimesta Jolpica/Ergast F1 API:sta."""

import time

import requests

BASE_URL = "https://api.jolpi.ca/ergast/f1"
DEFAULT_SEASON = 2025


def get_json(path) -> dict:
    """Hakee yhden API-reitin ja palauttaa JSON:n."""
    for attempt in range(6):
        response = requests.get(f"{BASE_URL}/{path}", timeout=15)
        if response.status_code == 429:  # liikaa pyyntöjä -> odotetaan ja yritetään uudelleen
            time.sleep(5 * (attempt + 1))
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"API palautti toistuvasti virheen 429 (liikaa pyyntöjä): {path}")


def fetch_constructors(season=DEFAULT_SEASON):
    """Tallit ja tallien MM-sarjataulukko."""
    data = get_json(f"{season}/constructorstandings.json")
    lists = data["MRData"]["StandingsTable"]["StandingsLists"]
    return lists[0]["ConstructorStandings"] if lists else []


def fetch_drivers(season=DEFAULT_SEASON):
    """Kuljettajat, profiilitiedot ja MM-pistetilanne."""
    data = get_json(f"{season}/driverstandings.json")
    lists = data["MRData"]["StandingsTable"]["StandingsLists"]
    return lists[0]["DriverStandings"] if lists else []


def fetch_races(season=DEFAULT_SEASON):
    """Kauden osakilpailut ja ratatiedot."""
    data = get_json(f"{season}/races.json?limit=100")
    return data["MRData"]["RaceTable"]["Races"]


def _fetch_paginated_races(endpoint, season=DEFAULT_SEASON):
    """Hakee sivutetun kisadatan (esim. results tai qualifying) kaikki sivut."""
    races = []
    offset = 0
    limit = 100
    while True:
        data = get_json(f"{season}/{endpoint}.json?limit={limit}&offset={offset}")
        mr_data = data["MRData"]
        batch = mr_data["RaceTable"]["Races"]
        if not batch:
            break
        races.extend(batch)
        offset += limit
        if offset >= int(mr_data.get("total", 0)):
            break
        time.sleep(0.3)  # ollaan kohteliaita API:a kohtaan
    return races


def fetch_race_results(season=DEFAULT_SEASON):
    """Kaikkien osakilpailujen kilpailutulokset."""
    return _fetch_paginated_races("results", season)


def fetch_qualifying(season=DEFAULT_SEASON):
    """Aika-ajotulokset toisesta API-reitistä datan rikastamista varten."""
    return _fetch_paginated_races("qualifying", season)
