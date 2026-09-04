import pandas as pd

from src.analysis.config import AnalysisConfig, DEFAULT_CONFIG
from src.analysis.sentiment import label_sentiment
from src.models.segmentation import classify_user


def test_default_sentiment_thresholds_are_preserved():
    assert DEFAULT_CONFIG.positive_sentiment_threshold == 0.1
    assert DEFAULT_CONFIG.negative_sentiment_threshold == -0.1
    assert label_sentiment(0.11) == "positive"
    assert label_sentiment(-0.11) == "negative"
    assert label_sentiment(0.1) == "neutral"


def test_sentiment_thresholds_are_configurable():
    config = AnalysisConfig(positive_sentiment_threshold=0.3, negative_sentiment_threshold=-0.3)
    assert label_sentiment(0.2, config) == "neutral"
    assert label_sentiment(-0.2, config) == "neutral"
    assert label_sentiment(0.31, config) == "positive"


def test_default_churn_rule_is_preserved():
    row = pd.Series({"score": 1, "delivery": 1, "cancellation": 1, "refund": 0, "customer_support": 0, "pricing": 0, "food_quality": 0})
    assert classify_user(row) == "churned"


def test_segmentation_rules_are_configurable():
    row = pd.Series({"score": 2, "delivery": 1, "cancellation": 0, "refund": 0, "customer_support": 0, "pricing": 0, "food_quality": 0})
    config = AnalysisConfig(at_risk_max_rating=2, at_risk_min_pain_points=1)
    assert classify_user(row, config=config) == "at_risk"
