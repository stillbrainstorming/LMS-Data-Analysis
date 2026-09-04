from collections.abc import Iterable

import pandas as pd
from textblob import TextBlob

from src.analysis.config import AnalysisConfig, DEFAULT_CONFIG


def score_sentiment(text: object) -> float:
    return float(TextBlob(str(text)).sentiment.polarity)


def label_sentiment(score: float, config: AnalysisConfig = DEFAULT_CONFIG) -> str:
    if score > config.positive_sentiment_threshold:
        return "positive"
    if score < config.negative_sentiment_threshold:
        return "negative"
    return "neutral"


def add_sentiment(df: pd.DataFrame, text_column: str = "content", config: AnalysisConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    frame = df.copy()
    scores = frame[text_column].map(score_sentiment)
    frame["sentiment_score"] = scores
    frame["sentiment_label"] = scores.map(lambda score: label_sentiment(score, config))
    return frame


def score_sentiments(texts: Iterable[object]) -> list[float]:
    return [score_sentiment(text) for text in texts]
