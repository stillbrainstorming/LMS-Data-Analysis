from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd

METADATA_FILENAME = "data/dataset_metadata.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_metadata(
    df: pd.DataFrame,
    *,
    app_id: str,
    lang: str,
    country: str,
    requested_count: int,
    snapshot_path: str,
    retrieved_at: datetime | None = None,
) -> dict[str, object]:
    dates = pd.to_datetime(df["at"], errors="coerce").dropna()
    retrieval_time = retrieved_at or utc_now()
    return {
        "schema_version": 1,
        "source": "Google Play via google-play-scraper",
        "app_id": app_id,
        "language": lang,
        "country": country,
        "requested_review_count": requested_count,
        "retrieved_at_utc": retrieval_time.isoformat(),
        "review_count": int(len(df)),
        "coverage_start": dates.min().isoformat() if not dates.empty else None,
        "coverage_end": dates.max().isoformat() if not dates.empty else None,
        "snapshot_path": snapshot_path,
    }


def write_metadata(metadata: dict[str, object], path: str | Path = METADATA_FILENAME) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    temporary.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)


def load_metadata(path: str | Path = METADATA_FILENAME) -> dict[str, object] | None:
    source = Path(path)
    if not source.exists() or source.stat().st_size == 0:
        return None
    try:
        return json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
