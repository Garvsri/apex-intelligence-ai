
import json

import pytest

from apex import data_loader


def valid_manifest_entry():
    return {
        "dataset_id": "test_race",
        "filename": "test_race.csv",
        "season": 2024,
        "grand_prix": "Test Grand Prix",
        "session_type": "R",
        "data_type": "lap_times",
    }


def write_manifest(tmp_path, entries, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"datasets": entries}),
        encoding="utf-8",
    )
    monkeypatch.setattr(data_loader, "MANIFEST_PATH", manifest_path)


def test_duplicate_dataset_ids_are_rejected(tmp_path, monkeypatch):
    entry = valid_manifest_entry()
    duplicate = {**entry, "filename": "another_race.csv"}
    write_manifest(tmp_path, [entry, duplicate], monkeypatch)

    with pytest.raises(ValueError, match="Duplicate dataset ID"):
        data_loader.load_manifest()


def test_invalid_session_type_is_rejected(tmp_path, monkeypatch):
    entry = valid_manifest_entry()
    entry["session_type"] = "INVALID"
    write_manifest(tmp_path, [entry], monkeypatch)

    with pytest.raises(ValueError, match="Invalid session type"):
        data_loader.load_manifest()


def test_missing_registered_csv_is_rejected(tmp_path, monkeypatch):
    entry = valid_manifest_entry()
    write_manifest(tmp_path, [entry], monkeypatch)

    monkeypatch.setattr(
        data_loader, "PROCESSED_DATA_DIR", tmp_path
    )

    with pytest.raises(FileNotFoundError, match="Registered dataset file"):
        data_loader.load_dataset("test_race")
