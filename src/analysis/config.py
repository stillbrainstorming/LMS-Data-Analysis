from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisConfig:
    """Explicit, documented defaults for the analytical heuristics."""

    positive_sentiment_threshold: float = 0.1
    negative_sentiment_threshold: float = -0.1
    churn_rating: int = 1
    churn_min_pain_points: int = 2
    at_risk_max_rating: int = 3
    at_risk_min_pain_points: int = 1
    satisfied_min_rating: int = 4


DEFAULT_CONFIG = AnalysisConfig()
