"""Ajaa dataputken: Extract -> Transform -> Load (f1.db)."""

from src import database, extract, transform


def main(season=extract.DEFAULT_SEASON):
    print(f"1/3 Haetaan kauden {season} data F1 API:sta...")
    raw_constructors = extract.fetch_constructors(season)
    raw_drivers = extract.fetch_drivers(season)
    raw_races = extract.fetch_races(season)
    raw_results = extract.fetch_race_results(season)
    raw_qualifying = extract.fetch_qualifying(season)

    print("2/3 Muunnetaan, rikastetaan ja siivotaan...")
    races = transform.transform_races(raw_races)
    constructors = transform.transform_constructors(raw_constructors, total_races=len(races))
    drivers = transform.transform_drivers(raw_drivers)
    race_results = transform.transform_race_results(raw_results, raw_qualifying)
    print(
        f"  {len(constructors)} tallia, {len(drivers)} kuljettajaa, "
        f"{len(races)} osakilpailua"
    )

    print("3/3 Tallennetaan SQLiteen...")
    database.save_all(constructors, drivers, races, race_results)
    print(f"Valmis: {len(race_results)} kilpailutulosriviä tallennettu tietokantaan ({database.DB_PATH}).")


if __name__ == "__main__":
    main()
