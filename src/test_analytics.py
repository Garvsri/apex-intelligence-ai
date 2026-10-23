
from pathlib import Path

import pandas as pd
from apex.analytics import compare_driver_pace

ROOT = Path(__file__).resolve().parents[1]

laps = pd.read_csv(
    ROOT / "data" / "processed" / "british_gp_2024_laps.csv"
)

result = compare_driver_pace(laps, "HAM", "VER")

print("Apex Intelligence AI — Analytics Test")
print(result)

assert result["HAM"]["valid_laps"] > 0
assert result["VER"]["valid_laps"] > 0
assert result["mean_gap_seconds"] is not None

print("All checks passed!")
