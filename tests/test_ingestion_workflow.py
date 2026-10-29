
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
        "Driver": ["HAM", "VER"],
        "DriverNumber": [44, 1],
        "LapNumber": [1, 2],
        "LapTime": [
            pd.Timedelta(90, unit="s"),
            pd.Timedelta(91, unit="s"),
        ],
        "Sector1Time": [
            pd.Timedelta(30, unit="s"),
            pd.Timedelta(31, unit="s"),
        ],
        "Sector2Time": [
            pd.Timedelta(35, unit="s"),
            pd.Timedelta(35, unit="s"),
        ],
        "Sector3Time": [
            pd.Timedelta(25, unit="s"),
            pd.Timedelta(25, unit="s"),
        ],
        "PitOutTime": [pd.NaT, pd.Timedelta(400, unit="s")],
        "PitInTime": [pd.NaT, pd.NaT],
        "Compound": ["MEDIUM", "SOFT"],
        "TyreLife": [3.0, 1.0],
        "Stint": [1, 2],
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

    assert result["rows_imported"] == 2
    assert (processed / "test_2024_race.csv").exists()

    # Verify the tyre and pit metadata was saved to CSV.
    saved = pd.read_csv(processed / "test_2024_race.csv")

    assert saved.loc[0, "compound"] == "MEDIUM"
    assert saved.loc[1, "compound"] == "SOFT"
    assert saved.loc[0, "tyre_life"] == 3.0
    assert saved.loc[1, "stint"] == 2
    assert bool(saved.loc[1, "is_pit_out_lap"])
    assert "pit_in_time_seconds" in saved.columns
    assert "pit_out_time_seconds" in saved.columns

    # Verify the dataset was registered in the manifest.
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
