import pandas as pd

from src.analysis.pain_points import pain_point_columns


def summary_metrics(df: pd.DataFrame) -> dict[str, float | int]:
    return {
        "review_count": int(len(df)),
        "average_rating": float(df["score"].mean()),
    }


def rating_distribution(df: pd.DataFrame) -> pd.Series:
    return df["score"].value_counts().sort_index()


def sentiment_distribution(df: pd.DataFrame) -> pd.Series:
    return df["sentiment_label"].value_counts().sort_index()


def segment_distribution(df: pd.DataFrame) -> pd.Series:
    return df["user_segment"].value_counts().sort_index()


def pain_point_counts(df: pd.DataFrame) -> pd.Series:
    return df[pain_point_columns()].sum().sort_values(ascending=False)


def pain_points_by_rating(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("score")[pain_point_columns()].sum()


def sentiment_vs_rating(df: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(df["sentiment_label"], df["score"])


def pain_point_cooccurrence(df: pd.DataFrame) -> pd.DataFrame:
    points = pain_point_columns()
    matrix = pd.DataFrame(index=points, columns=points, dtype=float)
    for left in points:
        for right in points:
            matrix.loc[left, right] = ((df[left] == 1) & (df[right] == 1)).sum()
    return matrix


def one_star_pain_share(df: pd.DataFrame) -> pd.Series:
    points = pain_point_columns()
    total = df[points].sum()
    one_star = df.loc[df["score"] == 1, points].sum()
    return (one_star / total.replace(0, pd.NA) * 100).fillna(0)
