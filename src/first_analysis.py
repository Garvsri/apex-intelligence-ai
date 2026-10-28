
from pathlib import Path

import requests
import pandas as pd
import plotly.express as px

BASE_URL = "https://api.openf1.org/v1"
ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def fetch_data(endpoint, params):
    """Fetch historical F1 data from OpenF1."""
    response = requests.get(
        f"{BASE_URL}/{endpoint}",
        params=params,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


print("Finding the 2024 British Grand Prix race...")

sessions = fetch_data(
    "sessions",
    {
        "year": 2024,
        "country_name": "United Kingdom",
        "session_name": "Race",
    },
)

if not sessions:
    raise RuntimeError("No matching race session found.")

session = next(
    (
        s for s in sessions
        if s.get("circuit_short_name") == "Silverstone"
    ),
    None,
)

if session is None:
    raise RuntimeError("Silverstone race session not found.")

session_key = session["session_key"]

print(f"Race: {session['session_name']}")
print(f"Circuit: {session['circuit_short_name']}")
print(f"Session key: {session_key}")
print("Downloading lap data...")

laps_data = fetch_data(
    "laps",
    {"session_key": session_key},
)

if not laps_data:
    raise RuntimeError("No lap data returned by OpenF1.")

laps = pd.DataFrame(laps_data)

# Get driver names for readable charts
drivers_data = fetch_data(
    "drivers",
    {"session_key": session_key},
)

drivers = pd.DataFrame(drivers_data)

if not drivers.empty:
    drivers = drivers[
        ["driver_number", "full_name", "name_acronym"]
    ].drop_duplicates(subset=["driver_number"])

    laps = laps.merge(
        drivers,
        on="driver_number",
        how="left",
    )

    laps["Driver"] = laps["name_acronym"].fillna(
        laps["driver_number"].astype(str)
    )
else:
    laps["Driver"] = laps["driver_number"].astype(str)

# Keep useful fields that are available
useful_columns = [
    "Driver",
    "driver_number",
    "lap_number",
    "lap_duration",
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
    "is_pit_out_lap",
]

available = [
    col for col in useful_columns if col in laps.columns
]

laps = laps[available].copy()

laps["lap_duration"] = pd.to_numeric(
    laps["lap_duration"], errors="coerce"
)

laps = laps.dropna(subset=["lap_duration"])

# Exclude pit-out laps and unusually long laps
if "is_pit_out_lap" in laps.columns:
    laps = laps[laps["is_pit_out_lap"] != True]

laps = laps[laps["lap_duration"] < 200]

csv_path = OUTPUT_DIR / "british_gp_2024_laps.csv"
laps.to_csv(csv_path, index=False)

print(f"\nValid lap records: {len(laps)}")
print(f"Dataset saved to: {csv_path}")

# Compare Max Verstappen and Lewis Hamilton
# Analyze all drivers with available lap data
comparison = laps.copy()

if comparison.empty:
    print("VER/HAM data unavailable; showing available drivers.")
    print(laps["Driver"].unique())
else:
    print("\nAverage lap time (seconds):")
    print(
        comparison.groupby("Driver")["lap_duration"]
        .mean()
        .round(3)
    )

    fig = px.line(
        comparison,
        x="lap_number",
        y="lap_duration",
        color="Driver",
        markers=True,
        title="2024 British GP — Lap-Time Comparison",
        labels={
            "lap_number": "Lap Number",
            "lap_duration": "Lap Time (seconds)",
            "Driver": "Driver",
        },
    )

    chart_path = OUTPUT_DIR / "lap_comparison.html"
    fig.write_html(str(chart_path))

    print(f"\nChart saved to: {chart_path}")
    print("Open the HTML chart in your browser.")
