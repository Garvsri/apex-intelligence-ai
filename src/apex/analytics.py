
import numpy as np
import pandas as pd
from scipy.stats import theilslopes


def compare_driver_pace(
    laps: pd.DataFrame,
    driver_a: str,
    driver_b: str,
) -> dict:
    """Compare mean lap times for two drivers."""

    required = {"Driver", "lap_duration"}
    missing = required - set(laps.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    selected = laps[
        laps["Driver"].isin([driver_a, driver_b])
    ].copy()

    selected["lap_duration"] = pd.to_numeric(
        selected["lap_duration"],
        errors="coerce",
    )
    selected = selected.dropna(subset=["lap_duration"])
    selected = selected[selected["lap_duration"] > 0]

    averages = selected.groupby("Driver")["lap_duration"].mean()

    result = {}

    for driver in [driver_a, driver_b]:
        result[driver] = {
            "mean_lap_seconds": (
                round(float(averages[driver]), 3)
                if driver in averages.index else None
            ),
            "valid_laps": int((selected["Driver"] == driver).sum()),
        }

    if (
        result[driver_a]["mean_lap_seconds"] is not None
        and result[driver_b]["mean_lap_seconds"] is not None
    ):
        result["mean_gap_seconds"] = round(
            result[driver_a]["mean_lap_seconds"]
            - result[driver_b]["mean_lap_seconds"],
            3,
        )
    else:
        result["mean_gap_seconds"] = None

    return result


def season_driver_leaderboard(season: int) -> list[dict]:
    """
    Summarize season pace and compare drivers relative to
    the field at each race.

    Raw means across circuits are descriptive, not a direct
    ranking of driver skill.
    """
    from apex.data_loader import list_datasets, load_dataset

    if not isinstance(season, int) or isinstance(season, bool):
        raise ValueError("Season must be an integer.")

    datasets = [
        entry for entry in list_datasets()
        if entry["season"] == season and entry["session_type"] == "R"
    ]

    if not datasets:
        raise ValueError(
            f"No registered race datasets found for {season}."
        )

    race_frames = []

    for entry in datasets:
        metadata, laps = load_dataset(entry["dataset_id"])

        required = {"Driver", "lap_duration"}
        missing = required - set(laps.columns)
        if missing:
            raise ValueError(
                f"{entry['dataset_id']} is missing columns: "
                f"{sorted(missing)}"
            )

        columns = ["Driver", "lap_duration"]
        if "is_pit_out_lap" in laps.columns:
            columns.append("is_pit_out_lap")

        frame = laps[columns].copy()
        frame["lap_duration"] = pd.to_numeric(
            frame["lap_duration"], errors="coerce"
        )
        frame = frame.dropna(subset=["Driver", "lap_duration"])
        frame = frame[frame["lap_duration"] > 0]

        if "is_pit_out_lap" in frame.columns:
            pit_out = (
                frame["is_pit_out_lap"]
                .astype("string")
                .str.lower()
                .isin(["true", "1", "yes"])
            )
            frame = frame[~pit_out]

        frame["grand_prix"] = metadata["grand_prix"]
        frame["dataset_id"] = metadata["dataset_id"]
        race_frames.append(frame[[
            "Driver", "lap_duration", "grand_prix", "dataset_id"
        ]])

    all_laps = pd.concat(race_frames, ignore_index=True)

    if all_laps.empty:
        return []

    # Average pace for each driver at each race.
    race_pace = (
        all_laps.groupby(["dataset_id", "grand_prix", "Driver"])
        ["lap_duration"]
        .mean()
        .reset_index(name="driver_race_mean_seconds")
    )

    # Use the median of driver averages in each race as the
    # reference, reducing sensitivity to unusually slow averages.
    race_pace["race_reference_seconds"] = (
        race_pace.groupby("dataset_id")["driver_race_mean_seconds"]
        .transform("median")
    )
    race_pace["pace_delta_seconds"] = (
        race_pace["driver_race_mean_seconds"]
        - race_pace["race_reference_seconds"]
    )

    relative = (
        race_pace.groupby("Driver")
        .agg(
            mean_race_pace_delta_seconds=("pace_delta_seconds", "mean"),
            races_with_pace_comparison=("dataset_id", "nunique"),
        )
        .reset_index()
    )

    raw = (
        all_laps.groupby("Driver")
        .agg(
            mean_lap_seconds=("lap_duration", "mean"),
            lap_time_std_seconds=("lap_duration", "std"),
            valid_laps=("lap_duration", "count"),
            races_analyzed=("dataset_id", "nunique"),
        )
        .reset_index()
    )

    leaderboard = raw.merge(relative, on="Driver", how="left")

    for column in [
        "mean_lap_seconds",
        "lap_time_std_seconds",
        "mean_race_pace_delta_seconds",
    ]:
        leaderboard[column] = leaderboard[column].round(3)

    leaderboard = leaderboard.sort_values(
        "mean_race_pace_delta_seconds"
    )

    return leaderboard.astype(object).where(
        pd.notna(leaderboard), None
    ).to_dict(orient="records")

def grand_prix_driver_performance(
    season: int,
    grand_prix: str,
) -> dict:
    """Summarize fastest laps and driver pace for one Grand Prix."""
    from apex.data_loader import list_datasets, load_dataset

    if not isinstance(season, int) or isinstance(season, bool):
        raise ValueError("Season must be an integer.")

    if not isinstance(grand_prix, str) or not grand_prix.strip():
        raise ValueError("Grand Prix name must be a non-empty string.")

    matches = [
        entry for entry in list_datasets()
        if entry["season"] == season
        and entry["session_type"] == "R"
        and entry["grand_prix"].casefold() == grand_prix.strip().casefold()
    ]
    matches.sort(
    key=lambda entry: (
        "race_tyres" not in entry.get("dataset_id", ""),
        entry.get("dataset_id", ""),
    )
)

    if not matches:
        available = sorted({
            entry["grand_prix"]
            for entry in list_datasets()
            if entry["season"] == season and entry["session_type"] == "R"
        })
        raise ValueError(
            f"No race dataset found for {grand_prix} in {season}. "
            f"Available Grand Prix: {available}"
        )

    # Prefer the explicitly imported race dataset if duplicates exist.
    matches.sort(
        key=lambda entry: (
            entry.get("status") != "imported",
            entry["dataset_id"],
        )
    )
    metadata, laps = load_dataset(matches[0]["dataset_id"])

    required = {"Driver", "lap_duration", "lap_number"}
    missing = required - set(laps.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {sorted(missing)}")

    frame = laps.copy()
    frame["lap_duration"] = pd.to_numeric(
        frame["lap_duration"], errors="coerce"
    )
    frame["lap_number"] = pd.to_numeric(
        frame["lap_number"], errors="coerce"
    )
    frame = frame.dropna(subset=["Driver", "lap_duration", "lap_number"])
    frame = frame[frame["lap_duration"] > 0]

    if "is_pit_out_lap" in frame.columns:
        pit_out = (
            frame["is_pit_out_lap"]
            .astype("string")
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        frame = frame[~pit_out]

    if frame.empty:
        raise ValueError("No valid laps remain for this Grand Prix.")

    frame["Driver"] = frame["Driver"].astype(str).str.strip().str.upper()

    fastest = frame.loc[frame["lap_duration"].idxmin()]
    driver_stats = (
        frame.groupby("Driver")
        .agg(
            fastest_lap_seconds=("lap_duration", "min"),
            mean_lap_seconds=("lap_duration", "mean"),
            valid_laps=("lap_duration", "count"),
        )
        .reset_index()
        .sort_values("mean_lap_seconds")
    )

    driver_stats["fastest_lap_seconds"] = (
        driver_stats["fastest_lap_seconds"].round(3)
    )
    driver_stats["mean_lap_seconds"] = (
        driver_stats["mean_lap_seconds"].round(3)
    )

    return {
        "season": season,
        "grand_prix": metadata["grand_prix"],
        "session_type": metadata["session_type"],
        "dataset_id": metadata["dataset_id"],
        "fastest_lap": {
    "driver": fastest["Driver"],
    "driver_name": {
        "SAI": "Carlos Sainz",
        "PER": "Sergio Perez",
        "HAM": "Lewis Hamilton",
        "VER": "Max Verstappen",
    }.get(fastest["Driver"], fastest["Driver"]),
    "lap_number": int(fastest["lap_number"]),
    "lap_time_seconds": round(float(fastest["lap_duration"]), 3),
},
        "best_mean_pace": {
            "driver": driver_stats.iloc[0]["Driver"],
            "driver_name": {
                "SAI": "Carlos Sainz",
                "PER": "Sergio Perez",
                "HAM": "Lewis Hamilton",
                "VER": "Max Verstappen",
            }.get(driver_stats.iloc[0]["Driver"], driver_stats.iloc[0]["Driver"]),
            "mean_lap_seconds": float(
                driver_stats.iloc[0]["mean_lap_seconds"]
            ),
            "valid_laps": int(
                driver_stats.iloc[0]["valid_laps"]
            ),
        },
        "drivers": driver_stats.to_dict(orient="records"),
        "metric_note": (
            "Mean lap times are descriptive. Traffic, tyre condition, "
            "fuel load, and safety-car periods can affect race pace. "
            "The fastest recorded lap is not necessarily an official "
            "fastest-lap classification."
        ),
    }

def grand_prix_lap_times(
    season: int,
    grand_prix: str,
    drivers: list[str] | None = None,
) -> dict:
    """Return lap-by-lap timing data for selected drivers in a Grand Prix."""
    from apex.data_loader import list_datasets, load_dataset

    if not isinstance(season, int) or isinstance(season, bool):
        raise ValueError("Season must be an integer.")

    if not isinstance(grand_prix, str) or not grand_prix.strip():
        raise ValueError("Grand Prix name must be a non-empty string.")

    selected_drivers = [
        driver.strip().upper()
        for driver in (drivers or ["HAM", "VER"])
        if driver.strip()
    ]

    if not selected_drivers:
        raise ValueError("At least one driver code is required.")

    matches = [
        entry for entry in list_datasets()
        if entry["season"] == season
        and entry["session_type"] == "R"
        and entry["grand_prix"].casefold() == grand_prix.strip().casefold()
    ]

    if not matches:
        raise ValueError(
            f"No race dataset found for {grand_prix} in {season}."
        )

    matches.sort(
        key=lambda entry: (
            entry.get("status") != "imported",
            entry["dataset_id"],
        )
    )

    metadata, laps = load_dataset(matches[0]["dataset_id"])

    required = {"Driver", "lap_duration", "lap_number"}
    missing = required - set(laps.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {sorted(missing)}")

    frame = laps.copy()
    frame["Driver"] = frame["Driver"].astype("string").str.strip().str.upper()
    frame["lap_duration"] = pd.to_numeric(
        frame["lap_duration"], errors="coerce"
    )
    frame["lap_number"] = pd.to_numeric(
        frame["lap_number"], errors="coerce"
    )

    frame = frame.dropna(subset=["Driver", "lap_duration", "lap_number"])
    frame = frame[frame["lap_duration"] > 0]

    if "is_pit_out_lap" in frame.columns:
        pit_out = (
            frame["is_pit_out_lap"]
            .astype("string")
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        frame = frame[~pit_out]

    frame = frame[frame["Driver"].isin(selected_drivers)]

    if frame.empty:
        raise ValueError("No valid laps found for the selected drivers.")

    frame["lap_number"] = frame["lap_number"].astype(int)

    pivot = frame.pivot_table(
        index="lap_number",
        columns="Driver",
        values="lap_duration",
        aggfunc="mean",
    ).sort_index()

    lap_records = []
    for lap_number, row in pivot.iterrows():
        record = {"lap": int(lap_number)}
        for driver in selected_drivers:
            value = row.get(driver)
            record[driver] = (
                round(float(value), 3)
                if value is not None and pd.notna(value)
                else None
            )
        lap_records.append(record)

    return {
        "season": season,
        "grand_prix": metadata["grand_prix"],
        "dataset_id": metadata["dataset_id"],
        "drivers": selected_drivers,
        "laps": lap_records,
        "metric_note": (
            "Lap times are in seconds. Missing values mean no valid lap "
            "was available for that driver on that lap number. "
            "Traffic, tyres, fuel load, and safety cars affect lap times."
        ),
    }

def grand_prix_tyre_stints(
    season: int,
    grand_prix: str,
) -> dict:
    """Summarize driver tyre stints for a registered Grand Prix."""
    from apex.data_loader import list_datasets, load_dataset

    if not isinstance(season, int) or isinstance(season, bool):
        raise ValueError("Season must be an integer.")

    if not isinstance(grand_prix, str) or not grand_prix.strip():
        raise ValueError("Grand Prix name must be a non-empty string.")

    matches = [
        entry for entry in list_datasets()
        if entry["season"] == season
        and entry["session_type"] == "R"
        and entry["grand_prix"].casefold() == grand_prix.strip().casefold()
        and entry.get("status") == "imported"
    ]

    if not matches:
        raise ValueError(
            f"No imported race dataset found for {grand_prix} in {season}."
        )

    required_tyre_columns = {"compound", "stint", "tyre_life"}

    # Prefer the new race-specific tyre datasets.
    # Fall back to older datasets only when necessary.
    preferred_matches = sorted(
        matches,
        key=lambda entry: (
            "race_tyres" not in entry.get("dataset_id", ""),
            entry.get("dataset_id", ""),
        ),
    )

    selected = None
    laps = None

    for entry in preferred_matches:
        _, candidate = load_dataset(entry["dataset_id"])

        has_required_columns = required_tyre_columns.issubset(
            candidate.columns
        )
        if has_required_columns:
            selected = entry
            laps = candidate
            break

    if selected is None or laps is None:
        raise ValueError(
            f"No tyre metadata is available for {grand_prix} in {season}."
        )

    frame = laps.copy()

    frame["Driver"] = (
        frame["Driver"].astype("string").str.strip().str.upper()
    )

    for column in (
        "lap_number",
        "lap_duration",
        "stint",
        "tyre_life",
    ):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame = frame.dropna(
        subset=["Driver", "lap_number", "lap_duration", "stint"]
    )

    frame = frame[
        (frame["lap_duration"] > 0)
        & (frame["lap_number"] > 0)
        & (frame["stint"] > 0)
    ]

    if frame.empty:
        raise ValueError("No valid tyre stint records were found.")

    frame["stint"] = frame["stint"].astype(int)
    frame["lap_number"] = frame["lap_number"].astype(int)

    if "compound" not in frame.columns:
        frame["compound"] = pd.NA

    frame["compound"] = (
        frame["compound"].astype("string").str.upper()
    )

    if "is_pit_out_lap" in frame.columns:
        pit_out = (
            frame["is_pit_out_lap"]
            .astype("string")
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        )
    else:
        pit_out = pd.Series(False, index=frame.index)

    frame["is_pit_out_lap_normalized"] = pit_out

    summaries = []

    for driver, driver_laps in frame.groupby("Driver", sort=True):
        driver_laps = driver_laps.sort_values(
            ["lap_number", "stint"]
        )

        for stint_number, group in driver_laps.groupby(
            "stint", sort=True
        ):
            valid_laps = group.sort_values("lap_number")

            compound_values = (
                valid_laps["compound"].dropna().unique().tolist()
            )

            tyre_life = valid_laps["tyre_life"].dropna()

            pit_in = pd.to_numeric(
                valid_laps.get(
                    "pit_in_time_seconds",
                    pd.Series(index=valid_laps.index, dtype=float),
                ),
                errors="coerce",
            ).dropna()

            pit_out_times = pd.to_numeric(
                valid_laps.loc[
                    valid_laps["is_pit_out_lap_normalized"],
                    "pit_out_time_seconds",
                ],
                errors="coerce",
            ).dropna()

            summaries.append({
                "driver": str(driver),
                "stint": int(stint_number),
                "compound": (
                    compound_values[0] if compound_values else None
                ),
                "start_lap": int(valid_laps["lap_number"].min()),
                "end_lap": int(valid_laps["lap_number"].max()),
                "lap_records": int(len(valid_laps)),
                "mean_lap_seconds": round(
                    float(valid_laps["lap_duration"].mean()), 3
                ),
                "median_lap_seconds": round(
                    float(valid_laps["lap_duration"].median()), 3
                ),
                "tyre_life_start": (
                    float(tyre_life.iloc[0])
                    if not tyre_life.empty else None
                ),
                "tyre_life_end": (
                    float(tyre_life.iloc[-1])
                    if not tyre_life.empty else None
                ),
                "pit_in_session_seconds": (
                    round(float(pit_in.iloc[-1]), 3)
                    if not pit_in.empty else None
                ),
                "pit_out_session_seconds": (
                    round(float(pit_out_times.iloc[0]), 3)
                    if not pit_out_times.empty else None
                ),
                "pit_out_lap_records": int(
                    valid_laps["is_pit_out_lap_normalized"].sum()
                ),
            })

    # Link each stint to the pit transition that entered it.
    previous_stints = {}

    for summary in summaries:
        driver = summary["driver"]
        previous = previous_stints.get(driver)

        if previous is not None:
            summary["pit_transition"] = {
                "from_stint": previous["stint"],
                "to_stint": summary["stint"],
                "pit_in_session_seconds": previous[
                    "pit_in_session_seconds"
                ],
                "pit_out_session_seconds": summary[
                    "pit_out_session_seconds"
                ],
            }
        else:
            summary["pit_transition"] = None

        previous_stints[driver] = summary

    return {
        "season": season,
        "grand_prix": selected["grand_prix"],
        "dataset_id": selected["dataset_id"],
        "stints": summaries,
        "metric_note": (
            "Stint summaries use available timed lap records. Lap-record "
            "counts are not guaranteed to equal official stint lengths. "
            "Pit-in and pit-out values are session-relative timestamps, "
            "not stationary pit-stop durations. Lap times are affected by "
            "traffic, weather, fuel load, safety cars, and track conditions."
        ),
    }

def grand_prix_tyre_degradation(
    season: int,
    grand_prix: str,
) -> dict:
    """
    Analyse lap-time degradation against tyre age for each
    driver and stint in a registered Grand Prix.

    Degradation is estimated using linear regression within
    each individual stint.
    """
    from apex.data_loader import list_datasets, load_dataset

    if not isinstance(season, int) or isinstance(season, bool):
        raise ValueError("Season must be an integer.")

    if not isinstance(grand_prix, str) or not grand_prix.strip():
        raise ValueError("Grand Prix name must be a non-empty string.")

    # Find imported race datasets for this Grand Prix.
    matches = [
        entry for entry in list_datasets()
        if entry["season"] == season
        and entry["session_type"] == "R"
        and entry["grand_prix"].casefold() == grand_prix.strip().casefold()
        and entry.get("status") == "imported"
    ]

    if not matches:
        raise ValueError(
            f"No imported race dataset found for {grand_prix} in {season}."
        )

    # Prefer the race-specific tyre dataset.
    preferred_matches = sorted(
        matches,
        key=lambda entry: (
            "race_tyres" not in entry.get("dataset_id", ""),
            entry.get("dataset_id", ""),
        ),
    )

    required = {
        "Driver",
        "lap_number",
        "lap_duration",
        "compound",
        "stint",
        "tyre_life",
    }

    selected = None
    laps = None

    for entry in preferred_matches:
        _, candidate = load_dataset(entry["dataset_id"])

        if required.issubset(candidate.columns):
            selected = entry
            laps = candidate
            break

    if selected is None or laps is None:
        raise ValueError(
            f"No tyre degradation metadata is available for "
            f"{grand_prix} in {season}."
        )

    frame = laps.copy()

    # Normalize driver identifiers.
    frame["Driver"] = (
        frame["Driver"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # Convert numerical fields safely.
    for column in (
        "lap_number",
        "lap_duration",
        "stint",
        "tyre_life",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "Driver",
            "lap_number",
            "lap_duration",
            "stint",
            "tyre_life",
        ]
    )

    frame = frame[
        (frame["lap_number"] > 0)
        & (frame["lap_duration"] > 0)
        & (frame["stint"] > 0)
        & (frame["tyre_life"] >= 0)
    ].copy()

    # Normalize compound names.
    frame["compound"] = (
        frame["compound"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    frame = frame[
        frame["compound"].notna()
        & ~frame["compound"].isin(["", "NONE", "NAN", "UNKNOWN"])
    ].copy()

    # Exclude pit-out laps because they are not representative
    # of normal racing pace.
    if "is_pit_out_lap" in frame.columns:
        pit_out = (
            frame["is_pit_out_lap"]
            .astype("string")
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        frame = frame[~pit_out].copy()

    if frame.empty:
        raise ValueError(
            "No valid tyre degradation lap records were found."
        )

    frame["stint"] = frame["stint"].astype(int)

    stint_results = []

    # Analyse each driver and stint independently.
    for (driver, stint_number), group in frame.groupby(
        ["Driver", "stint"],
        sort=True,
    ):
        group = group.sort_values("tyre_life").copy()

        compounds = group["compound"].dropna().unique().tolist()

        # A stint should use one compound. Do not combine
        # records if the source data contains conflicting compounds.
        if len(compounds) != 1:
            continue

        ages = group["tyre_life"].to_numpy(dtype=float)
        durations = group["lap_duration"].to_numpy(dtype=float)

        unique_ages = np.unique(ages)

        degradation_rate = None
        r_squared = None

        # Require at least 3 distinct tyre ages.
        if len(unique_ages) >= 3 and len(group) >= 3:
            slope, intercept = np.polyfit(
                ages,
                durations,
                1,
            )

            predicted = intercept + slope * ages

            ss_res = float(
                np.sum((durations - predicted) ** 2)
            )
            ss_tot = float(
                np.sum((durations - durations.mean()) ** 2)
            )

            degradation_rate = round(float(slope), 4)

            if ss_tot > 0:
                r_squared = round(
                    float(1 - ss_res / ss_tot),
                    4,
                )

        stint_results.append({
            "driver": str(driver),
            "stint": int(stint_number),
            "compound": str(compounds[0]),
            "start_lap": int(group["lap_number"].min()),
            "end_lap": int(group["lap_number"].max()),
            "tyre_age_start": round(float(ages.min()), 2),
            "tyre_age_end": round(float(ages.max()), 2),
            "valid_laps": int(len(group)),
            "mean_lap_seconds": round(
                float(group["lap_duration"].mean()),
                3,
            ),
            "median_lap_seconds": round(
                float(group["lap_duration"].median()),
                3,
            ),
            "degradation_seconds_per_lap": degradation_rate,
            "r_squared": r_squared,
            "regression_status": (
                "calculated"
                if degradation_rate is not None
                else "insufficient_data"
            ),
        })

    if not stint_results:
        raise ValueError(
            "No valid driver tyre stints were available for analysis."
        )

    # Aggregate compound performance using valid lap records.
    compound_results = []

    for compound, group in frame.groupby("compound", sort=True):
        matching_stints = [
            item for item in stint_results
            if item["compound"] == compound
        ]

        rates = [
            item["degradation_seconds_per_lap"]
            for item in matching_stints
            if item["degradation_seconds_per_lap"] is not None
        ]

        compound_results.append({
            "compound": str(compound),
            "drivers": int(group["Driver"].nunique()),
            "stints": int(len(matching_stints)),
            "valid_laps": int(len(group)),
            "mean_lap_seconds": round(
                float(group["lap_duration"].mean()),
                3,
            ),
            "mean_degradation_seconds_per_lap": (
                round(float(np.mean(rates)), 4)
                if rates else None
            ),
            "stints_with_degradation": int(len(rates)),
        })

    return {
        "season": season,
        "grand_prix": selected["grand_prix"],
        "dataset_id": selected["dataset_id"],
        "total_valid_laps": int(len(frame)),
        "stints": stint_results,
        "compound_comparison": compound_results,
        "metric_note": (
            "Degradation is estimated using linear regression of "
            "lap time against tyre age within each individual stint. "
            "At least three distinct tyre ages are required. "
            "Positive values indicate increasing lap times as tyres age. "
            "Negative values indicate decreasing fitted lap times. "
            "Lap times are also affected by fuel load, traffic, weather, "
            "track evolution, driver behaviour and race conditions. "
            "The regression slope is an observed association, not "
            "a pure causal measurement of tyre degradation."
        ),
    }

def grand_prix_tyre_degradation_v2(
    season: int,
    grand_prix: str,
) -> dict:
    """
    Tyre degradation analysis v2.1.

    Provides:
    - Ordinary linear regression baseline.
    - Theil-Sen robust regression.
    - MAD-based outlier detection.
    - Sector-level degradation estimates.
    - Statistical fit quality.
    - Data sufficiency classification.
    - Lap-time trend classification.
    - Context warnings for interpretation.
    """

    from apex.data_loader import list_datasets, load_dataset
    from scipy.stats import theilslopes

    if not isinstance(season, int) or isinstance(season, bool):
        raise ValueError("Season must be an integer.")

    if not isinstance(grand_prix, str) or not grand_prix.strip():
        raise ValueError("Grand Prix name must be a non-empty string.")

    matches = [
        entry for entry in list_datasets()
        if entry["season"] == season
        and entry["session_type"] == "R"
        and entry["grand_prix"].casefold() == grand_prix.strip().casefold()
        and entry.get("status") == "imported"
    ]

    if not matches:
        raise ValueError(
            f"No imported race dataset found for {grand_prix} in {season}."
        )

    matches.sort(
        key=lambda entry: (
            "race_tyres" not in entry.get("dataset_id", ""),
            entry.get("dataset_id", ""),
        )
    )

    required = {
        "Driver",
        "lap_number",
        "lap_duration",
        "compound",
        "stint",
        "tyre_life",
    }

    selected = None
    laps = None

    for entry in matches:
        _, candidate = load_dataset(entry["dataset_id"])

        if required.issubset(candidate.columns):
            selected = entry
            laps = candidate
            break

    if selected is None or laps is None:
        raise ValueError(
            f"No tyre degradation metadata is available for "
            f"{grand_prix} in {season}."
        )

    frame = laps.copy()

    frame["Driver"] = (
        frame["Driver"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    numeric_columns = [
        "lap_number",
        "lap_duration",
        "stint",
        "tyre_life",
        "duration_sector_1",
        "duration_sector_2",
        "duration_sector_3",
    ]

    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

    frame = frame.dropna(
        subset=[
            "Driver",
            "lap_number",
            "lap_duration",
            "stint",
            "tyre_life",
        ]
    )

    frame = frame[
        (frame["lap_number"] > 0)
        & (frame["lap_duration"] > 0)
        & (frame["stint"] > 0)
        & (frame["tyre_life"] >= 0)
    ].copy()

    frame["compound"] = (
        frame["compound"]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    frame = frame[
        frame["compound"].notna()
        & ~frame["compound"].isin(
            ["", "NONE", "NAN", "UNKNOWN"]
        )
    ].copy()

    if "is_pit_out_lap" in frame.columns:
        pit_out = (
            frame["is_pit_out_lap"]
            .astype("string")
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        )
        frame = frame[~pit_out].copy()

    if frame.empty:
        raise ValueError(
            "No valid tyre degradation lap records were found."
        )

    frame["stint"] = frame["stint"].astype(int)

    def calculate_regression(x_values, y_values):
        """Calculate ordinary and robust regression metrics."""

        x = np.asarray(x_values, dtype=float)
        y = np.asarray(y_values, dtype=float)

        valid = np.isfinite(x) & np.isfinite(y)
        x = x[valid]
        y = y[valid]

        result = {
            "valid_laps": int(len(x)),
            "unique_tyre_ages": int(len(np.unique(x))),
            "linear_slope": None,
            "linear_r_squared": None,
            "robust_slope": None,
            "robust_intercept": None,
            "outlier_count": 0,
            "outlier_indices": [],
        }

        if len(x) < 3 or len(np.unique(x)) < 3:
            return result

        # Ordinary least-squares regression.
        linear_slope, linear_intercept = np.polyfit(x, y, 1)
        linear_predictions = linear_intercept + linear_slope * x

        ss_res = float(
            np.sum((y - linear_predictions) ** 2)
        )
        ss_tot = float(
            np.sum((y - y.mean()) ** 2)
        )

        linear_r_squared = (
            1 - ss_res / ss_tot
            if ss_tot > 0 else None
        )

        # Theil-Sen robust regression.
        robust_slope, robust_intercept, _, _ = theilslopes(
            y,
            x,
        )

        robust_predictions = robust_intercept + robust_slope * x

        # Robust residual outlier detection using MAD.
        residuals = y - robust_predictions
        residual_median = float(np.median(residuals))

        absolute_deviations = np.abs(
            residuals - residual_median
        )

        mad = float(np.median(absolute_deviations))

        outlier_indices = []

        if mad > 0:
            robust_sigma = 1.4826 * mad

            outlier_indices = np.where(
                absolute_deviations > 3.5 * robust_sigma
            )[0].tolist()

        result.update({
            "linear_slope": round(float(linear_slope), 4),
            "linear_r_squared": (
                round(float(linear_r_squared), 4)
                if linear_r_squared is not None else None
            ),
            "robust_slope": round(float(robust_slope), 4),
            "robust_intercept": round(float(robust_intercept), 4),
            "outlier_count": len(outlier_indices),
            "outlier_indices": outlier_indices,
        })

        return result

    def classify_reliability(
        valid_laps,
        unique_ages,
        r_squared,
        outlier_count,
    ):
        """Classify the strength of a degradation estimate."""

        if valid_laps < 5 or unique_ages < 4:
            return "low"

        if r_squared is None:
            return "low"

        outlier_ratio = outlier_count / valid_laps

        if (
            valid_laps >= 10
            and unique_ages >= 7
            and r_squared >= 0.70
            and outlier_ratio <= 0.10
        ):
            return "high"

        if (
            valid_laps >= 6
            and unique_ages >= 5
            and r_squared >= 0.40
            and outlier_ratio <= 0.25
        ):
            return "medium"

        return "low"

    stint_results = []

    sector_columns = {
        "sector_1": "duration_sector_1",
        "sector_2": "duration_sector_2",
        "sector_3": "duration_sector_3",
    }

    for (driver, stint_number), group in frame.groupby(
        ["Driver", "stint"],
        sort=True,
    ):
        group = group.sort_values(
            ["tyre_life", "lap_number"]
        ).copy()

        compounds = group["compound"].dropna().unique().tolist()

        if len(compounds) != 1:
            continue

        ages = group["tyre_life"].to_numpy(dtype=float)
        durations = group["lap_duration"].to_numpy(dtype=float)

        regression = calculate_regression(ages, durations)

        outlier_laps = [
            int(group.iloc[index]["lap_number"])
            for index in regression["outlier_indices"]
        ]

        robust_slope = regression["robust_slope"]
        linear_slope = regression["linear_slope"]
        r_squared = regression["linear_r_squared"]

        reliability = classify_reliability(
            regression["valid_laps"],
            regression["unique_tyre_ages"],
            r_squared,
            regression["outlier_count"],
        )

        sector_results = {}

        for sector_name, column in sector_columns.items():
            if column not in group.columns:
                continue

            sector_data = group.dropna(
                subset=[column]
            )

            sector_regression = calculate_regression(
                sector_data["tyre_life"],
                sector_data[column],
            )

            sector_results[sector_name] = {
                "valid_laps": sector_regression["valid_laps"],
                "linear_degradation_seconds_per_lap": (
                    sector_regression["linear_slope"]
                ),
                "robust_degradation_seconds_per_lap": (
                    sector_regression["robust_slope"]
                ),
                "r_squared": sector_regression["linear_r_squared"],
            }

        stint_results.append({
            "driver": str(driver),
            "stint": int(stint_number),
            "compound": str(compounds[0]),
            "start_lap": int(group["lap_number"].min()),
            "end_lap": int(group["lap_number"].max()),
            "tyre_age_start": round(float(ages.min()), 2),
            "tyre_age_end": round(float(ages.max()), 2),
            "valid_laps": regression["valid_laps"],
            "mean_lap_seconds": round(
                float(group["lap_duration"].mean()), 3
            ),
            "median_lap_seconds": round(
                float(group["lap_duration"].median()), 3
            ),
            "raw_degradation_seconds_per_lap": linear_slope,
            "raw_r_squared": r_squared,
            "robust_degradation_seconds_per_lap": robust_slope,
            "outlier_count": regression["outlier_count"],
            "outlier_laps": outlier_laps,
                        "reliability": reliability,

            "statistical_fit_quality": (
                "high" if r_squared is not None and r_squared >= 0.70
                else "medium" if r_squared is not None and r_squared >= 0.40
                else "low"
            ),

            "data_sufficiency": (
                "high"
                if regression["valid_laps"] >= 10
                and regression["unique_tyre_ages"] >= 7
                else "medium"
                if regression["valid_laps"] >= 6
                and regression["unique_tyre_ages"] >= 5
                else "low"
            ),

            "tyre_wear_interpretation": "uncertain",

            "lap_time_trend": (
                "increasing"
                if robust_slope is not None and robust_slope > 0.02
                else "decreasing"
                if robust_slope is not None and robust_slope < -0.02
                else "stable"
                if robust_slope is not None
                else "insufficient_data"
            ),

            "outlier_count": regression["outlier_count"],
            "outlier_laps": outlier_laps,

            "context_warnings": [
                "Weather and track-status data unavailable",
                "Lap-time changes may reflect race conditions",
                "Regression measures observed pace trends, not pure tyre wear"
            ],

            "regression_status": (
                "calculated"
                if robust_slope is not None
                else "insufficient_data"
            ),

            "sector_analysis": sector_results,
        })

    if not stint_results:
        raise ValueError(
            "No valid driver tyre stints were available for analysis."
        )

    compound_results = []

    for compound, group in frame.groupby("compound", sort=True):
        matching_stints = [
            item for item in stint_results
            if item["compound"] == compound
        ]

        robust_rates = [
            item["robust_degradation_seconds_per_lap"]
            for item in matching_stints
            if item["robust_degradation_seconds_per_lap"] is not None
        ]

        raw_rates = [
            item["raw_degradation_seconds_per_lap"]
            for item in matching_stints
            if item["raw_degradation_seconds_per_lap"] is not None
        ]

        compound_results.append({
            "compound": str(compound),
            "drivers": int(group["Driver"].nunique()),
            "stints": int(len(matching_stints)),
            "valid_laps": int(len(group)),
            "mean_lap_seconds": round(
                float(group["lap_duration"].mean()), 3
            ),
            "mean_raw_degradation_seconds_per_lap": (
                round(float(np.mean(raw_rates)), 4)
                if raw_rates else None
            ),
            "mean_robust_degradation_seconds_per_lap": (
                round(float(np.mean(robust_rates)), 4)
                if robust_rates else None
            ),
            "stints_with_degradation": int(len(robust_rates)),
        })

    return {
        "season": season,
        "grand_prix": selected["grand_prix"],
        "dataset_id": selected["dataset_id"],
        "analysis_version": "2.1",
        "total_valid_laps": int(len(frame)),
        "total_stints": int(len(stint_results)),
        "stints": stint_results,
        "compound_comparison": compound_results,
        "metric_note": (
            "Raw degradation is estimated using ordinary least-squares "
            "regression. Robust degradation uses the Theil-Sen estimator. "
            "Outliers are flagged using median absolute deviation (MAD) "
            "of robust-regression residuals and are not automatically "
            "removed. Sector estimates are calculated independently. "
            "Reliability reflects sample size, tyre-age coverage, linear "
            "fit and outlier proportion. These metrics measure observed "
            "lap-time trends, not pure causal tyre wear. Fuel load, traffic, "
            "weather, track evolution, safety cars and driver behaviour "
            "can influence the results. Weather and track-status data are "
            "not available in this dataset."
        ),
    }
