from datetime import datetime, timezone

import pandas as pd
import pytest

from src.data.ingestion import snapshot_path, validate_fetched_reviews
from src.data.manifest import build_metadata


def valid_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "reviewId": ["1", "2"],
            "userName": ["a", "b"],
            "content": ["great", "late delivery"],
            "score": [5, 1],
            "thumbsUpCount": [2, 0],
            "at": ["2026-09-01 10:00:00", "2026-09-02 11:00:00"],
            "appVersion": ["1", "1"],
        }
    )


def test_validate_fetched_reviews_accepts_expected_source_schema():
    validate_fetched_reviews(valid_frame())


def test_validate_fetched_reviews_rejects_missing_columns():
    frame = valid_frame().drop(columns=["score"])
    with pytest.raises(ValueError, match="missing required columns"):
        validate_fetched_reviews(frame)


def test_validate_fetched_reviews_rejects_invalid_scores():
    frame = valid_frame()
    frame.loc[0, "score"] = 6
    with pytest.raises(ValueError, match="invalid scores"):
        validate_fetched_reviews(frame)


def test_validate_fetched_reviews_rejects_invalid_timestamps():
    frame = valid_frame()
    frame.loc[0, "at"] = "not-a-date"
    with pytest.raises(ValueError, match="invalid timestamps"):
        validate_fetched_reviews(frame)


def test_snapshot_path_is_utc_and_versioned():
    timestamp = datetime(2026, 9, 4, 10, 30, tzinfo=timezone.utc)
    assert snapshot_path(timestamp, "data/snapshots").as_posix() == "data/snapshots/reviews_20260904T103000Z.csv"


def test_metadata_records_retrieval_and_coverage():
    metadata = build_metadata(
        valid_frame(),
        app_id="com.application.zomato",
        lang="en",
        country="in",
        requested_count=2000,
        snapshot_path="data/snapshots/reviews_20260904T103000Z.csv",
        retrieved_at=datetime(2026, 9, 4, 10, 30, tzinfo=timezone.utc),
    )
    assert metadata["review_count"] == 2
    assert metadata["coverage_start"].startswith("2026-09-01")
    assert metadata["coverage_end"].startswith("2026-09-02")
    assert metadata["retrieved_at_utc"].startswith("2026-09-04T10:30:00")
