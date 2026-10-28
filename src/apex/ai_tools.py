
from langchain.tools import tool

from apex.analytics import (
    compare_driver_pace,
    season_driver_leaderboard,
    grand_prix_driver_performance,
)
from apex.data_loader import load_laps


@tool
def compare_f1_drivers(driver_a: str, driver_b: str) -> dict:
    """Compare mean recorded lap durations for two drivers
    in the 2024 British Grand Prix.

    Use three-letter driver codes such as HAM, VER, NOR, or LEC.
    A negative mean gap means driver_a has the lower mean lap time.
    A positive mean gap means driver_b has the lower mean lap time.
    """
    try:
        laps = load_laps()
    except FileNotFoundError:
        return {"error": "The historical lap dataset is unavailable."}
    except ValueError as exc:
        return {"error": str(exc)}

    available = set(laps["Driver"].dropna().str.upper())

    driver_a = driver_a.strip().upper()
    driver_b = driver_b.strip().upper()

    if driver_a not in available or driver_b not in available:
        return {
            "error": "Unknown driver code.",
            "available_drivers": sorted(available),
        }

    return compare_driver_pace(laps, driver_a, driver_b)


@tool
def get_f1_season_leaderboard(season: int) -> dict:
    """Get the race-normalized F1 driver pace leaderboard for a season.

    Use a season year such as 2023 or 2025.
    Results include mean lap time, valid laps, races analyzed,
    and mean race pace delta in seconds. A negative pace delta
    means the driver's mean lap time was below the median of
    driver-level mean lap times at their races. This is descriptive,
    not a definitive measure of driver skill.
    """
    try:
        drivers = season_driver_leaderboard(season)
        return {
            "season": season,
            "drivers": drivers,
            "metric_note": (
                "Race-normalized pace delta compares each driver's "
                "mean lap time with the median of driver-level means "
                "at each race. It is descriptive, not a definitive "
                "ranking of driver skill."
            ),
        }
    except (ValueError, FileNotFoundError) as exc:
        return {"error": str(exc)}
@tool
def get_f1_race_performance(season: int, grand_prix: str) -> dict:
    """Get driver performance statistics for a specific Formula 1 Grand Prix.

    Use the season year and the full Grand Prix name, for example:
    season=2024, grand_prix="British Grand Prix".

    Returns fastest recorded lap, mean lap times, and valid lap counts.
    Mean lap time is descriptive and is not a definitive measure of driver skill.
    """
    try:
        return grand_prix_driver_performance(season, grand_prix)
    except (ValueError, FileNotFoundError) as exc:
        return {"error": str(exc)}