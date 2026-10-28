
import json

import pandas as pd
import pytest

from apex import ingestion


def fake_schedule():
    return pd.DataFrame([
        {
            "EventName": "Australian Grand Prix",
            "RoundNumber": 1,
            "R": pd.Timestamp("2021-03-21"),
        },
        {
            "EventName": "Future Grand Prix",
            "RoundNumber": 2,
            "R": pd.Timestamp("2099-12-31"),
        },
    ])


def test_ingest_season_skips_future_events(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"datasets": []}),
        encoding="utf-8",
    )

    monkeypatch.setattr(ingestion, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(
        ingestion,
        "PROCESSED_DATA_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        ingestion.fastf1,
        "get_event_schedule",
        lambda *args, **kwargs: fake_schedule(),
    )

    monkeypatch.setattr(
        ingestion,
        "load_manifest",
        lambda: json.loads(manifest_path.read_text(encoding="utf-8")),
    )

    attempted = []

    def fake_ingest(**kwargs):
        attempted.append(kwargs)
        entry = {
            "dataset_id": kwargs["dataset_id"],
            "filename": f'{kwargs["dataset_id"]}.csv',
            "season": kwargs["year"],
            "grand_prix": str(kwargs["grand_prix"]),
            "session_type": kwargs["session_type"],
            "data_type": "lap_times",
            "source": "FastF1",
            "status": "imported",
        }
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["datasets"].append(entry)
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        return {
            "dataset": entry,
            "rows_imported": 10,
            "csv_path": str(tmp_path / entry["filename"]),
        }

    monkeypatch.setattr(ingestion, "ingest_f1_session", fake_ingest)

    result = ingestion.ingest_season(2021)

    assert len(attempted) == 1
    assert attempted[0]["year"] == 2021
    assert result["summary"]["imported"] == 1
    assert result["summary"]["skipped"] == 1
    assert result["summary"]["failed"] == 0

    saved_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(saved_manifest["datasets"]) == 1


def test_ingest_season_rejects_invalid_year():
    with pytest.raises(ValueError):
        ingestion.ingest_season(1800)


def test_ingest_season_rejects_invalid_session():
    with pytest.raises(ValueError):
        ingestion.ingest_season(2021, session_type="INVALID")


def test_ingest_season_skips_registered_dataset(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    dataset_id = "2021_australian_grand_prix_r"

    existing_csv = tmp_path / f"{dataset_id}.csv"
    existing_csv.write_text("placeholder", encoding="utf-8")

    import json

    manifest = {
        "datasets": [
            {
                "dataset_id": dataset_id,
                "filename": existing_csv.name,
            }
        ]
    }
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.setattr(ingestion, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(ingestion, "PROCESSED_DATA_DIR", tmp_path)
    monkeypatch.setattr(
        ingestion,
        "load_manifest",
        lambda: json.loads(manifest_path.read_text(encoding="utf-8")),
    )
    monkeypatch.setattr(
        ingestion.fastf1,
        "get_event_schedule",
        lambda *args, **kwargs: fake_schedule().iloc[[0]],
    )

    def unexpected_download(**kwargs):
        pytest.fail("An existing dataset should not be downloaded again.")

    monkeypatch.setattr(ingestion, "ingest_f1_session", unexpected_download)

    result = ingestion.ingest_season(2021)

    assert result["summary"]["imported"] == 0
    assert result["summary"]["skipped"] == 1
    assert result["summary"]["failed"] == 0


def test_ingest_season_continues_after_failed_event(tmp_path, monkeypatch):
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        '{"datasets": []}',
        encoding="utf-8",
    )

    monkeypatch.setattr(ingestion, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(ingestion, "PROCESSED_DATA_DIR", tmp_path)
    monkeypatch.setattr(
        ingestion,
        "load_manifest",
        lambda: json.loads(manifest_path.read_text(encoding="utf-8")),
    )

    schedule = fake_schedule().iloc[[0]].copy()
    second_event = schedule.iloc[0].copy()
    second_event["EventName"] = "Second Grand Prix"
    second_event["RoundNumber"] = 2
    second_event["R"] = pd.Timestamp("2021-04-01")

    schedule = pd.concat(
        [schedule, pd.DataFrame([second_event])],
        ignore_index=True,
    )

    monkeypatch.setattr(
        ingestion.fastf1,
        "get_event_schedule",
        lambda *args, **kwargs: schedule,
    )

    attempted = []

    def fake_ingest(**kwargs):
        attempted.append(kwargs["grand_prix"])

        if len(attempted) == 1:
            raise RuntimeError("Simulated download failure")

        return {
            "dataset": {"dataset_id": kwargs["dataset_id"]},
            "rows_imported": 10,
            "csv_path": str(tmp_path / f'{kwargs["dataset_id"]}.csv'),
        }

    monkeypatch.setattr(ingestion, "ingest_f1_session", fake_ingest)

    result = ingestion.ingest_season(2021)

    assert len(attempted) == 2
    assert result["summary"]["failed"] == 1
    assert result["summary"]["imported"] == 1
