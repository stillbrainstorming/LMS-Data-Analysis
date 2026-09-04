from pathlib import Path

import pandas as pd

from src.data.schema import RAW_COLUMNS, normalize_source_reviews

SOURCE_COLUMNS = list(RAW_COLUMNS)


def clean_reviews(df: pd.DataFrame) -> pd.DataFrame:
    return normalize_source_reviews(df)


def load_reviews(path: str | Path) -> pd.DataFrame:
    return clean_reviews(pd.read_csv(path))
