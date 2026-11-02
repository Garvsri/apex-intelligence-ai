import numpy as np
import pandas as pd
import pytest

from apex.strategy_simulator import (
    _fit_pace_models,
    _prepare_laps,
    simulate_live_strategy,
    simulate_race_strategy,
)


def make_race_data():
    rows = []
    compounds = {"SOFT": (90.0, 0.075), "MEDIUM": (90.5, 0.045), "HARD": (91.0, 0.025)}
    offsets = {"VER": 0.0, "HAM": 0.35, "LEC": 0.6}
    for driver, offset in offsets.items():
        for compound, (base, degradation) in compounds.items():
            for age in range(1, 26):
                rows.append({
                    "Driver": driver,
                    "lap_number": age,
                    "lap_duration": base + offset + degradation * (age - 1) + 0.01 * np.sin(age),
                    "compound": compound,
                    "tyre_life": age,
                    "is_pit_out_lap": False,
                })
    return pd.DataFrame(rows)


def test_prepare_laps_removes_invalid_and_pit_out_rows():
    data = make_race_data()
    data.loc[0, "lap_duration"] = np.nan
    data.loc[1, "is_pit_out_lap"] = True
    cleaned = _prepare_laps(data)
    assert len(cleaned) == len(data) - 2


def test_driver_offsets_are_not_zero_for_slower_driver():
    models = _fit_pace_models(_prepare_laps(make_race_data()))
    assert models["driver_offsets"]["HAM"] > models["driver_offsets"]["VER"]


def test_historical_strategy_covers_race_and_accounts_for_stops():
    result = simulate_race_strategy(make_race_data(), race_laps=20, driver="VER", max_stops=2)
    strategy = result["driver_results"][0]["best_strategy"]
    assert sum(stint["laps"] for stint in strategy["stints"]) == 20
    assert strategy["stops"] == len(strategy["stints"]) - 1
    assert len({stint["compound"] for stint in strategy["stints"]}) >= 2


def test_historical_field_ranking_contains_all_drivers():
    result = simulate_race_strategy(make_race_data(), race_laps=20, max_stops=2)
    assert result["drivers_analyzed"] == 3
    assert [item["position"] for item in result["field_ranking"]] == [1, 2, 3]


def test_live_optimizer_uses_multiple_stop_budget_and_returns_valid_plan():
    result = simulate_live_strategy(
        make_race_data(),
        {"VER": {"current_compound": "MEDIUM", "tyre_age": 8}},
        remaining_laps=20,
        max_stops=2,
    )
    driver = result["driver_results"][0]
    recommendation = driver["recommendation"]
    assert recommendation["stops_added"] <= 2
    assert sum(stint["laps"] for stint in recommendation["stints"]) == 20
    assert recommendation["estimated_remaining_seconds"] > 0


def test_invalid_live_compound_is_rejected():
    with pytest.raises(ValueError, match="No historical model"):
        simulate_live_strategy(
            make_race_data(),
            {"VER": {"current_compound": "INTERMEDIATE", "tyre_age": 4}},
            remaining_laps=10,
        )


def test_negative_pit_loss_is_rejected():
    with pytest.raises(ValueError, match="Pit loss"):
        simulate_race_strategy(make_race_data(), pit_loss_seconds=-1)


def test_insufficient_compounds_is_rejected():
    data = make_race_data()
    data = data[data["compound"] == "HARD"]
    with pytest.raises(ValueError, match="At least two dry compounds"):
        simulate_race_strategy(data, race_laps=10)
