import re

import pandas as pd

KEYWORDS = {
    "delivery": ["delivery", "deliver", "delevery", "deliverd"],
    "cancellation": ["cancel", "cancelled", "cancellation"],
    "refund": ["refund", "money", "payment", "paid"],
    "customer_support": ["support", "customer care", "helpline", "agent"],
    "pricing": ["charge", "expensive", "price", "fee", "costly"],
    "food_quality": ["cold", "stale", "quality", "taste", "bad food"],
}


def _pattern(words: list[str]) -> str:
    return "|".join(re.escape(word) for word in words)


def add_pain_points(df: pd.DataFrame, text_column: str = "content") -> pd.DataFrame:
    frame = df.copy()
    text = frame[text_column].fillna("").astype(str).str.lower()
    for category, words in KEYWORDS.items():
        frame[category] = text.str.contains(_pattern(words), na=False).astype(int)
    return frame


def pain_point_columns() -> list[str]:
    return list(KEYWORDS)
