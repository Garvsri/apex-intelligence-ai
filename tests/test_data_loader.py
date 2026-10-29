
import pandas as pd
import pytest

from apex.data_loader import load_laps


def test_load_british_gp_dataset():
    laps = load_laps()

    assert len(laps) == 914
    assert laps["Driver"].nunique() == 19
    assert laps["Driver"].isna().sum() == 0
    assert (laps["lap_duration"] > 0).all()


def test_missing_file_raises_error(tmp_path):
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_laps(missing_file)


def test_missing_required_column_raises_error(tmp_path):
    invalid_file = tmp_path / "invalid.csv"
    pd.DataFrame(
        {"Driver": ["HAM"], "lap_duration": [94.2]}
    ).to_csv(invalid_file, index=False)

    with pytest.raises(ValueError, match="missing required columns"):
        load_laps(invalid_file)


def test_invalid_lap_duration_raises_error(tmp_path):
    invalid_file = tmp_path / "invalid_duration.csv"

    data = {
        "Driver": ["HAM"],
        "driver_number": [44],
        "lap_number": [1],
        "lap_duration": [0],
        "duration_sector_1": [32.0],
        "duration_sector_2": [37.0],
        "duration_sector_3": [25.0],
        "is_pit_out_lap": [False],
    }
    pd.DataFrame(data).to_csv(invalid_file, index=False)

    with pytest.raises(ValueError, match="non-positive lap durations"):
        load_laps(invalid_file)

def test_load_laps_preserves_optional_tyre_metadata(tmp_path):
    path = tmp_path / "laps_with_tyre_data.csv"

    data = {
        "Driver": ["HAM"],
        "driver_number": [44],
        "lap_number": [1],
        "lap_duration": [94.2],
        "duration_sector_1": [32.0],
        "duration_sector_2": [37.0],
        "duration_sector_3": [25.2],
        "is_pit_out_lap": [False],
        "compound": ["MEDIUM"],
        "tyre_life": [5.0],
        "stint": [1],
        "pit_in_time_seconds": [None],
        "pit_out_time_seconds": [None],
    }

    pd.DataFrame(data).to_csv(path, index=False)
    laps = load_laps(path)

    assert laps.loc[0, "compound"] == "MEDIUM"
    assert laps.loc[0, "tyre_life"] == 5.0
    assert laps.loc[0, "stint"] == 1
    assert pd.isna(laps.loc[0, "pit_in_time_seconds"])
    assert pd.isna(laps.loc[0, "pit_out_time_seconds"])
