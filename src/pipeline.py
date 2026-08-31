from pathlib import Path

import pandas as pd

from src.analysis.aggregates import (
    one_star_pain_share,
    pain_point_cooccurrence,
    pain_point_counts,
    pain_points_by_rating,
    rating_distribution,
    segment_distribution,
    sentiment_distribution,
    sentiment_vs_rating,
    summary_metrics,
)
from src.analysis.pain_points import add_pain_points
from src.analysis.sentiment import add_sentiment
from src.data.reviews import load_reviews
from src.models.segmentation import add_user_segments


def run_analysis(path: str | Path) -> dict[str, object]:
    reviews_df = load_reviews(path)
    analyzed = add_sentiment(reviews_df)
    analyzed = add_pain_points(analyzed)
    analyzed = add_user_segments(analyzed)
    return {
        "data": analyzed,
        "summary": summary_metrics(analyzed),
        "rating_distribution": rating_distribution(analyzed),
        "sentiment_distribution": sentiment_distribution(analyzed),
        "segment_distribution": segment_distribution(analyzed),
        "pain_point_counts": pain_point_counts(analyzed),
        "pain_points_by_rating": pain_points_by_rating(analyzed),
        "sentiment_vs_rating": sentiment_vs_rating(analyzed),
        "pain_point_cooccurrence": pain_point_cooccurrence(analyzed),
        "one_star_pain_share": one_star_pain_share(analyzed),
    }


def analyze_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    analyzed = add_sentiment(df)
    analyzed = add_pain_points(analyzed)
    return add_user_segments(analyzed)
