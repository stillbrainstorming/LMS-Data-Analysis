from collections.abc import Iterable

import pandas as pd
from textblob import TextBlob


POSITIVE_THRESHOLD = 0.1
NEGATIVE_THRESHOLD = -0.1


def score_sentiment(text: object) -> float:
    return float(TextBlob(str(text)).sentiment.polarity)


def label_sentiment(score: float) -> str:
    if score > POSITIVE_THRESHOLD:
        return "positive"
    if score < NEGATIVE_THRESHOLD:
        return "negative"
    return "neutral"


def add_sentiment(df: pd.DataFrame, text_column: str = "content") -> pd.DataFrame:
    frame = df.copy()
    scores = frame[text_column].map(score_sentiment)
    frame["sentiment_score"] = scores
    frame["sentiment_label"] = scores.map(label_sentiment)
    return frame


def score_sentiments(texts: Iterable[object]) -> list[float]:
    return [score_sentiment(text) for text in texts]
