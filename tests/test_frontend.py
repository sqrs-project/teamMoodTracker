"""Frontend helper tests."""

from __future__ import annotations

from datetime import date, datetime

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
from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.models import (
    DistributionItem,
    DistributionResponse,
    EntriesResponse,
    EntryResponse,
    TrendPoint,
    TrendsResponse,
)


def test_presenters_build_expected_dataframes() -> None:
    """Presentation helpers should build frames for charts and tables."""

    entries = EntriesResponse(
        total=1,
        items=[
            EntryResponse(
                id=1,
                user="Alice",
                mood=Mood.HAPPY,
                mood_emoji="😊",
                mood_label="Happy",
                comment="Nice day",
                entry_date=date(2026, 4, 6),
                created_at=datetime(2026, 4, 6, 9, 0, 0),
                updated_at=datetime(2026, 4, 6, 9, 30, 0),
            )
        ],
    )
    trends = TrendsResponse(
        scope="team",
        user=None,
        points=[TrendPoint(entry_date=date(2026, 4, 6), average_score=2.5)],
    )
    distribution = DistributionResponse(
        items=[DistributionItem(mood=Mood.HAPPY, mood_label="Happy", mood_emoji="😊", count=2)]
    )

    entries_data = entries_frame(entries)
    trend_data = trend_frame(trends)
    distribution_data = distribution_frame(distribution)
    chart_spec = distribution_chart(distribution).to_dict()

    assert list(entries_data.columns) == ["User", "Mood", "Comment", "Date", "Updated"]
    assert trend_data.iloc[0]["Score"] == 2.5
    assert distribution_data.iloc[0]["Count"] == 2
    assert chart_spec["encoding"]["y"]["scale"]["domainMin"] == 0


def test_presenters_handle_mood_formatting_and_ranges() -> None:
    """Formatting helpers should expose consistent labels and date ranges."""

    assert format_mood(Mood.STRESSED) == "😫 Stressed"
    assert parse_mood("😊 Happy") == Mood.HAPPY
    assert "😐 Neutral" in mood_options()
    assert range_to_dates("All time", date(2026, 4, 6)) == (None, None)
    assert range_to_dates("Last 7 days", date(2026, 4, 6))[0] == date(2026, 3, 31)
