"""Domain entities shared between layers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from team_mood_tracker.shared.constants import Mood


@dataclass(frozen=True)
class MoodEntryRecord:
    """Stored mood entry record."""

    id: int
    user: str
    mood: Mood
    comment: str | None
    entry_date: date
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UpsertResult:
    """Result returned after a create-or-update operation."""

    action: str
    entry: MoodEntryRecord
