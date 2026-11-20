"""Streamlit + Plotly -visualisointisovellus: Formula 1 -kausi 2025 (data SQLitestä)."""

import plotly.express as px
import streamlit as st

from src.database import load_race_results

st.set_page_config(page_title="Formula 1 -kausi 2025", layout="wide")

# Sarakkeiden suomenkieliset nimet kaavioihin ja taulukkoon
NIMET = {
    "driver_name": "Kuljettaja",
    "driver_code": "Lyhenne",
    "team_name": "Talli",
    "races": "Osakilpailut",
    "avg_grid": "Keskim. lähtöruutu",
    "avg_quali": "Keskim. aika-ajosijoitus",
    "avg_pos": "Keskim. maalisijoitus",
    "points": "Pisteet",
    "laps": "Ajetut kierrokset",
    "avg_gained": "Keskim. sijoitusmuutos (nousut/pudotukset)",
    "finish_rate_pct": "Maaliinajoprosentti (%)",
    "age": "Ikä (v)",
    "team_points": "Tallin kokonaispisteet",
    "points_share_pct": "Osuus tallin pisteistä (%)",
    "race_date": "Päivämäärä",
    "race_name": "Osakilpailu",
    "round": "Kierros",
    "value": "Pisteet",
    "variable": "Mittari",
}


@st.cache_data
def hae_data():
    return load_race_results()


df = hae_data()

st.title("Formula 1 – kauden 2025 tilastot ja suorituskykyanalyysi")

# Sivupalkin suodattimet
tallit = ["Kaikki tallit"] + sorted(df["team_name"].unique())
valittu_talli = st.sidebar.selectbox("Suodata tallin mukaan", tallit)
max_kisat = int(df.groupby("driver_id").size().to_numpy().max())
min_kisat = st.sidebar.slider("Vähimmäismäärä osakilpailuja", 1, max_kisat, 5)
kuljettaja = st.sidebar.selectbox(
    "Kuljettaja (kuntopuntari)",
    sorted(df["driver_name"].unique()),
)

# Tallisuodatus
data = df if valittu_talli == "Kaikki tallit" else df[df["team_name"] == valittu_talli]

# Kaavio 1: keskimääräinen lähtöruutu vs. pisteet
yhteenveto = data.groupby(["driver_name", "team_name"], as_index=False).agg(
    races=("round", "count"),
    avg_grid=("grid", "mean"),
    avg_quali=("quali_position", "mean"),
    avg_pos=("position", "mean"),
    points=("points", "sum"),
    laps=("laps", "sum"),
    avg_gained=("positions_gained", "mean"),
    finish_rate_pct=("finished", lambda s: round(s.mean() * 100, 1)),
)
yhteenveto = yhteenveto.loc[yhteenveto["races"] >= min_kisat]
yhteenveto["avg_grid"] = yhteenveto["avg_grid"].round(2)
yhteenveto["avg_quali"] = yhteenveto["avg_quali"].round(2)
yhteenveto["avg_pos"] = yhteenveto["avg_pos"].round(2)
yhteenveto["avg_gained"] = yhteenveto["avg_gained"].round(2)

kaavio1 = px.scatter(
    yhteenveto,
    x="avg_grid",
    y="points",
    size="laps",
    color="team_name",
    hover_name="driver_name",
    hover_data=["races", "avg_pos", "finish_rate_pct"],
    labels=NIMET,
    title="Keskimääräinen lähtöruutu vs. MM-pisteet (pallon koko = ajetut kierrokset)",
)
st.plotly_chart(kaavio1, width="stretch")

# Kaavio 2: valitun kuljettajan kuntopuntari
kuljettajan_data = df.loc[df["driver_name"] == kuljettaja].sort_values("round")
kaavio2 = px.line(
    kuljettajan_data,
    x="race_date",
    y=["cumulative_points", "rolling_points_5"],
    hover_name="race_name",
    markers=True,
    labels=NIMET,
    title=f"{kuljettaja}: MM-pistekertymä ja 5 osakilpailun liukuva pistekeskiarvo",
)
kaavio2.update_xaxes(tickformat="%d.%m.%Y", hoverformat="%d.%m.%Y")
kaavio2.for_each_trace(
    lambda t: t.update(
        name={
            "cumulative_points": "Kumulatiivinen pistekertymä",
            "rolling_points_5": "5 kilpailun liukuva keskiarvo",
        }[t.name],
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "Päivämäärä: %{x|%d.%m.%Y}<br>"
            + (
                "Pistekertymä: %{y}<extra></extra>"
                if t.name == "cumulative_points"
                else "5 kilpailun liukuva keskiarvo: %{y:.2f}<extra></extra>"
            )
        ),
    )
)
st.plotly_chart(kaavio2, width="stretch")

# Kaavio 3: rikastettu profiili & aika-ajodata – aika-ajosijoitus vs. sijoitusmuutos kisassa
profiili = data.groupby(["driver_name", "team_name"], as_index=False).agg(
    age=("age", "first"),
    avg_quali=("quali_position", "mean"),
    avg_gained=("positions_gained", "mean"),
    points=("points", "sum"),
    races=("round", "count"),
)
profiili = profiili.loc[profiili["races"] >= min_kisat]
profiili["avg_quali"] = profiili["avg_quali"].round(2)
profiili["avg_gained"] = profiili["avg_gained"].round(2)

kaavio3 = px.scatter(
    profiili,
    x="avg_quali",
    y="avg_gained",
    color="team_name",
    size="age",
    hover_name="driver_name",
    hover_data=["age", "points"],
    labels=NIMET,
    title="Aika-ajosijoitus vs. sijoitusmuutos kisassa (pallon koko = kuljettajan ikä)",
)
kaavio3.add_hline(y=0, line_dash="dash", line_color="gray")
st.plotly_chart(kaavio3, width="stretch")

# Kaavio 4: tallikonteksti – kuljettajan osuus tallinsa kokonaispisteistä
osuus = data.groupby(["driver_name", "team_name"], as_index=False).agg(
    points=("points", "sum"),
    team_points=("team_points", "first"),
    races=("round", "count"),
)
osuus = osuus.loc[(osuus["races"] >= min_kisat) & (osuus["team_points"] > 0)]
osuus["points_share_pct"] = (osuus["points"] / osuus["team_points"] * 100).round(1)

kaavio4 = px.bar(
    osuus.sort_values("points_share_pct", ascending=False).head(15),
    x="driver_name",
    y="points_share_pct",
    color="team_name",
    hover_data=["points", "team_points", "races"],
    labels=NIMET,
    title="Kuljettajan osuus tallin MM-pisteistä (%, 15 parasta)",
)
st.plotly_chart(kaavio4, width="stretch")

with st.expander("Näytä data taulukkona"):
    st.dataframe(yhteenveto.rename(columns=NIMET))
