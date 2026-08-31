# LMS Data Analysis

Reusable Python analysis layer for the LMS review-data project.

## Project structure

```text
LMS-Data-Analysis/
├── app/
├── src/
│   ├── data/
│   ├── analysis/
│   ├── models/
│   └── utils/
├── data/
├── tests/
├── notebooks/
├── requirements.txt
├── README.md
└── .gitignore
```

The committed dataset is retained in `data/lms_reviews_segmented.csv` as the current analysis snapshot. The source reviews in that file remain unchanged.

## Reusable analysis

The `src` package separates:

- data loading and cleaning
- review ingestion
- sentiment scoring
- pain-point tagging
- user segmentation
- aggregate metrics
- end-to-end analysis orchestration

The notebook under `notebooks/` is a reference workflow that imports these modules. It is not the application runtime entry point.

## Local setup

```bash
python -m venv .venv

# Windows
.venv\\Scripts\\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Run the tests with:

```bash
pytest
```

Run the reference workflow from the repository root with Jupyter:

```bash
jupyter notebook notebooks/LMS_reviews_analysis.ipynb
```

## Current analytical behavior

Sentiment uses TextBlob with positive scores above `0.1`, negative scores below `-0.1`, and neutral values in between. Pain points use the existing six keyword categories. User segmentation preserves the original rating and pain-point thresholds from the exploratory notebook.

The `churned` segment is an analytical heuristic based on review signals; it is not observed customer churn.

## Scope

This change establishes the reusable analysis foundation for the deployable dashboard described in Issue #1. The Streamlit application is intentionally left for Phase 2.
