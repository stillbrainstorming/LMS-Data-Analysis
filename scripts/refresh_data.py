import argparse
import json

from src.data.ingestion import (
    DEFAULT_APP_ID,
    DEFAULT_COUNT,
    DEFAULT_COUNTRY,
    DEFAULT_LANG,
    refresh_dataset,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh the LMS review dataset from Google Play")
    parser.add_argument("--app-id", default=DEFAULT_APP_ID)
    parser.add_argument("--lang", default=DEFAULT_LANG)
    parser.add_argument("--country", default=DEFAULT_COUNTRY)
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    args = parser.parse_args()

    metadata = refresh_dataset(
        app_id=args.app_id,
        lang=args.lang,
        country=args.country,
        count=args.count,
    )
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
