# LMS Data Analysis

Reusable Python analysis layer and Streamlit product analytics application for LMS review data.

## Project structure

```text
LMS-Data-Analysis/
├── app/
├── src/
│   ├── data/
│   │   ├── schema.py
│   │   └── reviews.py
│   ├── analysis/
│   │   ├── config.py
│   │   ├── sentiment.py
│   │   └── pain_points.py
│   ├── models/
│   └── utils/
├── data/
├── tests/
├── notebooks/
├── requirements.txt
├── requirements-dev.txt
├── .python-version
├── README.md
└── .gitignore
```

The committed dataset is retained in `data/lms_reviews_segmented.csv` as the current analysis snapshot. The source reviews in that file remain unchanged.

## Supported environment

The supported runtime is **Python 3.11.x**. The repository pins this major/minor version in `.python-version` so local development and deployment can use the same interpreter family.

`requirements.txt` contains runtime dependencies required by the Streamlit application. `requirements-dev.txt` extends the runtime environment with pytest and Jupyter for testing and the reference notebook. Keeping these dependencies separate avoids requiring notebook tooling in production.

## Application

The Streamlit application is `app/main.py`. It loads the committed snapshot, applies the reusable analytical pipeline, and provides dashboard filters plus the review explorer. It does not execute the notebook or require notebook state at startup.

### Local setup

From a fresh clone:

```bash
python --version
python -m venv .venv
```

Activate the environment:

```bash
# Windows PowerShell
.venv\\Scripts\\Activate.ps1

# Windows Command Prompt
.venv\\Scripts\\activate.bat

# macOS/Linux
source .venv/bin/activate
```

Install runtime dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start the production application locally:

```bash
streamlit run app/main.py
```

For development and notebook work, install the extended dependency set instead:

```bash
python -m pip install -r requirements-dev.txt
```

Run the deterministic test suite:

```bash
pytest
```

Run the reference workflow with Jupyter when needed:

```bash
jupyter notebook notebooks/LMS_reviews_analysis.ipynb
```

The notebook is a reference workflow only; it is not part of the production startup path.

### Reproducibility and deployment

A clean runtime environment requires only Python 3.11.x and `requirements.txt`. The application starts from `app/main.py`, reads the committed dataset from `data/`, and imports the reusable `src` package directly. No Colab-specific package installation, notebook execution, or notebook state is required.

For deployment, use the same Python 3.11.x runtime and install `requirements.txt`. Deployment remains manual and no GitHub Actions workflow is required.

### Performance and reliability

The dashboard uses Streamlit data caching for the analyzed dataset and reusable chart transformations. The dataset cache includes the source file modification timestamp, so a refreshed CSV invalidates the cached analysis automatically while unchanged data is reused across reruns.

Review exploration is bounded to a fixed page size rather than rendering the full filtered dataset. Filtering and pain-point tag generation are cached, and pagination resets safely when a filter reduces the available page count. Empty result sets return an informational state before downstream rendering.

Dataset loading and analysis are wrapped in a user-facing error boundary with a spinner during the potentially expensive first computation. Missing optional source fields remain covered by the Phase 6 schema normalization contract, and the application does not scrape live data during page loads.

## Data contract

`src/data/schema.py` is the single source of truth for the review data contract.

### Source fields

Stable source columns are:

- `reviewId` — required stable review identifier
- `userName` — optional source field
- `content` — required review text
- `score` — required 1–5 rating
- `thumbsUpCount` — optional helpful-vote count
- `at` — required review timestamp
- `appVersion` — optional app version

### Derived fields

The analytical pipeline adds `review_length`, `sentiment_score`, `sentiment_label`, the six pain-point flags, `user_segment`, and `is_complaint`. Source and derived columns are kept separate so downstream consumers have an explicit contract.

Optional source fields are normalized to safe defaults. Unrecoverable records (missing identifier/text/timestamp, invalid rating, or equivalent corrupt required values) are excluded rather than crashing the application. Duplicate `reviewId` values are resolved deterministically by retaining the latest timestamp, with stable identifier ordering applied afterward.

The resulting dataset remains CSV-based for the first deployable version; no database is required until scale or product requirements justify one.

## Reusable analysis

The `src` package separates:

- data loading and cleaning
- source schema normalization
- sentiment scoring
- pain-point tagging
- user segmentation
- aggregate metrics
- end-to-end analysis orchestration
- explicit analytical configuration

Analytical transformations are deterministic: the same normalized input and configuration produce the same derived output. The pipeline validates the derived schema after transformation so presentation code receives a predictable contract.

## Analytical methodology

### Sentiment

Sentiment uses TextBlob polarity. The default labels are:

- positive: score `> 0.1`
- neutral: score from `-0.1` through `0.1`
- negative: score `< -0.1`

These thresholds are configurable in the application. TextBlob is not a Hindi/Hinglish-aware model and can misclassify mixed-language text, emojis, sarcasm, short reviews, and product-specific language. Sentiment is therefore an inferred analytical field, not ground truth.

### Pain points

Pain points are inferred through case-insensitive keyword matching for six categories: delivery, cancellation, refund, customer support, pricing, and food quality. A matched keyword is a signal, not proof that an underlying business issue occurred.

### User segmentation

The default heuristic preserves the exploratory analysis rules:

- `churned`: 1-star review with at least 2 matched pain points
- `at_risk`: rating ≤ 3 with at least 1 matched pain point
- `satisfied`: rating ≥ 4
- `passive`: remaining reviews

These rules are configurable in the application. **Churned is not verified customer churn**; it is a heuristic segment derived from review signals.

### Dataset freshness

The application reports dataset row count, review coverage period, latest source review timestamp, and the UTC timestamp at which dashboard analysis was generated. Refreshing data is a separate ingestion concern and is not triggered by page loads.

## Scope

The application is a production-oriented Streamlit dashboard backed by the committed curated CSV snapshot. Dataset refresh is a controlled separate workflow, while the normal application path remains deterministic and does not scrape live Google Play data.

Deployment automation is intentionally excluded; no GitHub Actions workflow is required for this project.
