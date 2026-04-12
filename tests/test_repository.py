"""Repository-level tests."""

from __future__ import annotations

from datetime import date, datetime

from team_mood_tracker.shared.constants import Mood, SortBy, SortOrder
from team_mood_tracker.storage.repository import MoodEntryRepository


def test_upsert_updates_existing_row(repository: MoodEntryRepository) -> None:
    """Upserting the same user and day should update the existing row."""

    created = repository.upsert_entry(
        user="Alice",
        mood=Mood.HAPPY,
        comment="Initial",
        entry_date=date(2026, 4, 6),
        timestamp=datetime(2026, 4, 6, 9, 0, 0),
    )
    updated = repository.upsert_entry(
        user="Alice",
        mood=Mood.STRESSED,
        comment="Updated",
        entry_date=date(2026, 4, 6),
        timestamp=datetime(2026, 4, 6, 12, 0, 0),
    )

    assert created.action == "created"
    assert updated.action == "updated"
    assert updated.entry.id == created.entry.id
    assert updated.entry.comment == "Updated"
    assert updated.entry.updated_at.isoformat() == "2026-04-06T12:00:00"


def test_list_entries_applies_filters_and_sorting(repository: MoodEntryRepository) -> None:
    """Repository listing should honor filters and sorting arguments."""

    repository.upsert_entry(
        user="Alice",
        mood=Mood.HAPPY,
        comment=None,
        entry_date=date(2026, 4, 4),
        timestamp=datetime(2026, 4, 4, 9, 0, 0),
    )
    repository.upsert_entry(
        user="Bob",
        mood=Mood.NEUTRAL,
        comment=None,
        entry_date=date(2026, 4, 5),
        timestamp=datetime(2026, 4, 5, 9, 0, 0),
    )

    entries = repository.list_entries(
        date_from=date(2026, 4, 5),
        sort_by=SortBy.USER,
        sort_order=SortOrder.ASC,
    )

    assert [entry.user for entry in entries] == ["Bob"]


def test_list_entries_supports_mood_sort_order(repository: MoodEntryRepository) -> None:
    """Sorting by mood should use stressed < neutral < happy ordering."""

    repository.upsert_entry(
        user="Alice",
        mood=Mood.HAPPY,
        comment=None,
        entry_date=date(2026, 4, 6),
        timestamp=datetime(2026, 4, 6, 9, 0, 0),
    )
    repository.upsert_entry(
        user="Bob",
        mood=Mood.STRESSED,
        comment=None,
        entry_date=date(2026, 4, 6),
        timestamp=datetime(2026, 4, 6, 9, 10, 0),
    )
    repository.upsert_entry(
        user="Carol",
        mood=Mood.NEUTRAL,
        comment=None,
        entry_date=date(2026, 4, 6),
        timestamp=datetime(2026, 4, 6, 9, 20, 0),
    )

    asc_entries = repository.list_entries(sort_by=SortBy.MOOD, sort_order=SortOrder.ASC)
    desc_entries = repository.list_entries(sort_by=SortBy.MOOD, sort_order=SortOrder.DESC)

    assert [entry.mood for entry in asc_entries] == [Mood.STRESSED, Mood.NEUTRAL, Mood.HAPPY]
    assert [entry.mood for entry in desc_entries] == [Mood.HAPPY, Mood.NEUTRAL, Mood.STRESSED]
