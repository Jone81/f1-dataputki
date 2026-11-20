"""Testit hakumoduulille (requests.get korvataan feikillä, ei oikeita API-kutsuja)."""

import pytest

from src import extract


class FeikkiVastaus:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


@pytest.fixture(autouse=True)
def ei_odotuksia(monkeypatch):
    """Ohitetaan time.sleep, jotta testit pysyvät nopeina."""
    monkeypatch.setattr(extract.time, "sleep", lambda s: None)


def test_get_json_palauttaa_jsonin(monkeypatch):
    monkeypatch.setattr(extract.requests, "get", lambda url, timeout: FeikkiVastaus(200, {"a": 1}))
    assert extract.get_json("testi") == {"a": 1}


def test_get_json_yrittaa_uudelleen_429_virheella(monkeypatch):
    vastaukset = [FeikkiVastaus(429), FeikkiVastaus(429), FeikkiVastaus(200, {"ok": True})]
    kutsut = []

    def feikki_get(url, timeout):
        kutsut.append(url)
        return vastaukset[len(kutsut) - 1]

    monkeypatch.setattr(extract.requests, "get", feikki_get)
    assert extract.get_json("testi") == {"ok": True}
    assert len(kutsut) == 3


def test_get_json_nostaa_virheen_muista_virhekoodeista(monkeypatch):
    monkeypatch.setattr(extract.requests, "get", lambda url, timeout: FeikkiVastaus(500))
    with pytest.raises(RuntimeError):
        extract.get_json("testi")


def test_fetch_race_results_kokoaa_sivutetut_tulokset(monkeypatch):
    sivut = [
        {
            "MRData": {
                "total": "150",
                "RaceTable": {"Races": [{"round": "1"}]},
            }
        },
        {
            "MRData": {
                "total": "150",
                "RaceTable": {"Races": [{"round": "2"}]},
            }
        },
    ]
    kutsut = []

    def feikki_get_json(path):
        kutsut.append(path)
        return sivut[len(kutsut) - 1]

    monkeypatch.setattr(extract, "get_json", feikki_get_json)
    kisat = extract.fetch_race_results(2025)
    assert [r["round"] for r in kisat] == ["1", "2"]
    assert len(kutsut) == 2
