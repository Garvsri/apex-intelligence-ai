
import pandas as pd
import pytest

from apex import ingestion


class FakeSession:
    def __init__(self, laps):
        self.laps = laps

    def load(self, **kwargs):
        return None


def sample_laps():
    return pd.DataFrame({
        "Driver": ["HAM"],
        "DriverNumber": [44],
        "LapNumber": [1],
        "LapTime": [pd.Timedelta(90, unit="s")],
        "Sector1Time": [pd.Timedelta(30, unit="s")],
        "Sector2Time": [pd.Timedelta(35, unit="s")],
        "Sector3Time": [pd.Timedelta(25, unit="s")],
        "PitOutTime": [pd.NaT],
    })


def test_ingestion_registers_dataset(tmp_path, monkeypatch):
    processed = tmp_path / "processed"
    processed.mkdir()
    manifest_path = processed / "manifest.json"
    manifest_path.write_text('{"datasets": []}', encoding="utf-8")

    monkeypatch.setattr(ingestion, "PROCESSED_DATA_DIR", processed)
    monkeypatch.setattr(ingestion, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(
        ingestion,
        "load_manifest",
        lambda: {"datasets": []},
    )
    monkeypatch.setattr(
        ingestion.fastf1,
        "get_session",
        lambda *args: FakeSession(sample_laps()),
    )

    result = ingestion.ingest_f1_session(
        2024, "British Grand Prix", "R", "test_2024_race"
    )

    assert result["rows_imported"] == 1
    assert (processed / "test_2024_race.csv").exists()
    assert len(
        __import__("json").loads(
            manifest_path.read_text(encoding="utf-8")
        )["datasets"]
    ) == 1


def test_ingestion_rejects_duplicate_id(monkeypatch):
    monkeypatch.setattr(
        ingestion,
        "load_manifest",
        lambda: {"datasets": [{"dataset_id": "existing"}]},
    )

    with pytest.raises(ValueError, match="already registered"):
        ingestion.ingest_f1_session(
            2024, "British Grand Prix", "R", "existing"
        )
