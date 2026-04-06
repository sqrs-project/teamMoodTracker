"""Pydantic models exposed by the API and frontend client."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from team_mood_tracker.shared.constants import MAX_COMMENT_LENGTH, MAX_USER_LENGTH, Mood


class EntryCreateRequest(BaseModel):
    """Payload used to create or update today's mood entry."""

    user: str = Field(..., max_length=MAX_USER_LENGTH, examples=["Alice"])
    mood: Mood = Field(..., examples=[Mood.HAPPY.value])
    comment: str | None = Field(
        default=None,
        max_length=MAX_COMMENT_LENGTH,
        examples=["Feeling good after the sprint review."],
    )

    @field_validator("user")
    @classmethod
    def validate_user(cls, value: str) -> str:
        """Strip and validate the user field."""

        cleaned = value.strip()
        if not cleaned:
            msg = "User must not be empty."
            raise ValueError(msg)
        return cleaned

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str | None) -> str | None:
        """Normalize the comment value."""

        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class EntryResponse(BaseModel):
    """Serialized mood entry returned by the API."""

    id: int
    user: str
    mood: Mood
    mood_emoji: str
    mood_label: str
    comment: str | None
    entry_date: date
    created_at: datetime
    updated_at: datetime


class EntryUpsertResponse(BaseModel):
    """Response returned after creating or updating an entry."""

    action: str = Field(..., examples=["created"])
    entry: EntryResponse


class EntriesResponse(BaseModel):
    """Paginated-style response for the entries collection."""

    total: int
    items: list[EntryResponse]


class TrendPoint(BaseModel):
    """Single point in the trend graph."""

    entry_date: date
    average_score: float


class TrendsResponse(BaseModel):
    """Trend dataset returned by the analytics endpoint."""

    scope: str = Field(..., examples=["team"])
    user: str | None = Field(default=None, examples=["Alice"])
    points: list[TrendPoint]


class DistributionItem(BaseModel):
    """Distribution item for a single mood."""

    mood: Mood
    mood_label: str
    mood_emoji: str
    count: int


class DistributionResponse(BaseModel):
    """Mood distribution returned by the analytics endpoint."""

    items: list[DistributionItem]


class SummaryResponse(BaseModel):
    """Summary metrics for a selected period."""

    total_entries: int
    unique_users: int
    average_score: float
    mood_breakdown: list[DistributionItem]


class ErrorResponse(BaseModel):
    """Simple API error payload."""

    detail: str
