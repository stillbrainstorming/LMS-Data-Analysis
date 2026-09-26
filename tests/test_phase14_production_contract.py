import pandas as pd
import pytest

from app.review_explorer import clear_review_explorer_state
from scripts import preflight
from src.data.ingestion import validate_fetched_reviews
from src.data.manifest import build_metadata


def test_refresh_metadata_marks_success() -> None:
    frame = pd.DataFrame(
        {
            "reviewId": ["1"],
            "content": ["good"],
            "score": [5],
            "at": ["2026-09-01T10:00:00Z"],
        }
    )
    metadata = build_metadata(
        frame,
        app_id="com.application.zomato",
        lang="en",
        country="in",
        requested_count=1,
        snapshot_path="data/snapshots/reviews_20260901T100000Z.csv",
    )
    assert metadata["status"] == "success"


def test_ingestion_accepts_missing_optional_source_columns() -> None:
    frame = pd.DataFrame(
        {
            "reviewId": ["1"],
            "content": ["good"],
            "score": [5],
            "at": ["2026-09-01T10:00:00Z"],
        }
    )
    validate_fetched_reviews(frame)


def test_reset_clears_review_explorer_state() -> None:
    state = {
        "explorer_search": "refund",
        "explorer_ratings": [1],
        "explorer_sentiments": ["negative"],
        "explorer_segments": ["churned"],
        "explorer_pain_points": ["refund"],
        "explorer_dates": ("2026-09-01", "2026-09-02"),
        "explorer_sort": "Lowest rating",
        "explorer_page": 4,
        "explorer_selected_review": "row",
    }
    clear_review_explorer_state(state)
    assert state == {}


def test_preflight_scans_all_production_python_modules(tmp_path, monkeypatch) -> None:
    (tmp_path / "app").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "notebooks").mkdir()
    (tmp_path / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "src" / "module.py").write_text("x = 2\n", encoding="utf-8")
    (tmp_path / "notebooks" / "reference.py").write_text("def broken(:\n", encoding="utf-8")
    monkeypatch.setattr(preflight, "ROOT", tmp_path)
    preflight.check_production_source_syntax()

    (tmp_path / "src" / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    with pytest.raises(preflight.PreflightError, match="src/broken.py"):
        preflight.check_production_source_syntax()
