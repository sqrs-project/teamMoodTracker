"""Pure presentation helpers for Streamlit views."""

from __future__ import annotations

from datetime import date, timedelta

import altair as alt
import pandas as pd

from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.models import DistributionResponse, EntriesResponse, TrendsResponse


def mood_options() -> list[str]:
    """Return mood labels formatted for the UI."""

    return [format_mood(mood) for mood in Mood]


def parse_mood(option: str) -> Mood:
    """Extract the mood enum value from a formatted option."""

    mood_name = option.split(" ", maxsplit=1)[1].strip().lower()
    return Mood(mood_name)


def format_mood(mood: Mood) -> str:
    """Return the formatted mood label."""

    return f"{mood.emoji} {mood.label}"


def entries_frame(entries: EntriesResponse) -> pd.DataFrame:
    """Convert entries into a dataframe for display."""

    rows = [
        {
            "User": item.user,
            "Mood": f"{item.mood_emoji} {item.mood_label}",
            "Comment": item.comment or "",
            "Date": item.entry_date.isoformat(),
            "Updated": item.updated_at.isoformat(sep=" "),
        }
        for item in entries.items
    ]
    return pd.DataFrame(rows)


def trend_frame(trends: TrendsResponse) -> pd.DataFrame:
    """Convert trend points into a dataframe for charting."""

    rows = [
        {"Date": point.entry_date.isoformat(), "Score": point.average_score}
        for point in trends.points
    ]
    return pd.DataFrame(rows)


def trend_chart(trends: TrendsResponse) -> alt.Chart:
    """Build a fixed-scale line chart for mood trends."""

    data = trend_frame(trends)
    return (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X("Date:N", title="Date"),
            y=alt.Y("Score:Q", scale=alt.Scale(domain=[0, 3]), title="Mood Score"),
            tooltip=["Date:N", "Score:Q"],
        )
        .properties(height=320)
    )


def distribution_frame(distribution: DistributionResponse) -> pd.DataFrame:
    """Convert mood distribution into a dataframe for charting."""

    rows = [
        {"Mood": f"{item.mood_emoji} {item.mood_label}", "Count": item.count}
        for item in distribution.items
    ]
    return pd.DataFrame(rows)


def distribution_chart(distribution: DistributionResponse) -> alt.Chart:
    """Build a zero-based bar chart for the mood distribution."""

    data = distribution_frame(distribution)
    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X("Mood:N", sort=None, title="Mood"),
            y=alt.Y("Count:Q", scale=alt.Scale(domainMin=0), title="Count"),
            tooltip=["Mood:N", "Count:Q"],
        )
        .properties(height=320)
    )


def range_to_dates(option: str, today: date) -> tuple[date | None, date | None]:
    """Translate a range option into date filters."""

    if option == "All time":
        return None, None
    days = {"Last 7 days": 6, "Last 14 days": 13, "Last 30 days": 29}[option]
    return today - timedelta(days=days), today
