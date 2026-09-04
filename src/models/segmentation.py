import pandas as pd

from src.analysis.config import AnalysisConfig, DEFAULT_CONFIG
from src.analysis.pain_points import pain_point_columns


def classify_user(row: pd.Series, pain_points: list[str] | None = None, config: AnalysisConfig = DEFAULT_CONFIG) -> str:
    columns = pain_points or pain_point_columns()
    pain_count = row[columns].sum()
    if row["score"] == config.churn_rating and pain_count >= config.churn_min_pain_points:
        return "churned"
    if row["score"] <= config.at_risk_max_rating and pain_count >= config.at_risk_min_pain_points:
        return "at_risk"
    if row["score"] >= config.satisfied_min_rating:
        return "satisfied"
    return "passive"


def add_user_segments(df: pd.DataFrame, config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    frame = df.copy()
    points = pain_point_columns()
    frame["user_segment"] = frame.apply(classify_user, axis=1, pain_points=points, config=config)
    frame["is_complaint"] = (
        (frame["score"] == config.churn_rating) & (frame[points].sum(axis=1) > 0)
    ).astype(int)
    return frame
