from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews

from src.data.reviews import clean_reviews


def fetch_reviews(
    app_id: str = "com.application.zomato",
    lang: str = "en",
    country: str = "in",
    count: int = 2000,
    sort: Sort = Sort.NEWEST,
) -> pd.DataFrame:
    result, _ = reviews(app_id, lang=lang, country=country, sort=sort, count=count)
    return clean_reviews(pd.DataFrame(result))


def save_reviews(df: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
