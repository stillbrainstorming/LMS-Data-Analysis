# LMS Data Analysis

Reusable Python analysis layer and Streamlit product analytics application for LMS review data.

## Project structure

```text
LMS-Data-Analysis/
├── app/
├── src/
│   ├── data/
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
├── README.md
└── .gitignore
```

The committed dataset is retained in `data/lms_reviews_segmented.csv` as the current analysis snapshot. The source reviews in that file remain unchanged.

## Application

The Streamlit application is `app/main.py`. It loads the committed snapshot, applies the reusable analytical pipeline, and provides dashboard filters plus the Phase 3 review explorer.

Run locally:

```bash
streamlit run app/main.py
```

## Reusable analysis

The `src` package separates:

- data loading and cleaning
- review ingestion
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

The application reports the number of rows, review coverage period, latest source review timestamp, and the UTC timestamp at which the dashboard analysis was generated. The committed CSV is a snapshot; refreshing it is a separate ingestion concern and is not triggered by page loads.

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

Phase 4 makes analytical assumptions explicit, visible, and configurable while documenting source versus derived fields and dataset freshness. Deployment automation is intentionally excluded; no GitHub Actions workflow is required for this project.
