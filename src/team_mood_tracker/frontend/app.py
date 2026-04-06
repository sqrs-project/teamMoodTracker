"""Streamlit application entry point."""

from __future__ import annotations

from datetime import date

import streamlit as st

from team_mood_tracker.frontend.api_client import ApiClientError, MoodApiClient
from team_mood_tracker.frontend.presenters import (
    distribution_chart,
    distribution_frame,
    entries_frame,
    format_mood,
    mood_options,
    parse_mood,
    range_to_dates,
    trend_frame,
)
from team_mood_tracker.shared.config import get_settings
from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.models import (
    DistributionResponse,
    EntriesResponse,
    EntryCreateRequest,
    EntryResponse,
    SummaryResponse,
    TrendsResponse,
)


def main() -> None:  # pragma: no cover
    """Render the Streamlit dashboard."""

    settings = get_settings()
    client = MoodApiClient(base_url=settings.api_base_url)
    today = date.today()
    st.set_page_config(page_title="Team Mood Tracker", layout="wide")
    st.title("Team Mood Tracker")
    st.caption("Track one mood per user per day. Re-submitting today updates the existing entry.")

    _render_submission_section(client=client, today=today)
    st.divider()
    _render_dashboard_section(client=client, today=today)


def _render_submission_section(*, client: MoodApiClient, today: date) -> None:  # pragma: no cover
    """Render the submission form."""

    st.subheader("Today's Mood")
    user_name = st.text_input("User", placeholder="Enter your name")
    existing_entry = _load_existing_entry(client=client, user_name=user_name, today=today)
    _render_submission_hint(user_name=user_name, existing_entry=existing_entry)
    default_mood, default_comment = _submission_defaults(existing_entry)
    with st.form("submission_form"):
        option = st.radio(
            "Mood",
            mood_options(),
            index=list(Mood).index(default_mood),
            horizontal=True,
        )
        comment = st.text_area(
            "Comment (optional)",
            value=default_comment,
            max_chars=280,
            placeholder="Add context if you want.",
        )
        submitted = st.form_submit_button("Save today's mood")
    if not submitted:
        return
    _save_entry(client=client, user_name=user_name, mood=parse_mood(option), comment=comment)


def _render_dashboard_section(*, client: MoodApiClient, today: date) -> None:  # pragma: no cover
    """Render analytics and recent entries."""

    st.subheader("Team Overview")
    range_option = st.selectbox(
        "Time range",
        ["Last 7 days", "Last 14 days", "Last 30 days", "All time"],
    )
    date_from, date_to = range_to_dates(range_option, today)
    dashboard_data = _load_dashboard_data(
        client=client,
        today=today,
        date_from=date_from,
        date_to=date_to,
    )
    if dashboard_data is None:
        return
    summary, today_summary, trends, distribution, recent_entries = dashboard_data
    _render_metrics(summary=summary, today_summary=today_summary)
    _render_team_charts(trends=trends, distribution=distribution)
    _render_optional_user_trend(
        client=client,
        recent_entries=recent_entries,
        date_from=date_from,
        date_to=date_to,
    )
    _render_recent_entries(recent_entries)


def _render_user_trend(
    *,
    client: MoodApiClient,
    selected_user: str,
    date_from: date | None,
    date_to: date | None,
) -> None:  # pragma: no cover
    """Render a trend chart for the selected user."""

    try:
        user_trends = client.get_trends(user=selected_user, date_from=date_from, date_to=date_to)
    except ApiClientError as error:
        st.error(str(error))
        return
    st.markdown(f"#### {selected_user}'s Trend")
    data = trend_frame(user_trends)
    if data.empty:
        st.info("No history for this user yet.")
        return
    st.line_chart(data.set_index("Date"))


def _load_existing_entry(  # pragma: no cover
    *, client: MoodApiClient, user_name: str, today: date
) -> EntryResponse | None:
    """Load today's entry for a user."""

    if not user_name.strip():
        return None
    try:
        return client.get_today_entry(user=user_name, today=today)
    except ApiClientError as error:
        st.warning(str(error))
        return None


def _render_submission_hint(  # pragma: no cover
    *, user_name: str, existing_entry: EntryResponse | None
) -> None:
    """Render the helper message above the submission form."""

    if not user_name.strip():
        return
    if existing_entry is None:
        st.caption("No mood saved for today yet.")
        return
    st.info("Today's entry already exists. Saving again will update it.")


def _submission_defaults(  # pragma: no cover
    existing_entry: EntryResponse | None,
) -> tuple[Mood, str]:
    """Return default form values for the submission form."""

    if existing_entry is None:
        return Mood.NEUTRAL, ""
    return existing_entry.mood, existing_entry.comment or ""


def _load_dashboard_data(  # pragma: no cover
    *,
    client: MoodApiClient,
    today: date,
    date_from: date | None,
    date_to: date | None,
) -> (
    tuple[
        SummaryResponse,
        SummaryResponse,
        TrendsResponse,
        DistributionResponse,
        EntriesResponse,
    ]
    | None
):
    """Fetch all data required for the dashboard."""

    try:
        return (
            client.get_summary(date_from=date_from, date_to=date_to),
            client.get_summary(date_from=today, date_to=today),
            client.get_trends(date_from=date_from, date_to=date_to),
            client.get_distribution(date_from=date_from, date_to=date_to),
            client.list_entries(date_from=date_from, date_to=date_to),
        )
    except ApiClientError as error:
        st.error(str(error))
        return None


def _render_metrics(  # pragma: no cover
    *,
    summary: SummaryResponse,
    today_summary: SummaryResponse,
) -> None:
    """Render the summary metrics at the top of the dashboard."""

    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Entries Today", today_summary.total_entries)
    metric_two.metric("Unique Users", summary.unique_users)
    metric_three.metric("Average Mood Score", summary.average_score)


def _render_team_charts(  # pragma: no cover
    *,
    trends: TrendsResponse,
    distribution: DistributionResponse,
) -> None:
    """Render the team trend and distribution charts."""

    trend_column, distribution_column = st.columns(2)
    with trend_column:
        st.markdown("#### Team Trend")
        trend_data = trend_frame(trends)
        if trend_data.empty:
            st.info("No trend data yet. Submit the first check-in.")
        else:
            st.line_chart(trend_data.set_index("Date"))
    with distribution_column:
        st.markdown("#### Mood Distribution")
        distribution_data = distribution_frame(distribution)
        if distribution_data.empty or int(distribution_data["Count"].sum()) == 0:
            st.info("No distribution data yet.")
        else:
            st.altair_chart(distribution_chart(distribution), use_container_width=True)


def _render_optional_user_trend(  # pragma: no cover
    *,
    client: MoodApiClient,
    recent_entries: EntriesResponse,
    date_from: date | None,
    date_to: date | None,
) -> None:
    """Render the user-specific trend selector and chart when data exists."""

    users = sorted({entry.user for entry in recent_entries.items})
    if not users:
        return
    selected_user = st.selectbox("User trend", ["Team average", *users])
    if selected_user == "Team average":
        return
    _render_user_trend(
        client=client,
        selected_user=selected_user,
        date_from=date_from,
        date_to=date_to,
    )


def _render_recent_entries(recent_entries: EntriesResponse) -> None:  # pragma: no cover
    """Render the recent entries table."""

    st.markdown("#### Recent Entries")
    entries_data = entries_frame(recent_entries)
    if entries_data.empty:
        st.info("No mood entries found for the selected period.")
        return
    st.dataframe(entries_data, use_container_width=True, hide_index=True)


def _save_entry(  # pragma: no cover
    *, client: MoodApiClient, user_name: str, mood: Mood, comment: str
) -> None:
    """Persist the submitted entry and report the outcome."""

    payload = EntryCreateRequest(user=user_name, mood=mood, comment=comment)
    try:
        response = client.save_entry(payload)
    except (ApiClientError, ValueError) as error:
        st.error(str(error))
        return
    verb = "updated" if response.action == "updated" else "saved"
    st.success(f"Today's mood was {verb}: {format_mood(response.entry.mood)}")


if __name__ == "__main__":  # pragma: no cover
    main()
