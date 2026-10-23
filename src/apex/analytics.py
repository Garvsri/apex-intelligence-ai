
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

    selected = selected.dropna(
        subset=["lap_duration"]
    )

    averages = selected.groupby(
        "Driver"
    )["lap_duration"].mean()

    result = {}

    for driver in [driver_a, driver_b]:
        result[driver] = {
            "mean_lap_seconds": (
                round(float(averages[driver]), 3)
                if driver in averages.index
                else None
            ),
            "valid_laps": int(
                (selected["Driver"] == driver).sum()
            ),
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
