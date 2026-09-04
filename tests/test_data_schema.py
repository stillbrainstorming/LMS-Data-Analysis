import pandas as pd

from src.data.schema import (
    DERIVED_COLUMNS,
    RAW_COLUMNS,
    REQUIRED_SOURCE_COLUMNS,
    normalize_source_reviews,
    validate_derived_schema,
)


def fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "reviewId": ["b", "a", "a", "bad", ""],
            "content": ["good", "latest", "older", "broken", "missing id"],
            "score": [5, 4, 3, "not-a-score", 5],
            "at": ["2026-01-02", "2026-01-03", "2026-01-02", "invalid", "2026-01-04"],
        }
    )


def test_schema_separates_raw_and_derived_columns():
    assert "content" in RAW_COLUMNS
    assert "sentiment_label" in DERIVED_COLUMNS
    assert not set(RAW_COLUMNS) & set(DERIVED_COLUMNS)
    assert set(REQUIRED_SOURCE_COLUMNS).issubset(RAW_COLUMNS)


def test_missing_optional_columns_are_normalized():
    result = normalize_source_reviews(fixture())
    assert result["userName"].tolist() == ["", "", ""]
    assert result["appVersion"].tolist() == ["", "", ""]
    assert result["thumbsUpCount"].tolist() == [0, 0, 0]


def test_invalid_records_are_removed_and_duplicates_are_deterministic():
    result = normalize_source_reviews(fixture())
    assert result["reviewId"].tolist() == ["a", "b"]
    assert result.loc[result["reviewId"] == "a", "content"].item() == "latest"
    assert result["score"].tolist() == [4, 5]


def test_derived_schema_validation_rejects_incomplete_analysis():
    with pd.option_context("mode.copy_on_write", True):
        incomplete = pd.DataFrame({"reviewId": ["a"]})
    try:
        validate_derived_schema(incomplete)
    except ValueError as exc:
        assert "sentiment_score" in str(exc)
    else:
        raise AssertionError("Expected incomplete derived schema to fail validation")
