
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DATA_DIR = ROOT / "data" / "processed"
MANIFEST_PATH = PROCESSED_DATA_DIR / "manifest.json"

BRITISH_GP_2024_PATH = (
    PROCESSED_DATA_DIR / "british_gp_2024_laps.csv"
)

REQUIRED_COLUMNS = {
    "Driver",
    "driver_number",
    "lap_number",
    "lap_duration",
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
    "is_pit_out_lap",
}

NUMERIC_COLUMNS = (
    "driver_number",
    "lap_number",
    "lap_duration",
    "duration_sector_1",
    "duration_sector_2",
    "duration_sector_3",
)

VALID_SESSION_TYPES = {"FP1", "FP2", "FP3", "Q", "SQ", "S", "R"}


def list_datasets() -> list[dict]:
    """List datasets registered in the manifest."""
    manifest = load_manifest()
    return manifest["datasets"]


def load_manifest() -> dict:
    """Read and validate the dataset manifest."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"Dataset manifest not found: {MANIFEST_PATH}"
        )

    try:
        with MANIFEST_PATH.open("r", encoding="utf-8-sig") as file:
            manifest = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError("Dataset manifest contains invalid JSON.") from exc

    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object.")

    datasets = manifest.get("datasets")
    if not isinstance(datasets, list):
        raise ValueError("Manifest must contain a datasets list.")

    seen_ids = set()
    seen_filenames = set()

    for entry in datasets:
        if not isinstance(entry, dict):
            raise ValueError("Each dataset entry must be an object.")

        required = {
            "dataset_id",
            "filename",
            "season",
            "grand_prix",
            "session_type",
            "data_type",
        }
        missing = required - set(entry)
        if missing:
            raise ValueError(
                f"Dataset entry missing fields: {sorted(missing)}"
            )

        dataset_id = entry["dataset_id"]
        filename = entry["filename"]

        if not isinstance(dataset_id, str) or not dataset_id.strip():
            raise ValueError("Dataset ID must be a non-empty string.")

        if not isinstance(filename, str) or not filename.strip():
            raise ValueError("Dataset filename must be a non-empty string.")

        if dataset_id in seen_ids:
            raise ValueError(f"Duplicate dataset ID: {dataset_id}")

        if filename in seen_filenames:
            raise ValueError(f"Duplicate dataset filename: {filename}")

        if (
            not isinstance(entry["season"], int)
            or isinstance(entry["season"], bool)
            or entry["season"] < 1950
        ):
            raise ValueError(f"Invalid season for dataset: {dataset_id}")

        if not isinstance(entry["grand_prix"], str) or not entry["grand_prix"].strip():
            raise ValueError(f"Invalid Grand Prix name: {dataset_id}")

        if entry["session_type"] not in VALID_SESSION_TYPES:
            raise ValueError(
                f"Invalid session type for dataset: {dataset_id}"
            )

        if entry["data_type"] != "lap_times":
            raise ValueError(
                f"Unsupported data type for dataset: {dataset_id}"
            )

        # Prevent manifest entries from pointing outside processed data.
        if Path(filename).name != filename:
            raise ValueError(
                f"Dataset filename must be a simple filename: {filename}"
            )

        seen_ids.add(dataset_id)
        seen_filenames.add(filename)

    return manifest


def load_laps(
    path: str | Path = BRITISH_GP_2024_PATH,
) -> pd.DataFrame:
    """Load and validate a processed F1 lap dataset."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Lap dataset not found: {path}")

    laps = pd.read_csv(path)

    missing = REQUIRED_COLUMNS - set(laps.columns)
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {sorted(missing)}"
        )

    if laps.empty:
        raise ValueError("Lap dataset contains no records.")

    laps["Driver"] = (
        laps["Driver"].astype("string").str.strip().str.upper()
    )

    if laps["Driver"].isna().any() or laps["Driver"].eq("").any():
        raise ValueError("Dataset contains missing driver codes.")

    for column in NUMERIC_COLUMNS:
        laps[column] = pd.to_numeric(laps[column], errors="coerce")

    if laps["lap_duration"].isna().any():
        raise ValueError("Dataset contains invalid lap durations.")

    if (laps["lap_duration"] <= 0).any():
        raise ValueError("Dataset contains non-positive lap durations.")

    return laps


def load_dataset(dataset_id: str) -> tuple[dict, pd.DataFrame]:
    """Load a registered dataset and its metadata."""
    manifest = load_manifest()

    matches = [
        entry for entry in manifest["datasets"]
        if entry["dataset_id"] == dataset_id
    ]

    if not matches:
        raise KeyError(f"Unknown dataset ID: {dataset_id}")

    metadata = matches[0]
    path = PROCESSED_DATA_DIR / metadata["filename"]

    if not path.is_file():
        raise FileNotFoundError(
            f"Registered dataset file not found: {path}"
        )

    return metadata.copy(), load_laps(path)
