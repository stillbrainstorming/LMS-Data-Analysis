from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

RAW_COLUMNS = (
    "reviewId",
    "userName",
    "content",
    "score",
    "thumbsUpCount",
    "at",
    "appVersion",
)

REQUIRED_SOURCE_COLUMNS = ("reviewId", "content", "score", "at")
OPTIONAL_SOURCE_DEFAULTS = {
    "userName": "",
    "thumbsUpCount": 0,
    "appVersion": "",
}
DERIVED_COLUMNS = (
    "review_length",
    "sentiment_score",
    "sentiment_label",
    "delivery",
    "cancellation",
    "refund",
    "customer_support",
    "pricing",
    "food_quality",
    "user_segment",
    "is_complaint",
)

@dataclass(frozen=True)
class ReviewSchema:
    raw_columns: tuple[str, ...] = RAW_COLUMNS
    required_source_columns: tuple[str, ...] = REQUIRED_SOURCE_COLUMNS
    derived_columns: tuple[str, ...] = DERIVED_COLUMNS

SCHEMA = ReviewSchema()


def normalize_source_reviews(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    missing = [column for column in REQUIRED_SOURCE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required source columns: {', '.join(missing)}")

    for column, default in OPTIONAL_SOURCE_DEFAULTS.items():
        if column not in frame.columns:
            frame[column] = default

    frame = frame[list(RAW_COLUMNS)].copy()
    frame["reviewId"] = frame["reviewId"].astype("string").str.strip()
    frame["content"] = frame["content"].astype("string")
    frame["score"] = pd.to_numeric(frame["score"], errors="coerce")
    frame["thumbsUpCount"] = pd.to_numeric(frame["thumbsUpCount"], errors="coerce").fillna(0)
    frame["at"] = pd.to_datetime(frame["at"], errors="coerce")
    frame["userName"] = frame["userName"].fillna("").astype("string")
    frame["appVersion"] = frame["appVersion"].fillna("").astype("string")

    valid = (
        frame["reviewId"].notna()
        & frame["reviewId"].ne("")
        & frame["content"].notna()
        & frame["content"].str.strip().ne("")
        & frame["score"].between(1, 5)
        & frame["at"].notna()
    )
    frame = frame.loc[valid].copy()
    frame["score"] = frame["score"].astype("int64")
    frame["thumbsUpCount"] = frame["thumbsUpCount"].clip(lower=0).astype("int64")
    frame = frame.sort_values(["reviewId", "at"], kind="stable").drop_duplicates("reviewId", keep="last")
    return frame.sort_values("reviewId", kind="stable").reset_index(drop=True)


def validate_derived_schema(df: pd.DataFrame) -> None:
    missing = [column for column in DERIVED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing derived columns: {', '.join(missing)}")
