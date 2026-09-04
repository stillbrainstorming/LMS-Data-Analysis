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
from src.analysis.config import AnalysisConfig, DEFAULT_CONFIG
from src.analysis.pain_points import add_pain_points
from src.analysis.sentiment import add_sentiment
from src.data.reviews import load_reviews
from src.data.schema import validate_derived_schema
from src.models.segmentation import add_user_segments


def run_analysis(path: str | Path, config: AnalysisConfig = DEFAULT_CONFIG) -> dict[str, object]:
    reviews_df = load_reviews(path)
    analyzed = analyze_dataframe(reviews_df, config=config)
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


def analyze_dataframe(df: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    analyzed = add_sentiment(df, config=config)
    analyzed = add_pain_points(analyzed)
    analyzed = add_user_segments(analyzed, config=config)
    validate_derived_schema(analyzed)
    return analyzed
