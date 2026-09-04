# LMS Data Analysis

Reusable Python analysis layer and Streamlit product analytics application for LMS review data.

## Project structure

```text
LMS-Data-Analysis/
├── app/
├── scripts/
│   └── refresh_data.py
├── src/
│   ├── data/
│   │   ├── ingestion.py
│   │   ├── manifest.py
│   │   └── reviews.py
│   ├── analysis/
│   │   ├── config.py
│   │   ├── sentiment.py
│   │   └── pain_points.py
│   ├── models/
│   └── utils/
├── data/
│   ├── lms_reviews_segmented.csv
│   ├── dataset_metadata.json
│   └── snapshots/
├── tests/
├── notebooks/
├── requirements.txt
├── README.md
└── .gitignore
```

The committed dataset in `data/lms_reviews_segmented.csv` is the last known-good application snapshot. Refreshing data is an explicit ingestion operation and never runs during a dashboard page load.

## Application

The Streamlit application is `app/main.py`. It loads the committed snapshot, applies the reusable analytical pipeline, and provides dashboard filters plus the review explorer. Dataset freshness metadata is shown when available.

Run locally:

```bash
streamlit run app/main.py
```

## Data pipeline

The reusable ingestion layer is in `src/data/ingestion.py`. It supports configurable Google Play app identifier, language, country, and review count, validates the fetched source fields, cleans the reviews, runs the analytical transformations, and only then replaces the active dataset.

Use the controlled refresh command from the repository root:

```bash
python scripts/refresh_data.py
```

Optional configuration:

```bash
python scripts/refresh_data.py --app-id com.application.zomato --lang en --country in --count 2000
```

A successful refresh:

1. Fetches reviews from Google Play through `google-play-scraper`.
2. Validates required identifiers, scores, timestamps, and source columns.
3. Cleans and analyzes the complete fetched dataset.
4. Writes a timestamped snapshot under `data/snapshots/`.
5. Atomically replaces `data/lms_reviews_segmented.csv` with the validated analyzed dataset.
6. Records retrieval time, source configuration, row count, and coverage period in `data/dataset_metadata.json`.

If fetching or validation fails before the replacement step, the existing active dataset remains untouched. This gives the deployed application a last-known-good fallback without scraping on user requests.

Snapshots are intentionally created by the refresh workflow rather than committed in advance with fabricated timestamps. The repository therefore remains reproducible while each real refresh produces a dated artifact.

## Reusable analysis

The `src` package separates:

- data loading and cleaning
- review ingestion and validation
- snapshot and freshness metadata
- sentiment scoring
- pain-point tagging
- user segmentation
- aggregate metrics
- end-to-end analysis orchestration
- explicit analytical configuration

The notebook under `notebooks/` is a reference workflow. It is not required to run the application.

## Analytical methodology

### Sentiment

Sentiment uses TextBlob polarity. The default labels are:

- positive: score `> 0.1`
- neutral: score from `-0.1` through `0.1`
- negative: score `< -0.1`

These thresholds are configurable in the application and are preserved as the Phase 1/2 defaults. TextBlob is not a Hindi/Hinglish-aware model and can misclassify mixed-language text, emojis, sarcasm, short reviews, and product-specific language. Sentiment is therefore an inferred analytical field, not ground truth.

### Pain points

Pain points are inferred through case-insensitive keyword matching for six categories: delivery, cancellation, refund, customer support, pricing, and food quality. A matched keyword is a signal, not proof that an underlying business issue occurred.

### User segmentation

The default heuristic preserves the exploratory analysis rules:

- `churned`: 1-star review with at least 2 matched pain points
- `at_risk`: rating ≤ 3 with at least 1 matched pain point
- `satisfied`: rating ≥ 4
- `passive`: remaining reviews

These rules are configurable in the application. **Churned is not verified customer churn**; it is a heuristic segment derived from review signals. The same applies to other derived segment labels.

### Source vs derived data

Source/measured fields include review text, star rating, thumbs-up count, review timestamp, and app version where supplied by the source dataset. Derived fields include sentiment score/label, pain-point flags, user segment, complaint flag, and aggregate metrics/charts.

### Dataset freshness

The application reports the number of rows, review coverage period, latest source review timestamp, and the UTC timestamp at which the dashboard analysis was generated. When a refresh has been run, it also reports the ingestion retrieval timestamp and snapshot path from `data/dataset_metadata.json`.

## Source and redistribution considerations

The ingestion layer uses the third-party `google-play-scraper` library to retrieve public Google Play review data. Availability, response shape, rate limits, regional behavior, and library compatibility may change over time. Before redistributing refreshed datasets, verify the applicable Google Play terms, the library's own project terms, and any restrictions associated with the source data. The application does not scrape Google Play during normal page loads.

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

Run the reference workflow with Jupyter:

```bash
jupyter notebook notebooks/LMS_reviews_analysis.ipynb
```

## Scope

Phase 5 adds a controlled, reusable, validated refresh pipeline with configurable source parameters, dated snapshots, freshness metadata, deterministic analytical regeneration, and last-known-good dataset behavior. Deployment automation is intentionally excluded; no GitHub Actions workflow is required for this project.
