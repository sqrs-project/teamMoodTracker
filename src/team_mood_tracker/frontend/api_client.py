"""HTTP client used by the Streamlit frontend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import httpx

from team_mood_tracker.shared.constants import DEFAULT_TIMEOUT_SECONDS, Mood
from team_mood_tracker.shared.models import (
    DistributionResponse,
    EntriesResponse,
    EntryCreateRequest,
    EntryResponse,
    EntryUpsertResponse,
    SummaryResponse,
    TrendsResponse,
)


class ApiClientError(RuntimeError):
    """Raised when the API returns an error response."""


@dataclass(frozen=True)
class MoodApiClient:
    """Thin client around the FastAPI backend."""

    base_url: str
    timeout: float = DEFAULT_TIMEOUT_SECONDS

    def save_entry(self, payload: EntryCreateRequest) -> EntryUpsertResponse:
        """Create or update today's entry."""

        return EntryUpsertResponse.model_validate(
            self._request("POST", "/entries", json=payload.model_dump())
        )

    def get_entry(self, entry_id: int) -> EntryResponse:
        """Fetch a single entry by identifier."""

        return EntryResponse.model_validate(self._request("GET", f"/entries/{entry_id}"))

    def list_entries(
        self,
        *,
        user: str | None = None,
        mood: Mood | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> EntriesResponse:
        """List entries with optional filters."""

        params = _clean_params(
            user=user,
            mood=mood.value if mood else None,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return EntriesResponse.model_validate(self._request("GET", "/entries", params=params))

    def get_today_entry(self, user: str, today: date) -> EntryResponse | None:
        """Return today's entry for a user if one exists."""

        response = self.list_entries(
            user=user.strip(),
            date_from=today,
            date_to=today,
            sort_by="updated_at",
            sort_order="desc",
        )
        if not response.items:
            return None
        return response.items[0]

    def get_trends(
        self,
        *,
        user: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> TrendsResponse:
        """Fetch analytics trend data."""

        params = _clean_params(
            user=user,
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )
        return TrendsResponse.model_validate(
            self._request("GET", "/analytics/trends", params=params)
        )

    def get_distribution(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DistributionResponse:
        """Fetch analytics distribution data."""

        params = _clean_params(
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )
        return DistributionResponse.model_validate(
            self._request("GET", "/analytics/distribution", params=params)
        )

    def get_summary(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> SummaryResponse:
        """Fetch analytics summary data."""

        params = _clean_params(
            date_from=date_from.isoformat() if date_from else None,
            date_to=date_to.isoformat() if date_to else None,
        )
        return SummaryResponse.model_validate(
            self._request("GET", "/analytics/summary", params=params)
        )

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Issue an HTTP request and return the JSON payload."""

        url = f"{self.base_url.rstrip('/')}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, json=json, params=params)
                response.raise_for_status()
        except httpx.HTTPStatusError as error:
            detail = _extract_error_detail(error.response)
            raise ApiClientError(detail) from error
        except httpx.HTTPError as error:
            raise ApiClientError("API is unavailable right now.") from error
        return response.json()


def _clean_params(**params: str | None) -> dict[str, str]:
    """Drop query parameters whose values are empty."""

    return {key: value for key, value in params.items() if value}


def _extract_error_detail(response: httpx.Response) -> str:
    """Extract the most useful detail from an error response."""

    payload = response.json()
    detail = payload.get("detail")
    if isinstance(detail, str):
        return detail
    return "The server returned an unexpected error."
