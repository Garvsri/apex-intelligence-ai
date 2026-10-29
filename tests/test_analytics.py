
import pandas as pd
import pytest
from apex.analytics import (
    compare_driver_pace,
    grand_prix_tyre_stints,
)
from apex import data_loader


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

def sample_tyre_laps():
    return pd.DataFrame({
        "Driver": ["HAM", "HAM", "HAM", "HAM", "VER"],
        "driver_number": [44, 44, 44, 44, 1],
        "lap_number": [1, 2, 3, 4, 1],
        "lap_duration": [90.0, 91.0, 92.0, 93.0, 89.0],
        "duration_sector_1": [30.0] * 5,
        "duration_sector_2": [35.0] * 5,
        "duration_sector_3": [25.0] * 5,
        "is_pit_out_lap": [False, False, True, False, False],
        "compound": ["MEDIUM", "MEDIUM", "SOFT", "SOFT", "HARD"],
        "tyre_life": [1.0, 2.0, 1.0, 2.0, 1.0],
        "stint": [1, 1, 2, 2, 1],
        "pit_in_time_seconds": [100.0, 200.0, None, None, None],
        "pit_out_time_seconds": [None, None, 210.0, None, None],
    })


def test_tyre_stints_summarize_laps_and_compounds(monkeypatch):
    laps = sample_tyre_laps()
    datasets = [
        {
            "dataset_id": "test_tyre_race",
            "season": 2024,
            "grand_prix": "British Grand Prix",
            "session_type": "R",
            "status": "imported",
        }
    ]

    monkeypatch.setattr(data_loader, "list_datasets", lambda: datasets)
    monkeypatch.setattr(
        data_loader,
        "load_dataset",
        lambda dataset_id: (datasets[0], laps.copy()),
    )

    result = grand_prix_tyre_stints(2024, "British Grand Prix")

    ham_stints = [
        stint for stint in result["stints"]
        if stint["driver"] == "HAM"
    ]

    assert result["dataset_id"] == "test_tyre_race"
    assert len(ham_stints) == 2

    first, second = ham_stints

    assert first["stint"] == 1
    assert second["stint"] == 2

    assert first["pit_in_session_seconds"] == 200.0
    assert second["pit_out_session_seconds"] == 210.0

    first, second = ham_stints

    assert first["stint"] == 1
    assert first["compound"] == "MEDIUM"
    assert first["start_lap"] == 1
    assert first["end_lap"] == 2
    assert first["lap_records"] == 2
    assert first["mean_lap_seconds"] == 90.5
    assert first["median_lap_seconds"] == 90.5

    assert second["stint"] == 2
    assert second["compound"] == "SOFT"
    assert second["start_lap"] == 3
    assert second["end_lap"] == 4
    assert second["lap_records"] == 2


def test_tyre_stints_prefer_dataset_with_tyre_metadata(monkeypatch):
    old_dataset = {
        "dataset_id": "a_legacy_race",
        "season": 2024,
        "grand_prix": "British Grand Prix",
        "session_type": "R",
        "status": "imported",
    }
    tyre_dataset = {
        "dataset_id": "z_tyre_race",
        "season": 2024,
        "grand_prix": "British Grand Prix",
        "session_type": "R",
        "status": "imported",
    }

    legacy_laps = sample_tyre_laps().drop(
        columns=["compound", "stint", "tyre_life"]
    )

    def fake_load(dataset_id):
        if dataset_id == "a_legacy_race":
            return old_dataset, legacy_laps.copy()
        return tyre_dataset, sample_tyre_laps()

    monkeypatch.setattr(
        data_loader,
        "list_datasets",
        lambda: [old_dataset, tyre_dataset],
    )
    monkeypatch.setattr(data_loader, "load_dataset", fake_load)

    result = grand_prix_tyre_stints(2024, "British Grand Prix")

    assert result["dataset_id"] == "z_tyre_race"


def test_tyre_stints_raise_when_no_race_exists(monkeypatch):
    monkeypatch.setattr(data_loader, "list_datasets", lambda: [])

    with pytest.raises(ValueError, match="No imported race dataset"):
        grand_prix_tyre_stints(2024, "British Grand Prix")


def test_tyre_stints_raise_when_metadata_is_missing(monkeypatch):
    datasets = [
        {
            "dataset_id": "legacy_race",
            "season": 2024,
            "grand_prix": "British Grand Prix",
            "session_type": "R",
            "status": "imported",
        }
    ]

    legacy_laps = sample_tyre_laps().drop(
        columns=["compound", "stint", "tyre_life"]
    )

    monkeypatch.setattr(data_loader, "list_datasets", lambda: datasets)
    monkeypatch.setattr(
        data_loader,
        "load_dataset",
        lambda dataset_id: (datasets[0], legacy_laps.copy()),
    )

    with pytest.raises(ValueError, match="No tyre metadata"):
        grand_prix_tyre_stints(2024, "British Grand Prix")
