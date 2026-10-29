import json
from pathlib import Path
from datetime import date

import fastf1
import pandas as pd

from apex.data_loader import (
    MANIFEST_PATH,
    PROCESSED_DATA_DIR,
    REQUIRED_COLUMNS,
    load_manifest,
)
def normalize_fastf1_laps(laps: pd.DataFrame) -> pd.DataFrame:
    """Normalize FastF1 lap timing plus optional tyre and pit metadata."""
    required_source_columns = {
        "Driver",
        "DriverNumber",
        "LapNumber",
        "LapTime",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
    }

    missing = required_source_columns - set(laps.columns)
    if missing:
        raise ValueError(
            f"FastF1 data is missing columns: {sorted(missing)}"
        )

    # Optional fields are handled gracefully when older data lacks them.
    pit_out = (
        laps["PitOutTime"]
        if "PitOutTime" in laps.columns
        else pd.Series(pd.NaT, index=laps.index)
    )
    pit_in = (
        laps["PitInTime"]
        if "PitInTime" in laps.columns
        else pd.Series(pd.NaT, index=laps.index)
    )

    normalized = pd.DataFrame({
        "Driver": laps["Driver"],
        "driver_number": laps["DriverNumber"],
        "lap_number": laps["LapNumber"],
        "lap_duration": laps["LapTime"].map(_seconds),
        "duration_sector_1": laps["Sector1Time"].map(_seconds),
        "duration_sector_2": laps["Sector2Time"].map(_seconds),
        "duration_sector_3": laps["Sector3Time"].map(_seconds),
        "is_pit_out_lap": pit_out.notna(),
        "compound": (
            laps["Compound"].astype("string").str.upper()
            if "Compound" in laps.columns
            else pd.Series(pd.NA, index=laps.index, dtype="string")
        ),
        "tyre_life": (
            pd.to_numeric(laps["TyreLife"], errors="coerce")
            if "TyreLife" in laps.columns
            else pd.Series(float("nan"), index=laps.index)
        ),
        "stint": (
            pd.to_numeric(laps["Stint"], errors="coerce")
            if "Stint" in laps.columns
            else pd.Series(float("nan"), index=laps.index)
        ),
        "pit_in_time_seconds": pit_in.map(_seconds),
        "pit_out_time_seconds": pit_out.map(_seconds),
    })

    normalized["Driver"] = (
        normalized["Driver"].astype("string").str.strip().str.upper()
    )

    for column in (
        "driver_number",
        "lap_number",
        "lap_duration",
        "duration_sector_1",
        "duration_sector_2",
        "duration_sector_3",
        "tyre_life",
        "stint",
        "pit_in_time_seconds",
        "pit_out_time_seconds",
    ):
        normalized[column] = pd.to_numeric(
            normalized[column], errors="coerce"
        )

    normalized = normalized.dropna(subset=["Driver", "lap_duration"])
    normalized = normalized[normalized["lap_duration"] > 0]

    if normalized.empty:
        raise ValueError("No valid timed laps were found.")

    if not REQUIRED_COLUMNS.issubset(normalized.columns):
        raise ValueError("Normalized data does not match Apex's schema.")

    return normalized.reset_index(drop=True)

def ingest_f1_session(
    year: int,
    grand_prix: str | int,
    session_type: str,
    dataset_id: str,
    *,
    force_download: bool = False,
) -> dict:
    """Download, normalize, save, and register an F1 session."""
    valid_sessions = {"FP1", "FP2", "FP3", "Q", "SQ", "S", "R"}

    if session_type not in valid_sessions:
        raise ValueError(f"Unsupported session type: {session_type}")

    if not dataset_id or not dataset_id.strip():
        raise ValueError("dataset_id must not be empty.")

    if Path(dataset_id).name != dataset_id:
        raise ValueError("dataset_id must be a simple identifier.")

    manifest = load_manifest()
    existing_ids = {
        entry["dataset_id"] for entry in manifest["datasets"]
    }

    if dataset_id in existing_ids:
        raise ValueError(f"Dataset already registered: {dataset_id}")

    filename = f"{dataset_id}.csv"
    destination = PROCESSED_DATA_DIR / filename

    if destination.exists():
        raise FileExistsError(
            f"Destination already exists: {destination}"
        )

    session = fastf1.get_session(year, grand_prix, session_type)
    session.load(
        laps=True,
        telemetry=False,
        weather=False,
        messages=False,
    )

    if session.laps is None or session.laps.empty:
        raise ValueError("FastF1 returned no lap data for this session.")

    source_records = len(session.laps)
    valid_source_lap_times = int(session.laps["LapTime"].notna().sum())
    normalized = normalize_fastf1_laps(session.laps)
    rows_imported = len(normalized)

    quality_status = (
        "complete_timing_records"
        if rows_imported == source_records
        else "partial_timing_records"
    )

    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp.csv")

    try:
        normalized.to_csv(temporary, index=False)
        temporary.replace(destination)

        entry = {
            "dataset_id": dataset_id,
            "filename": filename,
            "season": year,
            "grand_prix": str(grand_prix),
            "session_type": session_type,
            "data_type": "lap_times",
            "source": "FastF1",
            "status": "imported",
            "quality": {
                "source_records": source_records,
                "source_records_with_lap_time": valid_source_lap_times,
                "valid_lap_records": rows_imported,
                "dropped_records": source_records - rows_imported,
                "timing_status": quality_status,
            },
        }

        manifest["datasets"].append(entry)

        manifest_temporary = MANIFEST_PATH.with_suffix(".tmp")
        try:
            manifest_temporary.write_text(
                json.dumps(manifest, indent=2),
                encoding="utf-8",
            )
            manifest_temporary.replace(MANIFEST_PATH)
        except Exception:
            if destination.exists():
                destination.unlink()
            raise

    finally:
        if temporary.exists():
            temporary.unlink()

    return {
        "dataset": entry,
        "rows_imported": rows_imported,
        "source_records": source_records,
        "dropped_records": source_records - rows_imported,
        "quality_status": quality_status,
        "csv_path": str(destination),
    }


def _seconds(value) -> float | None:
    """Convert a pandas/ datetime-like duration to seconds."""
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if hasattr(value, "total_seconds"):
        return float(value.total_seconds())

    return None


def save_normalized_laps(
    laps: pd.DataFrame,
    destination: str | Path,
) -> Path:
    """Normalize FastF1 laps and save them as a CSV."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    normalized = normalize_fastf1_laps(laps)
    normalized.to_csv(destination, index=False)

    return destination


def ingest_season(
    year: int,
    *,
    session_type: str = "R",
    force_download: bool = False,
) -> dict:
    """Import all available sessions of a given type for one season."""
    valid_sessions = {"FP1", "FP2", "FP3", "Q", "SQ", "S", "R"}

    if isinstance(year, bool) or not isinstance(year, int):
        raise ValueError("year must be an integer.")

    if year < 1950 or year > date.today().year:
        raise ValueError("year must be between 1950 and the current year.")

    if session_type not in valid_sessions:
        raise ValueError(f"Unsupported session type: {session_type}")

    schedule = fastf1.get_event_schedule(
        year,
        include_testing=False,
    )

    results = {
        "season": year,
        "session_type": session_type,
        "imported": [],
        "skipped": [],
        "failed": [],
    }

    for _, event in schedule.iterrows():
        event_name = str(event.get("EventName", "")).strip()
        round_number = event.get("RoundNumber")

        if not event_name or event_name.lower() == "nan":
            results["skipped"].append({
                "event": event_name or "Unknown event",
                "reason": "Missing event name",
            })
            continue


        # Find the requested session's date from the schedule.
        # FastF1 uses names like "Race" rather than "R".
        session_names = {
            "FP1": "Practice 1",
            "FP2": "Practice 2",
            "FP3": "Practice 3",
            "Q": "Qualifying",
            "SQ": "Sprint Qualifying",
            "S": "Sprint",
            "R": "Race",
        }
        expected_session_name = session_names[session_type]

        # Support simplified test schedules that use columns like "R".
        session_date = event.get(session_type)

        # Otherwise, match the session name in FastF1's real schedule.
        for session_num in range(1, 6):
            scheduled_name = str(
                event.get(f"Session{session_num}", "")
            ).strip()

            if scheduled_name == expected_session_name:
                session_date = event.get(f"Session{session_num}Date")
                break

        if session_date is not None and pd.notna(session_date):
            try:
                if pd.Timestamp(session_date).date() > date.today():
                    results["skipped"].append({
                        "event": event_name,
                        "reason": "Session is in the future",
                    })
                    continue
            except (TypeError, ValueError):
                pass


        safe_event_name = "".join(
            char.lower() if char.isalnum() else "_"
            for char in event_name
        ).strip("_")
        dataset_id = f"{year}_{safe_event_name}_{session_type.lower()}"

        try:
            manifest = load_manifest()
            registered = {
                item["dataset_id"]: item
                for item in manifest["datasets"]
            }

            if dataset_id in registered:
                existing = registered[dataset_id]
                existing_path = PROCESSED_DATA_DIR / existing["filename"]

                if existing_path.exists() and not force_download:
                    results["skipped"].append({
                        "event": event_name,
                        "reason": "Dataset already exists",
                        "dataset_id": dataset_id,
                    })
                    continue

                if force_download:
                    results["failed"].append({
                        "event": event_name,
                        "dataset_id": dataset_id,
                        "error": (
                            "Force replacement is not implemented; "
                            "existing data was left unchanged."
                        ),
                    })
                    continue

            if not force_download:
                expected_path = PROCESSED_DATA_DIR / f"{dataset_id}.csv"
                if expected_path.exists():
                    results["skipped"].append({
                        "event": event_name,
                        "reason": "CSV already exists but is not registered",
                    })
                    continue

            imported = ingest_f1_session(
                year=year,
                grand_prix=(
                    int(round_number)
                    if pd.notna(round_number) and int(round_number) > 0
                    else event_name
                ),
                session_type=session_type,
                dataset_id=dataset_id,
            )

            # Store the canonical event name from the schedule.
            manifest = load_manifest()
            for item in manifest["datasets"]:
                if item["dataset_id"] == dataset_id:
                    item["grand_prix"] = event_name
                    item["round_number"] = (
                        int(round_number)
                        if pd.notna(round_number)
                        else None
                    )
                    break

            manifest_temporary = MANIFEST_PATH.with_suffix(".tmp")
            try:
                manifest_temporary.write_text(
                    json.dumps(manifest, indent=2),
                    encoding="utf-8",
                )
                manifest_temporary.replace(MANIFEST_PATH)
            finally:
                if manifest_temporary.exists():
                    manifest_temporary.unlink()

            results["imported"].append({
                "event": event_name,
                **imported,
            })

        except Exception as exc:
            results["failed"].append({
                "event": event_name,
                "dataset_id": dataset_id,
                "error": str(exc),
            })

    results["summary"] = {
        "imported": len(results["imported"]),
        "skipped": len(results["skipped"]),
        "failed": len(results["failed"]),
    }

    return results
