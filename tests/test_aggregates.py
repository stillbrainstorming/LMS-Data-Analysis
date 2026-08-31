import pandas as pd

from src.analysis.aggregates import (
    pain_point_cooccurrence,
    pain_point_counts,
    pain_points_by_rating,
    rating_distribution,
    segment_distribution,
    sentiment_distribution,
    sentiment_vs_rating,
    summary_metrics,
)
from src.pipeline import analyze_dataframe


def test_aggregate_functions():
    df = analyze_dataframe(
        pd.DataFrame(
            {
                "reviewId": ["1", "2"],
                "userName": ["a", "b"],
                "content": ["great service", "late delivery"],
                "score": [5, 1],
                "thumbsUpCount": [0, 0],
                "at": ["2026-06-26", "2026-06-27"],
                "appVersion": ["1", "1"],
            }
        )
    )
    summary = summary_metrics(df)
    assert summary["review_count"] == 2
    assert summary["average_rating"] == 3.0
    assert rating_distribution(df).to_dict() == {1: 1, 5: 1}
    assert set(sentiment_distribution(df).index) == {"positive", "negative"}
    assert set(segment_distribution(df).index) == {"satisfied", "at_risk"}
    assert pain_point_counts(df)["delivery"] == 1
    assert pain_points_by_rating(df).loc[1, "delivery"] == 1
    assert sentiment_vs_rating(df).loc["positive", 5] == 1
    assert pain_point_cooccurrence(df).loc["delivery", "delivery"] == 1
