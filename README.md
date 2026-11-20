# Formula 1 -kausi 2025 – dataputki

Dataputki Formula 1:n avoimesta API:sta (`api.jolpi.ca/ergast/f1`) SQLite-tietokantaan ja Streamlit + Plotly -visualisointiin.

## Rakenne
- `src/extract.py` – hakee tallien MM-pistetilanteen (`constructorstandings`), kuljettajat (`driverstandings`), osakilpailut (`races`), kilpailutulokset (`results`) ja aika-ajotulokset (`qualifying`)
- `src/transform.py` – siivous (duplikaatit, tyhjät sijoitukset, varikkolähdöt), datan rikastus aika-ajotuloksilla ja laskennalliset muuttujat (kierrosaika sekunteina, sijoitusmuutos kisassa, 5 kilpailun liukuva pistekeskiarvo, kumulatiivinen pistekertymä, kuljettajan ikä, tallin pistekeskiarvo/kilpailu)
- `src/database.py` – SQLite-skeema (`constructors`, `drivers`, `races`, `race_results`) sekä tallennus ja `JOIN`-lukukysely
- `main.py` – ajaa dataputken (Extract → Transform → Load)
- `app.py` – interaktiivinen Streamlit-sovellus

## Käyttö
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py          # luo f1.db
streamlit run app.py
```

## Testit
```bash
pip install -r requirements-dev.txt
python -m pytest
```
- `tests/test_transform.py` – muunnosfunktiot (kierrosaika, siivous, liukuva keskiarvo, kumulatiiviset pisteet, sijoitusmuutos, ikä, tallin pistekeskiarvo)
- `tests/test_database.py` – taulujen luonti, `JOIN`-kysely, viiteavaimet ja uudelleenajo (väliaikainen SQLite-tiedosto)
- `tests/test_extract.py` – haku, sivutus ja 429-uudelleenyritys (feikkivastaukset, ei oikeita API-kutsuja)
