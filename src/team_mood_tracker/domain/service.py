"""Application service that coordinates repository calls and analytics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from team_mood_tracker.domain.analytics import (
    build_distribution,
    build_summary,
    build_team_trends,
    build_user_trends,
)
from team_mood_tracker.shared.constants import Mood, SortBy, SortOrder
from team_mood_tracker.shared.entities import MoodEntryRecord
from team_mood_tracker.shared.models import (
    DistributionResponse,
    EntriesResponse,
    EntryCreateRequest,
    EntryResponse,
    EntryUpsertResponse,
    SummaryResponse,
    TrendsResponse,
)
from team_mood_tracker.shared.time import current_date, current_timestamp
from team_mood_tracker.storage.repository import MoodEntryRepository


@dataclass(frozen=True)
class MoodService:
    """Service layer for mood-tracker use cases."""

    repository: MoodEntryRepository

    def initialize(self) -> None:
        """Initialize storage dependencies."""

        self.repository.database.initialize()

    def upsert_entry(self, payload: EntryCreateRequest) -> EntryUpsertResponse:
        """Create or update today's entry for a user."""

        result = self.repository.upsert_entry(
            user=payload.user,
            mood=payload.mood,
            comment=payload.comment,
            entry_date=current_date(),
            timestamp=current_timestamp(),
        )
        return EntryUpsertResponse(action=result.action, entry=self._entry_response(result.entry))

    def get_entry(self, entry_id: int) -> EntryResponse | None:
        """Return one entry by identifier."""

        record = self.repository.get_entry(entry_id)
        if record is None:
            return None
        return self._entry_response(record)

    def delete_entry(self, entry_id: int) -> bool:
        """Delete one entry by identifier."""

        return self.repository.delete_entry(entry_id)

    def list_entries(
        self,
        *,
        user: str | None = None,
        mood: Mood | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: SortBy = SortBy.ENTRY_DATE,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> EntriesResponse:
        """Return entries that match the supplied filters."""

        records = self.repository.list_entries(
            user=user,
            mood=mood,
            date_from=date_from,
            date_to=date_to,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return EntriesResponse(
            total=len(records),
            items=[self._entry_response(record) for record in records],
        )

    def get_trends(
        self,
        *,
        user: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> TrendsResponse:
        """Return team or per-user trend data."""

        records = self._analytics_entries(user=user, date_from=date_from, date_to=date_to)
        if user:
            return build_user_trends(records, user)
        return build_team_trends(records)

    def get_distribution(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DistributionResponse:
        """Return mood distribution for the selected period."""

        records = self._analytics_entries(date_from=date_from, date_to=date_to)
        return DistributionResponse(items=build_distribution(records))

    def get_summary(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> SummaryResponse:
        """Return summary metrics for the selected period."""

        records = self._analytics_entries(date_from=date_from, date_to=date_to)
        return build_summary(records)

    def _analytics_entries(
        self,
        *,
        user: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[MoodEntryRecord]:
        """Fetch entries for analytics queries."""

        return self.repository.list_entries(
            user=user,
            date_from=date_from,
            date_to=date_to,
            sort_by=SortBy.ENTRY_DATE,
            sort_order=SortOrder.ASC,
        )

    def _entry_response(self, record: MoodEntryRecord) -> EntryResponse:
        """Convert a domain record into an API response model."""

        return EntryResponse(
            id=record.id,
            user=record.user,
            mood=record.mood,
            mood_emoji=record.mood.emoji,
            mood_label=record.mood.label,
            comment=record.comment,
            entry_date=record.entry_date,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
