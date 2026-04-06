"""Shared constants used across the application."""

from __future__ import annotations

from enum import Enum

MAX_COMMENT_LENGTH = 280
MAX_USER_LENGTH = 64
DEFAULT_TIMEOUT_SECONDS = 5.0


class Mood(str, Enum):
    """Supported mood values."""

    HAPPY = "happy"
    NEUTRAL = "neutral"
    STRESSED = "stressed"

    @property
    def emoji(self) -> str:
        """Return the emoji representation of the mood."""

        return {
            Mood.HAPPY: "😊",
            Mood.NEUTRAL: "😐",
            Mood.STRESSED: "😫",
        }[self]

    @property
    def label(self) -> str:
        """Return the human-readable label of the mood."""

        return {
            Mood.HAPPY: "Happy",
            Mood.NEUTRAL: "Neutral",
            Mood.STRESSED: "Stressed",
        }[self]

    @property
    def score(self) -> int:
        """Return the numeric score used for aggregations."""

        return {
            Mood.HAPPY: 3,
            Mood.NEUTRAL: 2,
            Mood.STRESSED: 1,
        }[self]


class SortBy(str, Enum):
    """Supported sort columns for the entries list."""

    ENTRY_DATE = "entry_date"
    UPDATED_AT = "updated_at"
    USER = "user"
    MOOD = "mood"


class SortOrder(str, Enum):
    """Supported sort directions for the entries list."""

    ASC = "asc"
    DESC = "desc"
