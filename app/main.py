from pathlib import Path
import sys

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.analysis.pain_points import pain_point_columns
from src.data.reviews import load_reviews
from src.pipeline import analyze_dataframe

DATA_PATH = ROOT / "data" / "lms_reviews_segmented.csv"
PAIN_POINTS = pain_point_columns()
SEGMENTS = ["satisfied", "passive", "at_risk", "churned"]
SENTIMENTS = ["positive", "neutral", "negative"]

st.set_page_config(page_title="LMS Review Intelligence", page_icon="📊", layout="wide")
st.markdown("# LMS Review Intelligence")
st.caption("Interactive product analytics for customer reviews")

@st.cache_data
def load_analyzed_data(path: str) -> pd.DataFrame:
    return analyze_dataframe(load_reviews(path))


def format_percent(value: float, total: int) -> str:
    return f"{value / total * 100:.1f}%" if total else "0.0%"


try:
    df = load_analyzed_data(str(DATA_PATH))
except (FileNotFoundError, ValueError, KeyError) as exc:
    st.error(f"Unable to load the review dataset: {exc}")
    st.stop()

with st.sidebar:
    st.header("Filters")
    if st.button("Reset filters", use_container_width=True):
        for key in ["rating_filter", "sentiment_filter", "segment_filter", "pain_filter", "search_filter", "date_filter"]:
            st.session_state.pop(key, None)
        st.rerun()

    rating_filter = st.multiselect("Rating", sorted(df["score"].dropna().unique()), key="rating_filter")
    sentiment_filter = st.multiselect("Sentiment", SENTIMENTS, key="sentiment_filter")
    segment_filter = st.multiselect("User segment", SEGMENTS, key="segment_filter")
    pain_filter = st.multiselect("Pain point", PAIN_POINTS, key="pain_filter")
    search_filter = st.text_input("Search review text", placeholder="e.g. refund, delivery", key="search_filter")

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
    filtered = filtered[filtered[pain_filter].eq(1).all(axis=1)]
if search_filter.strip():
    filtered = filtered[filtered["content"].str.contains(search_filter.strip(), case=False, na=False)]
if date_filter and len(date_filter) == 2:
    start, end = pd.Timestamp(date_filter[0]), pd.Timestamp(date_filter[1]) + pd.Timedelta(days=1)
    filtered = filtered[(filtered["at"] >= start) & (filtered["at"] < end)]

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

left, right = st.columns(2)

with left:
    st.subheader("Rating distribution")
    rating_chart = filtered["score"].value_counts().reindex(range(1, 6), fill_value=0).rename("Reviews")
    st.bar_chart(rating_chart)

with right:
    st.subheader("Sentiment distribution")
    sentiment_chart = filtered["sentiment_label"].value_counts().reindex(SENTIMENTS, fill_value=0).rename("Reviews")
    st.bar_chart(sentiment_chart)

left, right = st.columns(2)

with left:
    st.subheader("User segments")
    segment_chart = filtered["user_segment"].value_counts().reindex(SEGMENTS, fill_value=0).rename("Reviews")
    st.bar_chart(segment_chart)

with right:
    st.subheader("Top pain points")
    pain_chart = filtered[PAIN_POINTS].sum().sort_values(ascending=True).rename("Reviews")
    pain_chart.index = pain_chart.index.str.replace("_", " ").str.title()
    st.bar_chart(pain_chart)

left, right = st.columns(2)

with left:
    st.subheader("Pain points by rating")
    by_rating = filtered.groupby("score")[PAIN_POINTS].sum().reindex(range(1, 6), fill_value=0)
    by_rating.columns = by_rating.columns.str.replace("_", " ").str.title()
    st.bar_chart(by_rating)

with right:
    st.subheader("Sentiment vs rating")
    sentiment_rating = pd.crosstab(filtered["score"], filtered["sentiment_label"]).reindex(index=range(1, 6), columns=SENTIMENTS, fill_value=0)
    st.bar_chart(sentiment_rating)

st.subheader("Pain-point co-occurrence")
cooccurrence = filtered[PAIN_POINTS].T.dot(filtered[PAIN_POINTS])
cooccurrence.index = cooccurrence.index.str.replace("_", " ").str.title()
cooccurrence.columns = cooccurrence.columns.str.replace("_", " ").str.title()
st.dataframe(cooccurrence, use_container_width=True)

if filtered["at"].notna().any():
    st.subheader("Review trend")
    trend = filtered.assign(review_date=pd.to_datetime(filtered["at"], errors="coerce")).dropna(subset=["review_date"])
    trend = trend.set_index("review_date").resample("D").size().rename("Reviews")
    st.line_chart(trend)

st.subheader("Recent reviews")
review_columns = ["at", "score", "sentiment_label", "user_segment", "content"]
review_view = filtered.sort_values("at", ascending=False)[review_columns].head(20).copy()
review_view["sentiment_label"] = review_view["sentiment_label"].str.title()
review_view["user_segment"] = review_view["user_segment"].str.replace("_", " ").str.title()
review_view = review_view.rename(columns={"at": "Date", "score": "Rating", "sentiment_label": "Sentiment", "user_segment": "Segment", "content": "Review"})
st.dataframe(review_view, use_container_width=True, hide_index=True)

st.caption(f"Showing {count:,} of {len(df):,} analyzed reviews. Derived sentiment, pain points, and segments are analytical heuristics.")
