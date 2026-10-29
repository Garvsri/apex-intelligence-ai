
import pandas as pd


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

    # Prefer a dataset with actual tyre metadata.
    selected = None
    laps = None

    for entry in matches:
        _, candidate = load_dataset(entry["dataset_id"])
        if required_tyre_columns.issubset(candidate.columns):
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

