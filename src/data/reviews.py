from pathlib import Path

import pandas as pd

SOURCE_COLUMNS = [
    "reviewId",
    "userName",
    "content",
    "score",
    "thumbsUpCount",
    "at",
    "appVersion",
]


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    missing = [column for column in SOURCE_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    frame = frame[SOURCE_COLUMNS].copy()
    frame["at"] = pd.to_datetime(frame["at"])
    frame = frame.dropna(subset=["content"])
    frame = frame[frame["content"].str.strip() != ""]
    frame["review_length"] = frame["content"].str.split().str.len()
    return frame.reset_index(drop=True)


def load_reviews(path: str | Path) -> pd.DataFrame:
    return clean_reviews(pd.read_csv(path))
