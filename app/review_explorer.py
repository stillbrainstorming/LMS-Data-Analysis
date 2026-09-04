from __future__ import annotations

from typing import Callable

import pandas as pd
import streamlit as st


DISPLAY_COLUMNS = [
    "at",
    "score",
    "sentiment_score",
    "sentiment_label",
    "user_segment",
    "pain_point_tags",
    "appVersion",
    "thumbsUpCount",
    "content",
]


@st.cache_data(show_spinner=False)
def add_pain_point_tags(df: pd.DataFrame, pain_points: tuple[str, ...]) -> pd.DataFrame:
    frame = df.copy()
    available_pain_points = [column for column in pain_points if column in frame.columns]
    if not available_pain_points:
        frame["pain_point_tags"] = ""
        return frame
    frame["pain_point_tags"] = frame.apply(
        lambda row: ", ".join(
            label.replace("_", " ").title()
            for label in available_pain_points
            if row.get(label, 0) == 1
        ),
        axis=1,
    )
    return frame


@st.cache_data(show_spinner=False)
def filter_reviews(df: pd.DataFrame, search: str, ratings: tuple[int, ...], sentiments: tuple[str, ...], segments: tuple[str, ...], pain_points: tuple[str, ...], start_date=None, end_date=None) -> pd.DataFrame:
    filtered = df.copy()
    if ratings:
        filtered = filtered[filtered["score"].isin(ratings)]
    if sentiments:
        filtered = filtered[filtered["sentiment_label"].isin(sentiments)]
    if segments:
        filtered = filtered[filtered["user_segment"].isin(segments)]
    available_pain_points = [column for column in pain_points if column in filtered.columns]
    if available_pain_points:
        filtered = filtered[filtered[available_pain_points].eq(1).all(axis=1)]
    if search.strip():
        filtered = filtered[filtered["content"].str.contains(search.strip(), case=False, na=False)]
    dates = pd.to_datetime(filtered["at"], errors="coerce")
    if start_date is not None:
        filtered = filtered[dates.dt.date >= start_date]
        dates = pd.to_datetime(filtered["at"], errors="coerce")
    if end_date is not None:
        filtered = filtered[dates.dt.date <= end_date]
    return filtered


def render_review_explorer(df: pd.DataFrame, pain_points: list[str], page_size: int = 20, detail_renderer: Callable[[pd.Series], None] | None = None) -> None:
    st.subheader("Review Explorer")
    with st.expander("Review filters", expanded=True):
        search = st.text_input("Search review text", key="explorer_search")
        ratings = tuple(st.multiselect("Rating", sorted(df["score"].dropna().unique()), key="explorer_ratings"))
        sentiments = tuple(st.multiselect("Sentiment", sorted(df["sentiment_label"].dropna().unique()), key="explorer_sentiments"))
        segments = tuple(st.multiselect("User segment", sorted(df["user_segment"].dropna().unique()), key="explorer_segments"))
        selected_pain_points = tuple(st.multiselect("Pain point", pain_points, format_func=lambda value: value.replace("_", " ").title(), key="explorer_pain_points"))
        available_dates = pd.to_datetime(df["at"], errors="coerce").dropna()
        start_date = end_date = None
        if not available_dates.empty:
            date_value = st.date_input("Review date", value=(available_dates.min().date(), available_dates.max().date()), min_value=available_dates.min().date(), max_value=available_dates.max().date(), key="explorer_dates")
            if isinstance(date_value, tuple) and len(date_value) == 2:
                start_date, end_date = date_value
    filtered = filter_reviews(df, search, ratings, sentiments, segments, selected_pain_points, start_date, end_date)
    filtered = add_pain_point_tags(filtered, tuple(pain_points))
    if filtered.empty:
        st.info("No reviews match the selected filters.")
        return
    sort_options = {"Newest": ("at", False), "Oldest": ("at", True), "Highest rating": ("score", False), "Lowest rating": ("score", True), "Most helpful": ("thumbsUpCount", False)}
    sort_label = st.selectbox("Sort reviews", list(sort_options), key="explorer_sort")
    sort_column, ascending = sort_options[sort_label]
    if sort_column not in filtered.columns:
        sort_column, ascending = "at", False
    filtered = filtered.sort_values(sort_column, ascending=ascending, na_position="last")
    page_count = max(1, (len(filtered) + page_size - 1) // page_size)
    current_page = int(st.session_state.get("explorer_page", 1))
    if current_page > page_count:
        st.session_state["explorer_page"] = 1
    page = st.number_input("Page", min_value=1, max_value=page_count, value=min(current_page, page_count), step=1, key="explorer_page")
    start = (page - 1) * page_size
    page_df = filtered.iloc[start : start + page_size]
    display_columns = [column for column in DISPLAY_COLUMNS if column in page_df.columns]
    display_df = page_df[display_columns].copy()
    display_df = display_df.rename(columns={"at": "Date", "score": "Rating", "sentiment_score": "Sentiment Score", "sentiment_label": "Sentiment", "user_segment": "Segment", "pain_point_tags": "Pain Points", "appVersion": "App Version", "thumbsUpCount": "Helpful", "content": "Review"})
    if "Segment" in display_df.columns:
        display_df["Segment"] = display_df["Segment"].astype("string").str.replace("_", " ").str.title()
    st.caption(f"Showing {start + 1}-{min(start + page_size, len(filtered))} of {len(filtered):,} matching reviews")
    st.dataframe(page_df[display_columns].rename(columns={"at": "Date", "score": "Rating", "sentiment_score": "Sentiment Score", "sentiment_label": "Sentiment", "user_segment": "Segment", "pain_point_tags": "Pain Points", "appVersion": "App Version", "thumbsUpCount": "Helpful", "content": "Review"}).assign(**({"Segment": display_df["Segment"]} if "Segment" in display_df.columns else {})), use_container_width=True, hide_index=True)
    if detail_renderer is not None:
        st.subheader("Review Detail")
        options = page_df.index.tolist()
        selected_index = st.selectbox("Select a review", options, format_func=lambda index: f"{page_df.loc[index, 'score']}★ — {str(page_df.loc[index, 'content'])[:90]}", key="explorer_selected_review")
        detail_renderer(page_df.loc[selected_index])
