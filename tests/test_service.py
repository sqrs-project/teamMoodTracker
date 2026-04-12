"""Service-layer tests."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from team_mood_tracker.domain.service import MoodService
from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.models import EntryCreateRequest


def test_upsert_entry_uses_current_day_and_reports_created(
    monkeypatch: pytest.MonkeyPatch, service: MoodService
) -> None:
    """The service should create today's entry using the shared clock helpers."""

    monkeypatch.setattr("team_mood_tracker.domain.service.current_date", lambda: date(2026, 4, 6))
    monkeypatch.setattr(
        "team_mood_tracker.domain.service.current_timestamp",
        lambda: datetime(2026, 4, 6, 8, 30, 0),
    )

    response = service.upsert_entry(
        EntryCreateRequest(user="Alice", mood=Mood.HAPPY, comment="All good")
    )

    assert response.action == "created"
    assert response.entry.entry_date == date(2026, 4, 6)
    assert response.entry.mood_emoji == "😊"


def test_summary_and_trends_are_aggregated(service: MoodService, seed_entries: None) -> None:
    """Summary and trend helpers should reflect the seeded data."""

    summary = service.get_summary()
    trends = service.get_trends()
    alice_trends = service.get_trends(user="Alice")

    assert summary.total_entries == 3
    assert summary.unique_users == 2
    assert summary.average_score == 2.0
    assert [point.average_score for point in trends.points] == [2.5, 1.0]
    assert [point.average_score for point in alice_trends.points] == [3.0, 1.0]


def test_analytics_return_empty_state_without_entries(service: MoodService) -> None:
    """Analytics should return stable zero/empty responses when no data exists."""

    summary = service.get_summary()
    distribution = service.get_distribution()
    team_trends = service.get_trends()
    user_trends = service.get_trends(user="Alice")

    assert summary.total_entries == 0
    assert summary.unique_users == 0
    assert summary.average_score == 0.0
    assert [item.count for item in summary.mood_breakdown] == [0, 0, 0]
    assert [item.count for item in distribution.items] == [0, 0, 0]
    assert team_trends.scope == "team"
    assert team_trends.points == []
    assert user_trends.scope == "user"
    assert user_trends.user == "Alice"
    assert user_trends.points == []
