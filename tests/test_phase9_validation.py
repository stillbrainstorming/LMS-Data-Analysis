import pandas as pd
import pytest

from src.analysis.aggregates import (
    pain_point_cooccurrence,
    pain_point_counts,
    pain_points_by_rating,
    rating_distribution,
    sentiment_distribution,
    sentiment_vs_rating,
    summary_metrics,
)
from src.analysis.config import AnalysisConfig, DEFAULT_CONFIG
from src.analysis.pain_points import add_pain_points
from src.analysis.sentiment import label_sentiment
from src.data.ingestion import validate_fetched_reviews
from src.data.schema import DERIVED_COLUMNS, normalize_source_reviews, validate_derived_schema
from src.pipeline import analyze_dataframe


def raw_reviews() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewId": "r1",
                "userName": "A",
                "content": "Great delivery and excellent service",
                "score": 5,
                "thumbsUpCount": 2,
                "at": "2026-01-02T10:00:00Z",
                "appVersion": "1.0",
            },
            {
                "reviewId": "r2",
                "userName": "B",
                "content": "Cold food, refund needed, expensive",
                "score": 1,
                "thumbsUpCount": 0,
                "at": "2026-01-03T10:00:00Z",
                "appVersion": "1.0",
            },
            {
                "reviewId": "r3",
                "userName": "C",
                "content": "Support did not help with cancellation",
                "score": 3,
                "thumbsUpCount": 1,
                "at": "2026-01-04T10:00:00Z",
                "appVersion": "1.0",
            },
        ]
    )


def analyzed_reviews() -> pd.DataFrame:
    return analyze_dataframe(normalize_source_reviews(raw_reviews()))


def test_normalization_rejects_malformed_required_records_and_deduplicates() -> None:
    frame = pd.concat(
        [
            raw_reviews(),
            pd.DataFrame(
                [
                    {
                        "reviewId": "r1",
                        "userName": "A2",
                        "content": "Updated review",
                        "score": 4,
                        "thumbsUpCount": 3,
                        "at": "2026-01-05T10:00:00Z",
                        "appVersion": "1.1",
                    },
                    {
                        "reviewId": "",
                        "content": "invalid id",
                        "score": 5,
                        "at": "2026-01-06T10:00:00Z",
                    },
                    {
                        "reviewId": "bad-score",
                        "content": "invalid score",
                        "score": 8,
                        "at": "2026-01-06T10:00:00Z",
                    },
                ]
            ),
        ],
        ignore_index=True,
    )

    normalized = normalize_source_reviews(frame)

    assert normalized["reviewId"].tolist() == ["r1", "r2", "r3"]
    assert normalized.loc[normalized["reviewId"] == "r1", "content"].item() == "Updated review"
    assert normalized["score"].between(1, 5).all()
    assert normalized["at"].notna().all()


def test_normalization_requires_source_columns() -> None:
    with pytest.raises(ValueError, match="Missing required source columns"):
        normalize_source_reviews(pd.DataFrame({"reviewId": ["r1"]}))


def test_sentiment_threshold_boundaries_and_custom_config() -> None:
    assert label_sentiment(0.1) == "neutral"
    assert label_sentiment(-0.1) == "neutral"
    assert label_sentiment(0.1001) == "positive"
    assert label_sentiment(-0.1001) == "negative"

    config = AnalysisConfig(positive_sentiment_threshold=0.2, negative_sentiment_threshold=-0.2)
    assert label_sentiment(0.15, config) == "neutral"
    assert label_sentiment(-0.25, config) == "negative"


def test_pain_point_tagging_is_case_insensitive_and_handles_missing_text() -> None:
    frame = pd.DataFrame({"content": ["REFUND please", None, "Great quality"]})
    tagged = add_pain_points(frame)

    assert tagged.loc[0, "refund"] == 1
    assert tagged.loc[1, "refund"] == 0
    assert tagged.loc[2, "food_quality"] == 1


def test_pipeline_produces_complete_derived_schema() -> None:
    analyzed = analyzed_reviews()
    validate_derived_schema(analyzed)
    assert all(column in analyzed.columns for column in DERIVED_COLUMNS)
    assert set(analyzed["user_segment"]) == {"satisfied", "churned", "at_risk"}
    assert analyzed.loc[analyzed["score"] == 1, "is_complaint"].item() == 1


def test_aggregate_metrics_are_deterministic() -> None:
    analyzed = analyzed_reviews()
    summary = summary_metrics(analyzed)

    assert summary["review_count"] == 3
    assert summary["average_rating"] == pytest.approx(3.0)
    assert rating_distribution(analyzed).to_dict() == {1: 1, 3: 1, 5: 1}
    assert sentiment_distribution(analyzed).sum() == 3
    assert sentiment_vs_rating(analyzed).to_numpy().sum() == 3
    assert pain_point_counts(analyzed).loc["delivery"] == 1
    assert pain_points_by_rating(analyzed).loc[1, "refund"] == 1
    assert pain_point_cooccurrence(analyzed).loc["refund", "refund"] == 1
    assert pain_point_cooccurrence(analyzed).loc["refund", "food_quality"] == 1


def test_derived_schema_rejects_missing_columns() -> None:
    with pytest.raises(ValueError, match="Missing derived columns"):
        validate_derived_schema(pd.DataFrame())


def test_ingestion_validation_rejects_empty_and_invalid_source_data() -> None:
    with pytest.raises(ValueError, match="no reviews"):
        validate_fetched_reviews(pd.DataFrame(columns=raw_reviews().columns))

    invalid = raw_reviews().copy()
    invalid.loc[0, "score"] = 0
    with pytest.raises(ValueError, match="invalid scores"):
        validate_fetched_reviews(invalid)

    invalid_timestamp = raw_reviews().copy()
    invalid_timestamp.loc[0, "at"] = "not-a-date"
    with pytest.raises(ValueError, match="invalid timestamps"):
        validate_fetched_reviews(invalid_timestamp)


def test_ingestion_validation_rejects_missing_required_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        validate_fetched_reviews(pd.DataFrame({"reviewId": ["r1"]}))


def test_ingestion_validation_does_not_require_live_scraping() -> None:
    validate_fetched_reviews(raw_reviews())
