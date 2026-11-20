"""Datan muuntaminen: siivous, rikastus ja uusien muuttujien laskeminen."""

import pandas as pd


def lap_time_to_seconds(lap_time):
    """Muuttaa kierrosajan '1:20.450' -> 80.45 sekuntia."""
    try:
        minutes, seconds = lap_time.split(":")
        return round(int(minutes) * 60 + float(seconds), 3)
    except (AttributeError, ValueError):
        return None


def transform_constructors(raw_constructors, total_races=24):
    """Muuntaa tallien MM-sarjataulukon ja laskee pistekeskiarvon per kilpailu."""
    rows = []
    for c in raw_constructors:
        info = c["Constructor"]
        pos = c.get("position") or c.get("positionText")
        rows.append(
            {
                "constructor_id": info["constructorId"],
                "team_name": info["name"],
                "nationality": info.get("nationality"),
                "standing_pos": int(pos) if str(pos).isdigit() else None,
                "points": float(c.get("points", 0)),
                "wins": int(c.get("wins", 0)),
            }
        )
    df = pd.DataFrame(rows).drop_duplicates("constructor_id")
    # Laskettu muuttuja: tallin pistekeskiarvo per osakilpailu
    races_count = max(int(total_races), 1)
    df["points_per_race"] = (df["points"] / races_count).round(2)
    return df


def transform_drivers(raw_drivers, today=None):
    """Muuntaa kuljettajaprofiilit ja laskee kuljettajan iän."""
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.today()
    rows = []
    for item in raw_drivers:
        d = item.get("Driver", item)
        constructors = item.get("Constructors", [])
        team_id = constructors[-1]["constructorId"] if constructors else d.get("constructorId")
        birth = pd.to_datetime(d.get("dateOfBirth"), errors="coerce")
        num = d.get("permanentNumber")
        rows.append(
            {
                "driver_id": d["driverId"],
                "code": d.get("code") or d["familyName"][:3].upper(),
                "name": f"{d['givenName']} {d['familyName']}",
                "nationality": d.get("nationality"),
                "birth_date": d.get("dateOfBirth"),
                "age": round((today - birth).days / 365.25, 1) if pd.notna(birth) else None,
                "permanent_number": int(num) if str(num).isdigit() else None,
                "constructor_id": team_id,
            }
        )
    return pd.DataFrame(rows).drop_duplicates("driver_id")


def transform_races(raw_races):
    """Muuntaa kauden osakilpailut ja ratatiedot."""
    rows = []
    for r in raw_races:
        circuit = r.get("Circuit", {})
        loc = circuit.get("Location", {})
        rows.append(
            {
                "round": int(r["round"]),
                "race_name": r["raceName"],
                "circuit_name": circuit.get("circuitName"),
                "country": loc.get("country"),
                "locality": loc.get("locality"),
                "race_date": r.get("date"),
            }
        )
    return pd.DataFrame(rows).drop_duplicates("round").sort_values("round").reset_index(drop=True)


def _build_qualifying_lookup(raw_qualifying):
    """Rakentaa (round, driver_id) -> (quali_position, quali_time_sec) -hakemiston."""
    lookup = {}
    for race in raw_qualifying or []:
        rnd = int(race["round"])
        for q in race.get("QualifyingResults", []):
            driver_id = q["Driver"]["driverId"]
            pos = int(q["position"]) if str(q.get("position", "")).isdigit() else None
            best_str = q.get("Q3") or q.get("Q2") or q.get("Q1")
            lookup[(rnd, driver_id)] = (pos, lap_time_to_seconds(best_str))
    return lookup


def transform_race_results(raw_results, raw_qualifying=None):
    """Muuntaa ja siivoaa kilpailutulokset sekä rikastaa ne aika-ajodatalla."""
    quali_lookup = _build_qualifying_lookup(raw_qualifying)
    rows = []
    for race in raw_results:
        rnd = int(race["round"])
        for res in race.get("Results", []):
            driver_id = res["Driver"]["driverId"]
            constructor_id = res["Constructor"]["constructorId"]
            raw_grid = int(res.get("grid", 0))
            # Jos kuljettaja lähtee varikolta (grid == 0), käytetään lähtöruutuna 20
            grid = 20 if raw_grid == 0 else raw_grid
            pos_str = res.get("position")
            position = int(pos_str) if str(pos_str).isdigit() else None
            status = res.get("status", "")
            finished = 1 if (status == "Finished" or status.startswith("+")) else 0
            fastest_str = ((res.get("FastestLap") or {}).get("Time") or {}).get("time")
            quali_pos, quali_sec = quali_lookup.get((rnd, driver_id), (None, None))

            rows.append(
                {
                    "round": rnd,
                    "driver_id": driver_id,
                    "constructor_id": constructor_id,
                    "grid": grid,
                    "position": position,
                    "quali_position": quali_pos if quali_pos is not None else grid,
                    "quali_time_sec": quali_sec,
                    "status": status,
                    "finished": finished,
                    "laps": int(res.get("laps", 0)),
                    "points": float(res.get("points", 0)),
                    "fastest_lap_sec": lap_time_to_seconds(fastest_str),
                }
            )

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    # Siivous: duplikaatit ja puuttuvat maalisijoitukset
    before = len(df)
    df = df.drop_duplicates(["round", "driver_id"])
    df = df.dropna(subset=["position"])
    df["position"] = df["position"].astype(int)
    print(f"Siivous: poistettiin {before - len(df)} riviä (duplikaatit / puuttuva sijoitus)")

    # Uudet laskennalliset muuttujat
    df = df.sort_values(["driver_id", "round"]).reset_index(drop=True)
    df["positions_gained"] = df["grid"] - df["position"]
    df["rolling_points_5"] = (
        df.groupby("driver_id")["points"]
        .transform(lambda s: s.rolling(5, min_periods=1).mean())
        .round(2)
    )
    df["cumulative_points"] = df.groupby("driver_id")["points"].cumsum()
    return df
