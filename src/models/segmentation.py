import pandas as pd

from src.analysis.pain_points import pain_point_columns



def classify_user(row: pd.Series, pain_points: list[str] | None = None) -> str:
    columns = pain_points or pain_point_columns()
    pain_count = row[columns].sum()
    if row["score"] == 1 and pain_count >= 2:
        return "churned"
    if row["score"] <= 3 and pain_count >= 1:
        return "at_risk"
    if row["score"] >= 4:
        return "satisfied"
    return "passive"


def add_user_segments(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    points = pain_point_columns()
    frame["user_segment"] = frame.apply(classify_user, axis=1, pain_points=points)
    frame["is_complaint"] = (
        (frame["score"] == 1) & (frame[points].sum(axis=1) > 0)
    ).astype(int)
    return frame
