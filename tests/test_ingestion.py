
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
