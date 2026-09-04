from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from google_play_scraper import Sort, reviews

from src.data.manifest import build_metadata, write_metadata
from src.data.reviews import SOURCE_COLUMNS, clean_reviews
from src.pipeline import analyze_dataframe

DEFAULT_APP_ID = "com.application.zomato"
DEFAULT_LANG = "en"
DEFAULT_COUNTRY = "in"
DEFAULT_COUNT = 2000
DEFAULT_OUTPUT = Path("data/lms_reviews_segmented.csv")
DEFAULT_SNAPSHOT_DIR = Path("data/snapshots")


def validate_fetched_reviews(df: pd.DataFrame) -> None:
    missing = [column for column in SOURCE_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Fetched data is missing required columns: {', '.join(missing)}")
    if df.empty:
        raise ValueError("The ingestion source returned no reviews")
    if not df["reviewId"].astype(str).str.strip().ne("").all():
        raise ValueError("Fetched reviews contain empty review identifiers")
    scores = pd.to_numeric(df["score"], errors="coerce")
    if scores.isna().any() or not scores.between(1, 5).all():
        raise ValueError("Fetched reviews contain invalid scores")
    timestamps = pd.to_datetime(df["at"], errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Fetched reviews contain invalid timestamps")


def fetch_reviews(
    app_id: str = DEFAULT_APP_ID,
    lang: str = DEFAULT_LANG,
    country: str = DEFAULT_COUNTRY,
    count: int = DEFAULT_COUNT,
    sort: Sort = Sort.NEWEST,
) -> pd.DataFrame:
    if not app_id.strip():
        raise ValueError("app_id must not be empty")
    if not lang.strip() or not country.strip():
        raise ValueError("lang and country must not be empty")
    if count < 1:
        raise ValueError("count must be greater than zero")
    result, _ = reviews(app_id, lang=lang, country=country, sort=sort, count=count)
    raw = pd.DataFrame(result)
    validate_fetched_reviews(raw)
    return clean_reviews(raw)


def save_reviews(df: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def snapshot_path(retrieved_at: datetime | None = None, directory: str | Path = DEFAULT_SNAPSHOT_DIR) -> Path:
    timestamp = retrieved_at or datetime.now(timezone.utc)
    return Path(directory) / f"reviews_{timestamp.strftime('%Y%m%dT%H%M%SZ')}.csv"


def refresh_dataset(
    *,
    app_id: str = DEFAULT_APP_ID,
    lang: str = DEFAULT_LANG,
    country: str = DEFAULT_COUNTRY,
    count: int = DEFAULT_COUNT,
    output_path: str | Path = DEFAULT_OUTPUT,
    snapshot_dir: str | Path = DEFAULT_SNAPSHOT_DIR,
) -> dict[str, object]:
    retrieved_at = datetime.now(timezone.utc)
    refreshed = fetch_reviews(app_id=app_id, lang=lang, country=country, count=count)
    analyzed = analyze_dataframe(refreshed)
    analyzed_path = Path(output_path)
    temporary = analyzed_path.with_suffix(analyzed_path.suffix + ".tmp")
    snapshot = snapshot_path(retrieved_at, snapshot_dir)
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    save_reviews(analyzed, snapshot)
    save_reviews(analyzed, temporary)
    temporary.replace(analyzed_path)
    metadata = build_metadata(
        analyzed,
        app_id=app_id,
        lang=lang,
        country=country,
        requested_count=count,
        snapshot_path=str(snapshot),
        retrieved_at=retrieved_at,
    )
    write_metadata(metadata)
    return metadata
