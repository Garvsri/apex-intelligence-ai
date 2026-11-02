
import numpy as np
import pandas as pd
import pytest

from apex.analytics import grand_prix_tyre_degradation_v2


def make_stint(driver, stint, lap_times):
    """Create synthetic lap records for one tyre stint."""

    rows = []

    for index, lap_time in enumerate(lap_times):
        age = index + 1

        rows.append({
            "Driver": driver,
            "stint": stint,
            "lap_number": age,
            "lap_duration": lap_time,
            "compound": "MEDIUM",
            "tyre_life": age,
            "is_pit_out_lap": False,
        })

    return rows


@pytest.fixture
def mocked_race_dataset(monkeypatch):
    """Register a synthetic race dataset."""

    rows = []

    # High fit, high data sufficiency.
    rows += make_stint(
        "HAM", 1,
        [90 + age * 0.2 for age in range(1, 11)]
    )

    # High fit, but insufficient data.
    rows += make_stint(
        "VER", 1,
        [90.2, 90.4, 90.6, 90.8]
    )

    # Medium data sufficiency.
    rows += make_stint(
        "NOR", 1,
        [90.1, 90.2, 90.3, 90.4, 90.5, 90.6]
    )

    # Insufficient regression data.
    rows += make_stint(
        "LEC", 1,
        [90.1, 90.2]
    )

    frame = pd.DataFrame(rows)

    metadata = {
        "season": 2024,
        "grand_prix": "British Grand Prix",
        "dataset_id": "test_race_tyres",
    }

    monkeypatch.setattr(
        "apex.data_loader.list_datasets",
        lambda: [{
            "season": 2024,
            "session_type": "R",
            "grand_prix": "British Grand Prix",
            "dataset_id": "test_race_tyres",
            "status": "imported",
        }]
    )

    monkeypatch.setattr(
        "apex.data_loader.load_dataset",
        lambda dataset_id: (metadata, frame.copy())
    )


def test_v2_returns_analysis_version_21(mocked_race_dataset):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    assert result["analysis_version"] == "2.1"


def test_high_fit_does_not_mean_high_data_sufficiency(
    mocked_race_dataset,
):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    stint = next(
        item for item in result["stints"]
        if item["driver"] == "VER"
    )

    assert stint["statistical_fit_quality"] == "high"
    assert stint["data_sufficiency"] == "low"
    assert stint["tyre_wear_interpretation"] == "uncertain"


def test_high_data_sufficiency_classification(
    mocked_race_dataset,
):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    stint = next(
        item for item in result["stints"]
        if item["driver"] == "HAM"
    )

    assert stint["data_sufficiency"] == "high"
    assert stint["statistical_fit_quality"] == "high"


def test_medium_data_sufficiency_classification(
    mocked_race_dataset,
):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    stint = next(
        item for item in result["stints"]
        if item["driver"] == "NOR"
    )

    assert stint["data_sufficiency"] == "medium"


def test_insufficient_data_returns_no_regression(
    mocked_race_dataset,
):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    stint = next(
        item for item in result["stints"]
        if item["driver"] == "LEC"
    )

    assert stint["regression_status"] == "insufficient_data"
    assert stint["lap_time_trend"] == "insufficient_data"
    assert stint["robust_degradation_seconds_per_lap"] is None


def test_context_warnings_are_present(mocked_race_dataset):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    for stint in result["stints"]:
        assert "context_warnings" in stint
        assert len(stint["context_warnings"]) >= 1


def test_outlier_fields_are_consistent(mocked_race_dataset):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    for stint in result["stints"]:
        assert stint["outlier_count"] == len(
            stint["outlier_laps"]
        )


def test_lap_time_trend_uses_robust_slope(mocked_race_dataset):
    result = grand_prix_tyre_degradation_v2(
        2024, "British Grand Prix"
    )

    stint = next(
        item for item in result["stints"]
        if item["driver"] == "HAM"
    )

    assert stint["lap_time_trend"] == "increasing"
