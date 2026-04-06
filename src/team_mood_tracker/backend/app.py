"""FastAPI application factory and route definitions."""

from __future__ import annotations

from datetime import date
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Query, Response, status

from team_mood_tracker.domain.service import MoodService
from team_mood_tracker.shared.config import get_settings
from team_mood_tracker.shared.constants import Mood, SortBy, SortOrder
from team_mood_tracker.shared.models import (
    DistributionResponse,
    EntriesResponse,
    EntryCreateRequest,
    EntryResponse,
    EntryUpsertResponse,
    ErrorResponse,
    SummaryResponse,
    TrendsResponse,
)
from team_mood_tracker.storage.database import Database
from team_mood_tracker.storage.repository import MoodEntryRepository

ENTRY_EXAMPLE = {
    "id": 1,
    "user": "Alice",
    "mood": "happy",
    "mood_emoji": "😊",
    "mood_label": "Happy",
    "comment": "Feeling good after the sprint review.",
    "entry_date": "2026-04-06",
    "created_at": "2026-04-06T09:00:00",
    "updated_at": "2026-04-06T09:00:00",
}

UPSERT_EXAMPLE = {"action": "created", "entry": ENTRY_EXAMPLE}
ENTRIES_EXAMPLE = {"total": 1, "items": [ENTRY_EXAMPLE]}
TRENDS_EXAMPLE = {
    "scope": "team",
    "user": None,
    "points": [{"entry_date": "2026-04-05", "average_score": 2.5}],
}
DISTRIBUTION_EXAMPLE = {
    "items": [
        {"mood": "happy", "mood_label": "Happy", "mood_emoji": "😊", "count": 4},
        {"mood": "neutral", "mood_label": "Neutral", "mood_emoji": "😐", "count": 2},
        {"mood": "stressed", "mood_label": "Stressed", "mood_emoji": "😫", "count": 1},
    ]
}
SUMMARY_EXAMPLE = {
    "total_entries": 7,
    "unique_users": 4,
    "average_score": 2.43,
    "mood_breakdown": DISTRIBUTION_EXAMPLE["items"],
}
ERROR_EXAMPLE = {"detail": "Entry not found."}
NOT_FOUND_RESPONSE = {
    "model": ErrorResponse,
    "content": {"application/json": {"example": ERROR_EXAMPLE}},
}


def create_app(service: MoodService | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Team Mood Tracker API",
        version="0.1.0",
        description="API for recording daily moods and viewing team mood analytics.",
    )
    mood_service = service or default_service()
    mood_service.initialize()

    @app.post(
        "/entries",
        response_model=EntryUpsertResponse,
        summary="Create or update today's mood entry",
        description=(
            "Save today's mood for a user. Submitting twice on the same day "
            "updates the existing entry."
        ),
        responses={200: {"content": {"application/json": {"example": UPSERT_EXAMPLE}}}},
    )
    def upsert_entry(payload: EntryCreateRequest) -> EntryUpsertResponse:
        """Create or update today's entry for a user."""

        return mood_service.upsert_entry(payload)

    @app.get(
        "/entries",
        response_model=EntriesResponse,
        summary="List mood entries",
        description="Retrieve mood entries with optional filtering by user, mood, or date range.",
        responses={200: {"content": {"application/json": {"example": ENTRIES_EXAMPLE}}}},
    )
    def list_entries(
        user: str | None = Query(default=None, description="Filter by exact user name."),
        mood: Mood | None = Query(default=None, description="Filter by mood."),
        date_from: date | None = Query(
            default=None,
            description="Filter entries on or after this date.",
        ),
        date_to: date | None = Query(
            default=None,
            description="Filter entries on or before this date.",
        ),
        sort_by: SortBy = Query(
            default=SortBy.ENTRY_DATE,
            description="Column used for sorting.",
        ),
        sort_order: SortOrder = Query(
            default=SortOrder.DESC,
            description="Sort direction.",
        ),
    ) -> EntriesResponse:
        """Return entries that match the supplied filters."""

        return mood_service.list_entries(
            user=user,
            mood=mood,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    @app.get(
        "/entries/{entry_id}",
        response_model=EntryResponse,
        summary="Fetch one mood entry",
        description="Retrieve a single mood entry by its identifier.",
        responses={
            200: {"content": {"application/json": {"example": ENTRY_EXAMPLE}}},
            404: NOT_FOUND_RESPONSE,
        },
    )
    def get_entry(entry_id: int) -> EntryResponse:
        """Return a single entry."""

        entry = mood_service.get_entry(entry_id)
        if entry is None:
            raise _not_found()
        return entry

    @app.delete(
        "/entries/{entry_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete one mood entry",
        description="Delete a mood entry by its identifier.",
        responses={404: NOT_FOUND_RESPONSE},
    )
    def delete_entry(entry_id: int) -> Response:
        """Delete a single entry."""

        deleted = mood_service.delete_entry(entry_id)
        if not deleted:
            raise _not_found()
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @app.get(
        "/analytics/trends",
        response_model=TrendsResponse,
        summary="Get mood trends",
        description="Return the daily team-average mood trend or a per-user mood trend.",
        responses={200: {"content": {"application/json": {"example": TRENDS_EXAMPLE}}}},
    )
    def get_trends(
        user: str | None = Query(default=None, description="Optional user to scope the trend."),
        date_from: date | None = Query(
            default=None,
            description="Optional trend start date.",
        ),
        date_to: date | None = Query(default=None, description="Optional trend end date."),
    ) -> TrendsResponse:
        """Return team or per-user trend data."""

        return mood_service.get_trends(user=user, date_from=date_from, date_to=date_to)

    @app.get(
        "/analytics/distribution",
        response_model=DistributionResponse,
        summary="Get mood distribution",
        description="Return counts for each mood in the selected period.",
        responses={200: {"content": {"application/json": {"example": DISTRIBUTION_EXAMPLE}}}},
    )
    def get_distribution(
        date_from: date | None = Query(
            default=None,
            description="Optional distribution start date.",
        ),
        date_to: date | None = Query(
            default=None,
            description="Optional distribution end date.",
        ),
    ) -> DistributionResponse:
        """Return mood distribution data."""

        return mood_service.get_distribution(date_from=date_from, date_to=date_to)

    @app.get(
        "/analytics/summary",
        response_model=SummaryResponse,
        summary="Get aggregate summary",
        description=(
            "Return total entries, unique users, average score, and mood "
            "breakdown for the selected period."
        ),
        responses={200: {"content": {"application/json": {"example": SUMMARY_EXAMPLE}}}},
    )
    def get_summary(
        date_from: date | None = Query(default=None, description="Optional summary start date."),
        date_to: date | None = Query(default=None, description="Optional summary end date."),
    ) -> SummaryResponse:
        """Return summary analytics."""

        return mood_service.get_summary(date_from=date_from, date_to=date_to)

    @app.get(
        "/health",
        summary="Check API health",
        description="Return a lightweight status response for health checks.",
        responses={200: {"content": {"application/json": {"example": {"status": "ok"}}}}},
    )
    def health() -> dict[str, str]:
        """Return the health status."""

        return {"status": "ok"}

    return app


@lru_cache(maxsize=1)
def default_service() -> MoodService:
    """Build the default service instance used by the application."""

    settings = get_settings()
    database = Database(settings.database_url)
    repository = MoodEntryRepository(database=database)
    return MoodService(repository=repository)


def _not_found() -> HTTPException:
    """Return a standard not-found HTTP exception."""

    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found.")
