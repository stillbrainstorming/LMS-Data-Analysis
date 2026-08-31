import pandas as pd

from src.analysis.pain_points import add_pain_points
from src.analysis.sentiment import add_sentiment
from src.models.segmentation import add_user_segments


def sample_reviews() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "reviewId": ["1", "2", "3", "4"],
            "userName": ["a", "b", "c", "d"],
            "content": [
                "great service",
                "late delivery and no refund",
                "food was cold and support was terrible",
                "average experience",
            ],
            "score": [5, 1, 1, 3],
            "thumbsUpCount": [0, 0, 0, 0],
            "at": [
                "2026-06-26 10:00:00",
                "2026-06-26 11:00:00",
                "2026-06-26 12:00:00",
                "2026-06-26 13:00:00",
            ],
            "appVersion": ["1", "1", "1", "1"],
        }
    )


def test_sentiment_is_added():
    result = add_sentiment(sample_reviews())
    assert "sentiment_score" in result
    assert "sentiment_label" in result
    assert result.loc[0, "sentiment_label"] == "positive"


def test_pain_points_match_expected_keywords():
    result = add_pain_points(sample_reviews())
    assert result.loc[1, "delivery"] == 1
    assert result.loc[1, "refund"] == 1
    assert result.loc[2, "food_quality"] == 1
    assert result.loc[2, "customer_support"] == 1


def test_user_segments_preserve_existing_rules():
    result = add_user_segments(add_pain_points(sample_reviews()))
    assert result.loc[0, "user_segment"] == "satisfied"
    assert result.loc[1, "user_segment"] == "churned"
    assert result.loc[2, "user_segment"] == "churned"
    assert result.loc[3, "user_segment"] == "passive"


def test_complaint_flag_uses_one_star_and_any_pain_point():
    result = add_user_segments(add_pain_points(sample_reviews()))
    assert result.loc[1, "is_complaint"] == 1
    assert result.loc[2, "is_complaint"] == 1
    assert result.loc[3, "is_complaint"] == 0
