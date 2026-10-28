
from pathlib import Path

import pandas as pd

from apex.analytics import compare_driver_pace

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "processed" / "british_gp_2024_laps.csv"


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {CSV_PATH}\n"
            "Run src/first_analysis.py first."
        )

    laps = pd.read_csv(CSV_PATH)

    print("APEX INTELLIGENCE AI")
    print("2024 British Grand Prix")
    print(f"Loaded {len(laps)} lap records.\n")

    print("Available drivers:")
    print(", ".join(sorted(laps["Driver"].dropna().unique())))
    print()

    driver_a = input("Enter first driver code (e.g. HAM): ").strip().upper()
    driver_b = input("Enter second driver code (e.g. VER): ").strip().upper()

    result = compare_driver_pace(laps, driver_a, driver_b)

    print("\n--- Driver Comparison ---")
    print(f"{driver_a}: {result[driver_a]}")
    print(f"{driver_b}: {result[driver_b]}")
    print(f"Mean gap (A - B): {result['mean_gap_seconds']} seconds")


if __name__ == "__main__":
    main()
