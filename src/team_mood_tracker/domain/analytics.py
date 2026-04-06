"""Pure analytics helpers for mood entries."""

from __future__ import annotations

from collections import defaultdict

from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.entities import MoodEntryRecord
from team_mood_tracker.shared.models import (
    DistributionItem,
    SummaryResponse,
    TrendPoint,
    TrendsResponse,
)


def build_distribution(entries: list[MoodEntryRecord]) -> list[DistributionItem]:
    """Build distribution items from a list of entries."""

    counts = {mood: 0 for mood in Mood}
    for entry in entries:
        counts[entry.mood] += 1
    return [_distribution_item(mood=mood, count=counts[mood]) for mood in Mood]


def build_summary(entries: list[MoodEntryRecord]) -> SummaryResponse:
    """Build summary metrics for a list of entries."""

    if not entries:
        return SummaryResponse(
            total_entries=0,
            unique_users=0,
            average_score=0.0,
            mood_breakdown=build_distribution([]),
        )
    total_score = sum(entry.mood.score for entry in entries)
    unique_users = len({entry.user for entry in entries})
    return SummaryResponse(
        total_entries=len(entries),
        unique_users=unique_users,
        average_score=round(total_score / len(entries), 2),
        mood_breakdown=build_distribution(entries),
    )


def build_team_trends(entries: list[MoodEntryRecord]) -> TrendsResponse:
    """Build daily team-average trend points."""

    grouped = defaultdict(list)
    for entry in entries:
        grouped[entry.entry_date].append(entry.mood.score)
    points = [
        TrendPoint(
            entry_date=entry_date,
            average_score=round(sum(scores) / len(scores), 2),
        )
        for entry_date, scores in sorted(grouped.items())
    ]
    return TrendsResponse(scope="team", user=None, points=points)


def build_user_trends(entries: list[MoodEntryRecord], user: str) -> TrendsResponse:
    """Build daily trend points for one user."""

    points = [
        TrendPoint(entry_date=entry.entry_date, average_score=float(entry.mood.score))
        for entry in sorted(entries, key=lambda entry: (entry.entry_date, entry.id))
    ]
    return TrendsResponse(scope="user", user=user, points=points)


def _distribution_item(*, mood: Mood, count: int) -> DistributionItem:
    """Build a single distribution item."""

    return DistributionItem(
        mood=mood,
        mood_label=mood.label,
        mood_emoji=mood.emoji,
        count=count,
    )
