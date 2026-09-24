from __future__ import annotations

import json
import py_compile
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "app/main.py",
    "app/review_explorer.py",
    "requirements.txt",
    "data/lms_reviews_segmented.csv",
    "data/dataset_metadata.json",
    "src/data/schema.py",
)
ALLOWED_METADATA_STATUS = {"not_refreshed", "success", "failed"}


class PreflightError(Exception):
    pass


def check_required_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise PreflightError("Missing required files: " + ", ".join(missing))


def check_dependencies() -> None:
    dependency_file = ROOT / "requirements.txt"
    if not dependency_file.read_text(encoding="utf-8").strip():
        raise PreflightError("requirements.txt is empty")


def check_entry_point() -> None:
    entry_point = ROOT / "app" / "main.py"
    try:
        py_compile.compile(str(entry_point), doraise=True)
    except py_compile.PyCompileError as exc:
        raise PreflightError(f"app/main.py failed to compile: {exc.msg}") from exc


def check_dataset() -> None:
    from src.data.schema import normalize_source_reviews, validate_derived_schema

    dataset_path = ROOT / "data" / "lms_reviews_segmented.csv"
    frame = pd.read_csv(dataset_path)
    if frame.empty:
        raise PreflightError("The committed dataset is empty")

    normalized = normalize_source_reviews(frame)
    if normalized.empty:
        raise PreflightError("The dataset contains no valid source reviews")

    validate_derived_schema(frame)


def check_metadata() -> None:
    metadata_path = ROOT / "data" / "dataset_metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PreflightError(f"dataset_metadata.json is invalid: {exc}") from exc

    if metadata.get("schema_version") != 1:
        raise PreflightError("dataset_metadata.json has an unsupported schema_version")

    status = metadata.get("status")
    if status not in ALLOWED_METADATA_STATUS:
        raise PreflightError("dataset_metadata.json has an unsupported status")


def main() -> int:
    checks = (
        ("required files", check_required_files),
        ("runtime dependencies", check_dependencies),
        ("Streamlit entry point", check_entry_point),
        ("dataset contract", check_dataset),
        ("dataset metadata", check_metadata),
    )

    failures = []
    for name, check in checks:
        try:
            check()
            print(f"PASS: {name}")
        except Exception as exc:
            print(f"FAIL: {name}: {exc}")
            failures.append(name)

    if failures:
        print("Preflight failed: " + ", ".join(failures))
        return 1

    print("Preflight passed.")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
