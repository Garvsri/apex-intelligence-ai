from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd

DRY_COMPOUNDS = ("SOFT", "MEDIUM", "HARD")


def _prepare_laps(laps: pd.DataFrame) -> pd.DataFrame:
    required = {"Driver", "lap_number", "lap_duration", "compound", "tyre_life"}
    missing = required - set(laps.columns)
    if missing:
        raise ValueError(f"Strategy simulation requires columns: {sorted(missing)}")

    frame = laps.copy()
    for column in ("lap_number", "lap_duration", "tyre_life"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["Driver"] = frame["Driver"].astype("string").str.strip().str.upper()
    frame["compound"] = frame["compound"].astype("string").str.strip().str.upper()
    frame = frame.dropna(subset=["Driver", "lap_number", "lap_duration", "tyre_life", "compound"])
    frame = frame[
        (frame["Driver"] != "")
        & (frame["lap_number"] > 0)
        & (frame["lap_duration"] > 0)
        & (frame["tyre_life"] > 0)
        & (frame["compound"].isin(DRY_COMPOUNDS))
    ]
    if "is_pit_out_lap" in frame.columns:
        pit_out = frame["is_pit_out_lap"].astype("string").str.strip().str.lower().isin({"true", "1", "yes"})
        frame = frame[~pit_out]
    if frame.empty:
        raise ValueError("No valid dry-tyre lap records found.")
    frame["lap_number"] = frame["lap_number"].astype(int)
    frame["tyre_life"] = frame["tyre_life"].astype(int)
    return frame.reset_index(drop=True)


def _fit_pace_models(frame: pd.DataFrame) -> dict:
    """Fit compound degradation slopes and driver pace offsets.

    Model: lap_time = compound_baseline + driver_offset + degradation * (age - 1).
    Driver offsets are median residuals against the compound-wide fits.
    This is a descriptive historical model, not a causal tyre-wear model.
    """
    global_models = {}
    for compound, group in frame.groupby("compound"):
        ages = group["tyre_life"].to_numpy(dtype=float)
        times = group["lap_duration"].to_numpy(dtype=float)
        if len(times) < 3 or len(np.unique(ages)) < 2:
            continue
        slope, intercept = np.polyfit(ages - 1.0, times, 1)
        global_models[compound] = {
            "baseline": float(intercept),
            "degradation": float(max(0.0, slope)),
            "samples": int(len(times)),
        }
    if not global_models:
        raise ValueError("Insufficient data to fit compound performance models.")

    residuals = []
    for row in frame.itertuples(index=False):
        model = global_models.get(row.compound)
        if model:
            predicted = model["baseline"] + model["degradation"] * (row.tyre_life - 1)
            residuals.append((row.Driver, float(row.lap_duration - predicted)))
    residual_frame = pd.DataFrame(residuals, columns=["Driver", "residual"])
    driver_offsets = residual_frame.groupby("Driver")["residual"].median().to_dict()

    driver_models = {}
    for driver in frame["Driver"].unique():
        offset = float(driver_offsets.get(driver, 0.0))
        for compound, base in global_models.items():
            driver_models[(driver, compound)] = {
                "baseline": base["baseline"] + offset,
                "degradation": base["degradation"],
                "samples": base["samples"],
                "source": "compound_model_plus_driver_offset",
            }
    return {"driver_models": driver_models, "global_models": global_models, "driver_offsets": driver_offsets}


def _lap_time(model: dict, tyre_age: int) -> float:
    return float(model["baseline"] + model["degradation"] * max(0, tyre_age - 1))


def _stint_cost(model: dict, start_age: int, length: int) -> float:
    if length <= 0:
        return 0.0
    ages = np.arange(start_age, start_age + length, dtype=float)
    return float(np.sum(model["baseline"] + model["degradation"] * np.maximum(0.0, ages - 1.0)))


def _available_compounds(models: dict) -> list[str]:
    available = [compound for compound in DRY_COMPOUNDS if compound in models["global_models"]]
    if len(available) < 2:
        raise ValueError("At least two dry compounds must be available.")
    return available


def _optimize_future_stints(
    driver: str,
    models: dict,
    remaining_laps: int,
    stints_left: int,
    last_compound: Optional[str],
    used_compounds: frozenset[str],
    pit_loss_seconds: float,
    min_stint_laps: int,
    max_stint_age: int,
    require_two_compounds: bool,
):
    """Optimize a sequence of future stints; stints_left includes the final stint."""
    available = _available_compounds(models)

    @lru_cache(maxsize=None)
    def solve(remaining: int, count: int, previous: Optional[str], used_mask: int):
        if count < 1 or remaining < count * min_stint_laps:
            return float("inf"), ()
        used = frozenset(available[i] for i in range(len(available)) if used_mask & (1 << i))
        best_cost, best_plan = float("inf"), ()
        choices = [c for c in available if c != previous]
        for compound in choices:
            model = models["driver_models"].get((driver, compound), models["global_models"][compound])
            bit = 1 << available.index(compound)
            new_mask = used_mask | bit
            if count == 1:
                length = remaining
                if length < min_stint_laps or length > max_stint_age:
                    continue
                final_used = used | {compound}
                if require_two_compounds and len(final_used) < 2:
                    continue
                cost = _stint_cost(model, 1, length)
                if cost < best_cost:
                    best_cost, best_plan = cost, ((compound, length),)
                continue
            max_length = min(max_stint_age, remaining - min_stint_laps * (count - 1))
            for length in range(min_stint_laps, max_length + 1):
                stint = _stint_cost(model, 1, length)
                future_cost, future_plan = solve(remaining - length, count - 1, compound, new_mask)
                total = stint + pit_loss_seconds + future_cost
                if total < best_cost:
                    best_cost = total
                    best_plan = ((compound, length),) + future_plan
        return best_cost, best_plan

    initial_mask = 0
    for index, compound in enumerate(available):
        if compound in used_compounds:
            initial_mask |= 1 << index
    return solve(int(remaining_laps), int(stints_left), last_compound, initial_mask)


def _format_plan(driver: str, plan: tuple, total_cost: float, stops: int, first_lap: int = 1) -> dict:
    lap = first_lap
    stints = []
    for index, (compound, length) in enumerate(plan, start=1):
        if length <= 0:
            continue
        end_lap = lap + length - 1
        stints.append({"stint": len(stints) + 1, "compound": compound, "start_lap": lap, "end_lap": end_lap, "laps": length})
        lap = end_lap + 1
    return {"driver": driver, "stops": max(0, len(stints) - 1), "estimated_total_seconds": round(float(total_cost), 3), "stints": stints, "rank": 0}


def _build_strategy(driver: str, models: dict, race_laps: int, pit_loss_seconds: float, max_stops: int,
                    max_stint_age: int, initial_compound: Optional[str] = None, initial_tyre_age: int = 0,
                    min_stint_laps: int = 1, require_two_compounds: bool = True) -> dict:
    available = _available_compounds(models)
    if initial_compound is not None:
        initial_compound = initial_compound.upper()
        if initial_compound not in available:
            raise ValueError(f"No historical model for {initial_compound} tyres.")
        if initial_tyre_age < 1:
            raise ValueError("Initial tyre age must be positive.")

    results = []
    if initial_compound is None:
        for stops in range(1, max_stops + 1):
            cost, plan = _optimize_future_stints(
                driver, models, race_laps, stops + 1, None, frozenset(),
                pit_loss_seconds, min_stint_laps, max_stint_age, require_two_compounds,
            )
            if np.isfinite(cost) and plan:
                results.append(_format_plan(driver, plan, cost, stops))
    else:
        # Current tyres may be kept for zero or more additional laps before the first stop.
        current_model = models["driver_models"].get((driver, initial_compound), models["global_models"][initial_compound])
        max_continue = min(race_laps, max(0, max_stint_age - initial_tyre_age))
        for stops in range(0, max_stops + 1):
            if stops == 0:
                if race_laps <= max_continue and (not require_two_compounds):
                    cost = _stint_cost(current_model, initial_tyre_age + 1, race_laps)
                    plan = ((initial_compound, race_laps),)
                    result = _format_plan(driver, plan, cost, 0)
                    result["action"] = "stay_out"
                    results.append(result)
                continue
            for continue_laps in range(0, max_continue + 1):
                future_laps = race_laps - continue_laps
                if future_laps < stops * min_stint_laps:
                    continue
                future_cost, future_plan = _optimize_future_stints(
                    driver, models, future_laps, stops, initial_compound,
                    frozenset({initial_compound}), pit_loss_seconds,
                    min_stint_laps, max_stint_age, require_two_compounds,
                )
                if not np.isfinite(future_cost) or not future_plan:
                    continue
                current_cost = _stint_cost(current_model, initial_tyre_age + 1, continue_laps)
                total = current_cost + pit_loss_seconds + future_cost
                plan = ((initial_compound, continue_laps),) + future_plan
                result = _format_plan(driver, plan, total, stops)
                result["stops"] = stops
                result["action"] = "pit_now" if continue_laps == 0 else "stay_out_then_pit"
                result["laps_until_pit"] = continue_laps
                result["next_compound"] = future_plan[0][0]
                results.append(result)

    if not results:
        raise ValueError(f"Could not generate feasible strategies for {driver}.")
    results.sort(key=lambda item: item["estimated_total_seconds"])
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank
    return {"driver": driver, "best_strategy": results[0], "alternatives": results}


def simulate_race_strategy(laps: pd.DataFrame, race_laps: Optional[int] = None,
                           pit_loss_seconds: float = 22.0, max_stops: int = 3,
                           driver: Optional[str] = None, min_stint_laps: int = 1,
                           max_stint_age: Optional[int] = None,
                           require_two_compounds: bool = True) -> dict:
    if pit_loss_seconds < 0:
        raise ValueError("Pit loss cannot be negative.")
    if not 1 <= max_stops <= 3:
        raise ValueError("max_stops must be between 1 and 3.")
    if min_stint_laps < 1:
        raise ValueError("Minimum stint length must be positive.")
    frame = _prepare_laps(laps)
    actual_laps = int(frame["lap_number"].max())
    distance = int(race_laps or actual_laps)
    if distance < 1 or distance > actual_laps:
        raise ValueError("Race distance must be between 1 and recorded race laps.")
    if driver:
        driver = driver.strip().upper()
        frame = frame[frame["Driver"] == driver]
        if frame.empty:
            raise ValueError(f"No historical tyre data found for driver {driver}.")
    models = _fit_pace_models(frame)
    _available_compounds(models)
    if max_stint_age is None:
        max_stint_age = int(max(10, min(35, frame["tyre_life"].quantile(0.90))))
    if max_stint_age < min_stint_laps:
        raise ValueError("Maximum stint age cannot be below minimum stint length.")
    results = []
    for code in sorted(frame["Driver"].unique()):
        try:
            results.append(_build_strategy(code, models, distance, pit_loss_seconds, max_stops,
                                           max_stint_age, min_stint_laps=min_stint_laps,
                                           require_two_compounds=require_two_compounds))
        except ValueError:
            continue
    if not results:
        raise ValueError("No drivers had enough data to simulate a strategy.")
    results.sort(key=lambda item: item["best_strategy"]["estimated_total_seconds"])
    for position, item in enumerate(results, start=1):
        item["field_rank"] = position
    return {
        "mode": "historical_replay", "race_laps": distance,
        "drivers_analyzed": len(results), "pit_loss_seconds": pit_loss_seconds,
        "max_stops": max_stops, "driver_results": results,
        "field_ranking": [{"position": item["field_rank"], "driver": item["driver"],
                           "estimated_total_seconds": item["best_strategy"]["estimated_total_seconds"],
                           "stops": item["best_strategy"]["stops"]} for item in results],
        "model_note": "Estimates use compound-wide tyre-age pace trends plus driver median pace offsets. This is a simplified historical pace model, not a validated race outcome prediction.",
        "limitations": ["Weather, track status, fuel, traffic and safety cars are not modelled.",
                        "Historical lap-time trends are not pure tyre-wear measurements.",
                        "Tyre-set availability and event-specific FIA compound rules are not modelled.",
                        "Pit loss is a user-configured assumption."]
    }


def simulate_live_strategy(laps: pd.DataFrame, driver_states: dict, remaining_laps: int,
                            pit_loss_seconds: float = 22.0, max_stops: int = 3,
                            min_stint_laps: int = 1, max_stint_age: Optional[int] = None,
                            require_two_compounds: bool = True) -> dict:
    if not driver_states:
        raise ValueError("At least one live driver state is required.")
    if remaining_laps < 1:
        raise ValueError("remaining_laps must be positive.")
    if pit_loss_seconds < 0:
        raise ValueError("Pit loss cannot be negative.")
    if not 1 <= max_stops <= 3:
        raise ValueError("max_stops must be between 1 and 3.")
    if min_stint_laps < 1:
        raise ValueError("Minimum stint length must be positive.")
    frame = _prepare_laps(laps)
    models = _fit_pace_models(frame)
    _available_compounds(models)
    if max_stint_age is None:
        max_stint_age = int(max(10, min(35, frame["tyre_life"].quantile(0.90))))
    results = []
    for raw_driver, state in driver_states.items():
        driver = str(raw_driver).strip().upper()
        compound = str(state.get("current_compound", "")).strip().upper()
        try:
            tyre_age = int(state.get("tyre_age", 0))
        except (TypeError, ValueError):
            raise ValueError(f"Invalid tyre age for {driver}.")
        if compound not in DRY_COMPOUNDS or compound not in models["global_models"]:
            raise ValueError(f"No historical model for current {compound or 'unknown'} tyres for {driver}.")
        if tyre_age < 1:
            raise ValueError(f"Tyre age must be positive for {driver}.")
        strategy = _build_strategy(driver, models, int(remaining_laps), pit_loss_seconds,
                                   max_stops, max_stint_age, initial_compound=compound,
                                   initial_tyre_age=tyre_age, min_stint_laps=min_stint_laps,
                                   require_two_compounds=require_two_compounds)
        candidates = strategy["alternatives"]
        best = candidates[0]
        recommendation = {
            "driver": driver,
            "action": best.get("action", "stay_out"),
            "compound": best.get("next_compound", compound),
            "estimated_remaining_seconds": best["estimated_total_seconds"],
            "stops_added": best["stops"],
            "laps_until_pit": best.get("laps_until_pit", remaining_laps),
            "stints": best["stints"],
        }
        alternatives = [{"driver": driver, "action": item.get("action", "stay_out"),
                         "compound": item.get("next_compound", compound),
                         "estimated_remaining_seconds": item["estimated_total_seconds"],
                         "stops_added": item["stops"],
                         "laps_until_pit": item.get("laps_until_pit", remaining_laps),
                         "stints": item["stints"]} for item in candidates[:5]]
        results.append({"driver": driver, "current_compound": compound,
                        "current_tyre_age": tyre_age, "recommendation": recommendation,
                        "alternatives": alternatives})
    return {
        "mode": "live_snapshot", "remaining_laps": int(remaining_laps),
        "pit_loss_seconds": pit_loss_seconds, "driver_results": results,
        "model_note": "Multi-stop strategy estimates from caller-supplied race-state snapshots. This is not connected to a live telemetry feed.",
        "limitations": ["No automatic live timing feed.",
                        "Weather, track status, fuel, traffic and safety cars are not modelled.",
                        "Tyre-set availability and event-specific FIA compound rules are not modelled.",
                        "Pit loss is configurable, not measured from pit timestamps."]
    }


def evaluate_custom_strategy(
    laps: pd.DataFrame,
    driver: str,
    stints: list[dict],
    race_laps: int,
    pit_loss_seconds: float = 22.0,
    require_two_compounds: bool = True,
) -> dict:
    """Score a user-defined dry-tyre strategy using the historical pace model."""
    if pit_loss_seconds < 0:
        raise ValueError("Pit loss cannot be negative.")

    frame = _prepare_laps(laps)
    actual_laps = int(frame["lap_number"].max())
    distance = int(race_laps)

    if distance < 1 or distance > actual_laps:
        raise ValueError(
            f"Race distance must be between 1 and {actual_laps} recorded race laps."
        )

    driver = str(driver).strip().upper()
    frame = frame[frame["Driver"] == driver]
    if frame.empty:
        raise ValueError(f"No historical tyre data found for driver {driver}.")

    if not isinstance(stints, list) or not stints:
        raise ValueError("Add at least one stint to your custom strategy.")

    models = _fit_pace_models(frame)
    available = _available_compounds(models)
    max_stint_age = int(max(10, min(35, frame["tyre_life"].quantile(0.90))))

    normalized_stints = []
    for index, stint in enumerate(stints, start=1):
        compound = str(stint.get("compound", "")).strip().upper()
        try:
            length = int(stint.get("laps", 0))
        except (TypeError, ValueError):
            raise ValueError(f"Stint {index} has an invalid lap count.")

        if compound not in DRY_COMPOUNDS or compound not in available:
            raise ValueError(
                f"{compound or 'Unknown'} is not available in the historical model for {driver}."
            )
        if length < 1:
            raise ValueError(f"Stint {index} must contain at least one lap.")
        if length > max_stint_age:
            raise ValueError(
                f"Stint {index} is {length} laps, exceeding the model's "
                f"maximum supported stint length of {max_stint_age} laps."
            )
        if normalized_stints and compound == normalized_stints[-1]["compound"]:
            raise ValueError("Consecutive stints must use different compounds.")

        normalized_stints.append({"compound": compound, "laps": length})

    total_stint_laps = sum(item["laps"] for item in normalized_stints)
    if total_stint_laps != distance:
        raise ValueError(
            f"Your stints cover {total_stint_laps} laps, but the selected race distance is {distance}."
        )

    used_compounds = {item["compound"] for item in normalized_stints}
    if require_two_compounds and len(used_compounds) < 2:
        raise ValueError("A dry-race strategy must use at least two different compounds.")

    current_lap = 1
    estimated_lap_time = 0.0
    formatted_stints = []

    for index, stint in enumerate(normalized_stints, start=1):
        compound = stint["compound"]
        length = stint["laps"]
        model = models["driver_models"].get(
            (driver, compound), models["global_models"][compound]
        )
        stint_time = _stint_cost(model, 1, length)
        end_lap = current_lap + length - 1
        estimated_lap_time += stint_time

        formatted_stints.append({
            "stint": index,
            "compound": compound,
            "start_lap": current_lap,
            "end_lap": end_lap,
            "laps": length,
            "estimated_time_seconds": round(float(stint_time), 3),
        })
        current_lap = end_lap + 1

    pit_stops = max(0, len(formatted_stints) - 1)
    total_pit_loss = pit_stops * float(pit_loss_seconds)
    custom_total = estimated_lap_time + total_pit_loss

    # Compare against the same optimizer/model and race distance.
    optimized = simulate_race_strategy(
        laps=laps,
        race_laps=distance,
        pit_loss_seconds=pit_loss_seconds,
        max_stops=max(1, min(3, pit_stops)),
        driver=driver,
        require_two_compounds=require_two_compounds,
    )
    recommended = optimized["driver_results"][0]["best_strategy"]
    recommended_total = float(recommended["estimated_total_seconds"])
    delta = float(custom_total - recommended_total)

    return {
        "mode": "custom_strategy",
        "driver": driver,
        "race_laps": distance,
        "pit_loss_seconds": float(pit_loss_seconds),
        "pit_stops": pit_stops,
        "stints": formatted_stints,
        "estimated_lap_time_seconds": round(float(estimated_lap_time), 3),
        "total_pit_loss_seconds": round(float(total_pit_loss), 3),
        "estimated_total_seconds": round(float(custom_total), 3),
        "recommended_strategy": recommended,
        "recommended_total_seconds": round(recommended_total, 3),
        "delta_vs_recommended_seconds": round(delta, 3),
        "custom_is_faster": delta < 0,
        "max_supported_stint_laps": max_stint_age,
        "model_note": (
            "Custom plan scored with compound-wide tyre-age pace trends and "
            "the selected driver's median pace offset. This is a simplified "
            "historical model, not a validated race outcome prediction."
        ),
        "limitations": [
            "Weather, track status, fuel, traffic and safety cars are not modelled.",
            "Historical lap-time trends are not pure tyre-wear measurements.",
            "Tyre-set availability and event-specific FIA compound rules are not modelled.",
            "Pit loss is a user-configured assumption.",
        ],
    }

