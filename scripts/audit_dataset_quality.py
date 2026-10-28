import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
MANIFEST_PATH = DATA_DIR / "manifest.json"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
datasets = manifest.get("datasets", manifest)
items = list(datasets.values()) if isinstance(datasets, dict) else datasets

results = []
issues = []

for entry in items:
    dataset_id = entry.get("dataset_id", entry.get("id", ""))
    filename = entry.get("filename", entry.get("file", ""))

    if not filename:
        filename = f"{dataset_id}.csv"

    path = DATA_DIR / filename

    if not path.exists():
        issues.append(f"{dataset_id}: CSV not found ({filename})")
        continue

    try:
        df = pd.read_csv(path)
    except Exception as exc:
        issues.append(f"{dataset_id}: CSV read failed: {exc}")
        continue

    # Normalize column names for checking without changing the CSV.
    column_map = {str(col).strip().lower(): col for col in df.columns}
    missing_columns = {"driver", "lap_number", "lap_duration"} - set(column_map)

    if missing_columns:
        issues.append(
            f"{dataset_id}: missing required columns {sorted(missing_columns)}"
        )

    driver_col = column_map.get("driver")
    lap_col = column_map.get("lap_number")
    duration_col = column_map.get("lap_duration")

    invalid_times = 0
    duplicates = 0

    if duration_col is not None:
        lap_times = pd.to_numeric(df[duration_col], errors="coerce")
        invalid_times = int((lap_times.isna() | (lap_times <= 0)).sum())

        if invalid_times:
            issues.append(
                f"{dataset_id}: {invalid_times} missing/non-positive lap times"
            )

    duplicate_columns = [
        col for col in (driver_col, lap_col) if col is not None
    ]

    if len(duplicate_columns) == 2:
        # Only count duplicate records where both driver and lap number exist.
        valid_keys = df[duplicate_columns].notna().all(axis=1)
        duplicates = int(
            df.loc[valid_keys].duplicated(duplicate_columns).sum()
        )

        if duplicates:
            issues.append(
                f"{dataset_id}: {duplicates} duplicate driver/lap pairs"
            )

    quality = entry.get("quality") or {}
    recorded_rows = quality.get(
        "valid_lap_records",
        quality.get("saved_rows")
    )

    row_mismatch = False
    if recorded_rows is not None:
        try:
            row_mismatch = int(recorded_rows) != len(df)
        except (TypeError, ValueError):
            issues.append(
                f"{dataset_id}: invalid manifest row-count metadata "
                f"({recorded_rows!r})"
            )

    if row_mismatch:
        issues.append(
            f"{dataset_id}: CSV has {len(df)} rows; "
            f"manifest records {recorded_rows}"
        )

    results.append({
        "dataset_id": dataset_id,
        "rows": len(df),
        "drivers": int(df[driver_col].nunique())
        if driver_col is not None else None,
        "invalid_lap_times": invalid_times,
        "duplicate_driver_laps": duplicates,
        "manifest_rows": recorded_rows,
        "row_count_mismatch": row_mismatch,
    })

report_path = DATA_DIR / "quality_audit.json"
report_path.write_text(
    json.dumps({
        "datasets_checked": len(results),
        "issues_count": len(issues),
        "issues": issues,
        "results": results,
    }, indent=2),
    encoding="utf-8",
)

print(f"Datasets checked: {len(results)}")
print(f"Issues found: {len(issues)}")
print(f"Audit report: {report_path}")
for issue in issues:
    print("-", issue)
