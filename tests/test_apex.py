
import pandas as pd
import pytest

from apex.analytics import compare_driver_pace
from apex.rag import retrieve_context


def test_compare_driver_pace():
    # Small, controlled dataset with known answers
    laps = pd.DataFrame({
        "Driver": ["HAM", "HAM", "VER", "VER"],
        "lap_duration": [90.0, 92.0, 91.0, 93.0],
    })

    result = compare_driver_pace(laps, "HAM", "VER")

    assert result["HAM"]["mean_lap_seconds"] == 91.0
    assert result["VER"]["mean_lap_seconds"] == 92.0
    assert result["mean_gap_seconds"] == -1.0


def test_rag_retrieves_undercut_information():
    documents = retrieve_context(
        "How does an undercut work in Formula 1?",
        k=3,
    )

    assert documents, "RAG should return at least one document"

    combined_text = " ".join(
        doc.page_content.lower() for doc in documents
    )

    assert "undercut" in combined_text or "fresh tyres" in combined_text

def test_compare_driver_pace_rejects_missing_columns():
    laps = pd.DataFrame({
        "Driver": ["HAM", "VER"],
        # Intentionally missing "lap_duration"
    })

    with pytest.raises(ValueError, match="lap_duration"):
        compare_driver_pace(laps, "HAM", "VER")


def test_compare_driver_pace_handles_missing_lap_times():
    laps = pd.DataFrame({
        "Driver": ["HAM", "HAM", "VER", "VER"],
        "lap_duration": [90.0, None, 92.0, 94.0],
    })

    result = compare_driver_pace(laps, "HAM", "VER")

    assert result["HAM"]["mean_lap_seconds"] == 90.0
    assert result["HAM"]["valid_laps"] == 1
    assert result["VER"]["mean_lap_seconds"] == 93.0
    assert result["VER"]["valid_laps"] == 2
    assert result["mean_gap_seconds"] == -3.0
