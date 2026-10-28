
import pandas as pd
import pytest

from apex.analytics import compare_driver_pace


def test_compare_two_drivers():
    laps = pd.DataFrame({
        "Driver": ["HAM", "HAM", "VER", "VER"],
        "lap_duration": [90.0, 92.0, 91.0, 93.0],
    })

    result = compare_driver_pace(laps, "HAM", "VER")

    assert result["HAM"]["mean_lap_seconds"] == 91.0
    assert result["VER"]["mean_lap_seconds"] == 92.0
    assert result["HAM"]["valid_laps"] == 2
    assert result["VER"]["valid_laps"] == 2
    assert result["mean_gap_seconds"] == -1.0


def test_invalid_lap_durations_are_ignored():
    laps = pd.DataFrame({
        "Driver": ["HAM", "HAM", "VER", "VER"],
        "lap_duration": [90.0, None, 91.0, "invalid"],
    })

    result = compare_driver_pace(laps, "HAM", "VER")

    assert result["HAM"]["valid_laps"] == 1
    assert result["VER"]["valid_laps"] == 1
    assert result["mean_gap_seconds"] == -1.0


def test_missing_required_column_raises_error():
    laps = pd.DataFrame({"Driver": ["HAM"]})

    with pytest.raises(ValueError, match="Missing required columns"):
        compare_driver_pace(laps, "HAM", "VER")


def test_driver_with_no_valid_laps():
    laps = pd.DataFrame({
        "Driver": ["HAM", "VER"],
        "lap_duration": [90.0, None],
    })

    result = compare_driver_pace(laps, "HAM", "VER")

    assert result["HAM"]["mean_lap_seconds"] == 90.0
    assert result["VER"]["mean_lap_seconds"] is None
    assert result["mean_gap_seconds"] is None
