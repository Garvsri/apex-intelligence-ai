
import pandas as pd
import pytest

from apex.ingestion import normalize_fastf1_laps


def test_normalize_fastf1_laps():
    source = pd.DataFrame({
        "Driver": ["ham", "VER"],
        "DriverNumber": ["44", "1"],
        "LapNumber": [1, 1],
        "LapTime": [
            pd.Timedelta(90, unit="s"),
            pd.Timedelta(91, unit="s"),
        ],
        "Sector1Time": [
            pd.Timedelta(30, unit="s"),
            pd.Timedelta(31, unit="s"),
        ],
        "Sector2Time": [
            pd.Timedelta(35, unit="s"),
            pd.Timedelta(35, unit="s"),
        ],
        "Sector3Time": [
            pd.Timedelta(25, unit="s"),
            pd.Timedelta(25, unit="s"),
        ],
        "PitOutTime": [pd.NaT, pd.Timedelta(1, unit="s")],
    })

    result = normalize_fastf1_laps(source)

    assert len(result) == 2
    assert result.loc[0, "Driver"] == "HAM"
    assert result.loc[0, "lap_duration"] == 90
    assert result.loc[0, "is_pit_out_lap"] == False
    assert result.loc[1, "is_pit_out_lap"] == True


def test_normalize_rejects_missing_source_columns():
    with pytest.raises(ValueError, match="missing columns"):
        normalize_fastf1_laps(pd.DataFrame({"Driver": ["HAM"]}))


def test_normalize_discards_invalid_lap_times():
    source = pd.DataFrame({
        "Driver": ["HAM", "VER"],
        "DriverNumber": [44, 1],
        "LapNumber": [1, 1],
        "LapTime": [pd.NaT, pd.Timedelta(91, unit="s")],
        "Sector1Time": [pd.NaT, pd.Timedelta(31, unit="s")],
        "Sector2Time": [pd.NaT, pd.Timedelta(35, unit="s")],
        "Sector3Time": [pd.NaT, pd.Timedelta(25, unit="s")],
        "PitOutTime": [pd.NaT, pd.NaT],
    })

    result = normalize_fastf1_laps(source)

    assert len(result) == 1
    assert result.iloc[0]["Driver"] == "VER"

def test_normalize_includes_tyre_and_pit_metadata():
    source = pd.DataFrame({
        "Driver": ["ham", "VER"],
        "DriverNumber": [44, 1],
        "LapNumber": [1, 2],
        "LapTime": [
            pd.Timedelta(seconds=90),
            pd.Timedelta(seconds=91),
        ],
        "Sector1Time": [
            pd.Timedelta(seconds=30),
            pd.Timedelta(seconds=31),
        ],
        "Sector2Time": [
            pd.Timedelta(seconds=35),
            pd.Timedelta(seconds=35),
        ],
        "Sector3Time": [
            pd.Timedelta(seconds=25),
            pd.Timedelta(seconds=25),
        ],
        "PitOutTime": [pd.NaT, pd.Timedelta(seconds=400)],
        "PitInTime": [pd.Timedelta(seconds=350), pd.NaT],
        "Compound": ["SOFT", "MEDIUM"],
        "TyreLife": [5.0, 2.0],
        "Stint": [1, 2],
    })

    result = normalize_fastf1_laps(source)

    assert result.loc[0, "compound"] == "SOFT"
    assert result.loc[1, "compound"] == "MEDIUM"
    assert result.loc[0, "tyre_life"] == 5
    assert result.loc[1, "stint"] == 2
    assert result.loc[0, "pit_in_time_seconds"] == 350
    assert result.loc[1, "pit_out_time_seconds"] == 400
    assert result.loc[1, "is_pit_out_lap"]


def test_normalize_supports_missing_optional_metadata():
    source = pd.DataFrame({
        "Driver": ["HAM"],
        "DriverNumber": [44],
        "LapNumber": [1],
        "LapTime": [pd.Timedelta(seconds=90)],
        "Sector1Time": [pd.Timedelta(seconds=30)],
        "Sector2Time": [pd.Timedelta(seconds=35)],
        "Sector3Time": [pd.Timedelta(seconds=25)],
    })

    result = normalize_fastf1_laps(source)

    assert len(result) == 1
    assert pd.isna(result.loc[0, "compound"])
    assert pd.isna(result.loc[0, "tyre_life"])
    assert pd.isna(result.loc[0, "stint"])
    assert pd.isna(result.loc[0, "pit_in_time_seconds"])
    assert pd.isna(result.loc[0, "pit_out_time_seconds"])
    assert not result.loc[0, "is_pit_out_lap"]
