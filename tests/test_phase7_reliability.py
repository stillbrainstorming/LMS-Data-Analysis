import pandas as pd

from app.review_explorer import add_pain_point_tags, filter_reviews


def fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "reviewId": ["1", "2", "3"],
            "content": ["refund was slow", "great delivery", "support helped"],
            "score": [1, 5, 3],
            "at": pd.to_datetime(["2026-01-03", "2026-01-02", "2026-01-01"]),
            "sentiment_label": ["negative", "positive", "neutral"],
            "user_segment": ["churned", "satisfied", "at_risk"],
            "refund": [1, 0, 0],
            "delivery": [0, 1, 0],
        }
    )


def test_filtering_handles_empty_results_without_error():
    result = filter_reviews(fixture(), "does-not-exist", (), (), (), (), None, None)
    assert result.empty


def test_filtering_ignores_missing_optional_pain_columns():
    result = filter_reviews(fixture(), "", (), (), (), ("cancellation",), None, None)
    assert len(result) == len(fixture())


def test_pain_point_tags_handles_missing_columns():
    result = add_pain_point_tags(fixture().drop(columns=["refund", "delivery"]), ("refund", "delivery"))
    assert result["pain_point_tags"].eq("").all()


def test_filtering_and_pagination_inputs_are_deterministic():
    result = filter_reviews(fixture(), "", (1, 3), (), (), (), None, None)
    assert result["reviewId"].tolist() == ["1", "3"]
