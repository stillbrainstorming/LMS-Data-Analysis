from datetime import datetime, timezone
from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.review_explorer import render_review_explorer
from src.analysis.config import AnalysisConfig, DEFAULT_CONFIG
from src.analysis.pain_points import pain_point_columns
from src.data.manifest import load_metadata
from src.data.reviews import load_reviews
from src.pipeline import analyze_dataframe

DATA_PATH = ROOT / "data" / "lms_reviews_segmented.csv"
METADATA_PATH = ROOT / "data" / "dataset_metadata.json"
PAIN_POINTS = pain_point_columns()
SEGMENTS = ["satisfied", "passive", "at_risk", "churned"]
SENTIMENTS = ["positive", "neutral", "negative"]

st.set_page_config(page_title="LMS Review Intelligence", page_icon="📊", layout="wide")
st.markdown("# LMS Review Intelligence")
st.caption("Interactive product analytics for customer reviews")


@st.cache_data(show_spinner=False)
def load_analyzed_data(path: str, modified_time_ns: int, analysis_config: AnalysisConfig) -> pd.DataFrame:
    return analyze_dataframe(load_reviews(path), config=analysis_config)


@st.cache_data(show_spinner=False)
def build_rating_distribution(df: pd.DataFrame) -> pd.Series:
    return df["score"].value_counts().reindex(range(1, 6), fill_value=0).rename("Reviews")


@st.cache_data(show_spinner=False)
def build_sentiment_distribution(df: pd.DataFrame) -> pd.Series:
    return df["sentiment_label"].value_counts().reindex(SENTIMENTS, fill_value=0).rename("Reviews")


@st.cache_data(show_spinner=False)
def build_segment_distribution(df: pd.DataFrame) -> pd.Series:
    return df["user_segment"].value_counts().reindex(SEGMENTS, fill_value=0).rename("Reviews")


@st.cache_data(show_spinner=False)
def build_pain_point_distribution(df: pd.DataFrame, pain_points: tuple[str, ...]) -> pd.Series:
    result = df[list(pain_points)].sum().sort_values(ascending=True).rename("Reviews")
    result.index = result.index.str.replace("_", " ").str.title()
    return result


@st.cache_data(show_spinner=False)
def build_pain_points_by_rating(df: pd.DataFrame, pain_points: tuple[str, ...]) -> pd.DataFrame:
    result = df.groupby("score")[list(pain_points)].sum().reindex(range(1, 6), fill_value=0)
    result.columns = result.columns.str.replace("_", " ").str.title()
    return result


@st.cache_data(show_spinner=False)
def build_sentiment_rating(df: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(df["score"], df["sentiment_label"]).reindex(index=range(1, 6), columns=SENTIMENTS, fill_value=0)


@st.cache_data(show_spinner=False)
def build_cooccurrence(df: pd.DataFrame, pain_points: tuple[str, ...]) -> pd.DataFrame:
    result = df[list(pain_points)].T.dot(df[list(pain_points)])
    result.index = result.index.str.replace("_", " ").str.title()
    result.columns = result.columns.str.replace("_", " ").str.title()
    return result


@st.cache_data(show_spinner=False)
def build_review_trend(df: pd.DataFrame) -> pd.Series:
    return (
        df.assign(review_date=pd.to_datetime(df["at"], errors="coerce"))
        .dropna(subset=["review_date"])
        .set_index("review_date")
        .resample("D")
        .size()
        .rename("Reviews")
    )


def render_methodology(config: AnalysisConfig, df: pd.DataFrame) -> None:
    with st.expander("Methodology & analytical quality"):
        st.markdown("### Sentiment")
        st.write("Sentiment is calculated with TextBlob polarity. Scores above the configured positive threshold are positive; scores below the negative threshold are negative; values in between are neutral.")
        st.warning("TextBlob is an English-oriented rule/statistical approach and does not reliably understand Hindi, Hinglish, emojis, sarcasm, or product-specific language. Sentiment labels are therefore inferred, not ground truth.")
        st.markdown("### Pain-point tagging")
        st.write("Pain points are inferred from case-insensitive keyword matching across six categories: delivery, cancellation, refund, customer support, pricing, and food quality. A keyword match is not proof that the underlying issue occurred.")
        st.markdown("### User segmentation")
        st.write("Segments are heuristic classifications derived from star rating and the number of matched pain points. In particular, `churned` means a one-star review with at least the configured number of pain points; it does not represent observed customer churn.")
        st.markdown("### Configured rules")
        st.table(pd.DataFrame([
            ["Positive sentiment", f"> {config.positive_sentiment_threshold:.2f}"],
            ["Negative sentiment", f"< {config.negative_sentiment_threshold:.2f}"],
            ["Churned", f"{config.churn_rating}-star + ≥{config.churn_min_pain_points} pain points"],
            ["At risk", f"≤{config.at_risk_max_rating}-star + ≥{config.at_risk_min_pain_points} pain point"],
            ["Satisfied", f"≥{config.satisfied_min_rating}-star"],
        ], columns=["Rule", "Definition"]))
        st.markdown("### Source vs derived fields")
        st.write("Source/measured fields include review text, star rating, thumbs-up count, review timestamp, and app version when supplied by the dataset. Derived fields include sentiment score/label, pain-point flags, user segment, complaint flag, and all aggregates/charts based on them.")
        st.markdown("### Dataset coverage & freshness")
        dates = pd.to_datetime(df["at"], errors="coerce").dropna()
        coverage = f"{dates.min():%Y-%m-%d} to {dates.max():%Y-%m-%d}" if not dates.empty else "Unavailable"
        latest = f"{dates.max():%Y-%m-%d %H:%M:%S}" if not dates.empty else "Unavailable"
        metadata = load_metadata(METADATA_PATH)
        st.write(f"Dataset rows: **{len(df):,}**  ")
        st.write(f"Review coverage: **{coverage}**  ")
        st.write(f"Latest source review timestamp: **{latest}**  ")
        if metadata:
            st.write(f"Last ingestion retrieval: **{metadata.get('retrieved_at_utc', 'Unavailable')}**  ")
            st.write(f"Ingestion snapshot: **{metadata.get('snapshot_path', 'Unavailable')}**  ")
        else:
            st.info("No ingestion metadata is available yet. The committed dataset remains the last known-good snapshot.")
        st.write(f"Dashboard analysis generated: **{datetime.now(timezone.utc):%Y-%m-%d %H:%M:%S UTC}**")


with st.sidebar:
    st.header("Filters")
    if st.button("Reset filters", use_container_width=True):
        for key in ["rating_filter", "sentiment_filter", "segment_filter", "pain_filter", "search_filter", "date_filter"]:
            st.session_state.pop(key, None)
        st.rerun()

    st.subheader("Analysis configuration")
    positive_threshold = st.number_input("Positive sentiment threshold", min_value=0.0, max_value=1.0, value=DEFAULT_CONFIG.positive_sentiment_threshold, step=0.05, key="positive_threshold")
    negative_threshold = st.number_input("Negative sentiment threshold", min_value=-1.0, max_value=0.0, value=DEFAULT_CONFIG.negative_sentiment_threshold, step=0.05, key="negative_threshold")
    churn_min_pain_points = st.number_input("Churned: minimum pain points", min_value=1, max_value=6, value=DEFAULT_CONFIG.churn_min_pain_points, step=1, key="churn_min_pain_points")
    at_risk_max_rating = st.slider("At risk: maximum rating", min_value=1, max_value=5, value=DEFAULT_CONFIG.at_risk_max_rating, key="at_risk_max_rating")
    at_risk_min_pain_points = st.number_input("At risk: minimum pain points", min_value=1, max_value=6, value=DEFAULT_CONFIG.at_risk_min_pain_points, step=1, key="at_risk_min_pain_points")
    config = AnalysisConfig(
        positive_sentiment_threshold=positive_threshold,
        negative_sentiment_threshold=negative_threshold,
        churn_min_pain_points=churn_min_pain_points,
        at_risk_max_rating=at_risk_max_rating,
        at_risk_min_pain_points=at_risk_min_pain_points,
    )

    rating_filter = st.multiselect("Rating", sorted(pd.Series(range(1, 6))), key="rating_filter")
    sentiment_filter = st.multiselect("Sentiment", SENTIMENTS, key="sentiment_filter")
    segment_filter = st.multiselect("User segment", SEGMENTS, key="segment_filter")
    pain_filter = st.multiselect("Pain point", PAIN_POINTS, key="pain_filter")
    search_filter = st.text_input("Search review text", placeholder="e.g. refund, delivery", key="search_filter")


try:
    modified_time_ns = DATA_PATH.stat().st_mtime_ns
    with st.spinner("Loading and analyzing review data..."):
        df = load_analyzed_data(str(DATA_PATH), modified_time_ns, config)
except (FileNotFoundError, OSError, ValueError, KeyError) as exc:
    st.error(f"Unable to load the review dataset safely: {exc}")
    st.info("The application uses the committed last-known-good CSV snapshot. Verify that the dataset exists and matches the documented schema.")
    st.stop()

with st.sidebar:
    dates = pd.to_datetime(df["at"], errors="coerce").dropna()
    date_filter = None
    if not dates.empty:
        date_filter = st.date_input("Review date", value=(dates.min().date(), dates.max().date()), min_value=dates.min().date(), max_value=dates.max().date(), key="date_filter")

filtered = df.copy()
if rating_filter:
    filtered = filtered[filtered["score"].isin(rating_filter)]
if sentiment_filter:
    filtered = filtered[filtered["sentiment_label"].isin(sentiment_filter)]
if segment_filter:
    filtered = filtered[filtered["user_segment"].isin(segment_filter)]
if pain_filter:
    available_pain_filter = [column for column in pain_filter if column in filtered.columns]
    if available_pain_filter:
        filtered = filtered[filtered[available_pain_filter].eq(1).all(axis=1)]
if search_filter.strip():
    filtered = filtered[filtered["content"].str.contains(search_filter.strip(), case=False, na=False)]
if date_filter and len(date_filter) == 2:
    start, end = pd.Timestamp(date_filter[0]), pd.Timestamp(date_filter[1]) + pd.Timedelta(days=1)
    timestamps = pd.to_datetime(filtered["at"], errors="coerce")
    filtered = filtered[(timestamps >= start) & (timestamps < end)]

render_methodology(config, df)

count = len(filtered)
average_rating = filtered["score"].mean() if count else 0
negative_share = filtered["sentiment_label"].eq("negative").sum()
churned_share = filtered["user_segment"].eq("churned").sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Reviews", f"{count:,}")
m2.metric("Average rating", f"{average_rating:.2f}/5" if count else "—")
m3.metric("Negative sentiment", format_percent(negative_share, count))
m4.metric("Churned heuristic", format_percent(churned_share, count))

st.divider()
if filtered.empty:
    st.warning("No reviews match the active filters. Try removing a filter or reset the filters.")
    st.stop()

pain_point_tuple = tuple(PAIN_POINTS)
left, right = st.columns(2)
with left:
    st.subheader("Rating distribution")
    st.bar_chart(build_rating_distribution(filtered))
with right:
    st.subheader("Sentiment distribution")
    st.bar_chart(build_sentiment_distribution(filtered))

left, right = st.columns(2)
with left:
    st.subheader("User segments")
    st.bar_chart(build_segment_distribution(filtered))
with right:
    st.subheader("Top pain points")
    st.bar_chart(build_pain_point_distribution(filtered, pain_point_tuple))

left, right = st.columns(2)
with left:
    st.subheader("Pain points by rating")
    st.bar_chart(build_pain_points_by_rating(filtered, pain_point_tuple))
with right:
    st.subheader("Sentiment vs rating")
    st.bar_chart(build_sentiment_rating(filtered))

st.subheader("Pain-point co-occurrence")
st.dataframe(build_cooccurrence(filtered, pain_point_tuple), use_container_width=True)

if pd.to_datetime(filtered["at"], errors="coerce").notna().any():
    st.subheader("Review trend")
    st.line_chart(build_review_trend(filtered))

st.subheader("Recent reviews")
review_columns = ["at", "score", "sentiment_label", "user_segment", "content"]
review_view = filtered.sort_values("at", ascending=False)[review_columns].head(20).copy()
review_view["sentiment_label"] = review_view["sentiment_label"].str.title()
review_view["user_segment"] = review_view["user_segment"].str.replace("_", " ").str.title()
review_view = review_view.rename(columns={"at": "Date", "score": "Rating", "sentiment_label": "Sentiment", "user_segment": "Segment", "content": "Review"})
st.dataframe(review_view, use_container_width=True, hide_index=True)

st.caption(f"Showing {count:,} of {len(df):,} analyzed reviews. Derived sentiment, pain points, and segments are analytical heuristics.")
render_review_explorer(filtered, PAIN_POINTS, detail_renderer=render_review_detail)
