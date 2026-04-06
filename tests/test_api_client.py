"""Tests for the frontend API client."""

from __future__ import annotations

from datetime import date

import httpx
import pytest

from team_mood_tracker.frontend.api_client import ApiClientError, MoodApiClient
from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.models import EntryCreateRequest


def test_api_client_returns_typed_models(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API client should convert JSON payloads into typed response models."""

    def fake_request(
        self: httpx.Client,
        method: str,
        url: str,
        json: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        request = httpx.Request(method, url, json=json, params=params)
        if url.endswith("/entries") and method == "POST":
            return httpx.Response(
                200,
                json={
                    "action": "created",
                    "entry": {
                        "id": 1,
                        "user": "Alice",
                        "mood": "happy",
                        "mood_emoji": "😊",
                        "mood_label": "Happy",
                        "comment": "Ready",
                        "entry_date": "2026-04-06",
                        "created_at": "2026-04-06T09:00:00",
                        "updated_at": "2026-04-06T09:00:00",
                    },
                },
                request=request,
            )
        return httpx.Response(
            200,
            json={
                "total": 1,
                "items": [
                    {
                        "id": 1,
                        "user": "Alice",
                        "mood": "happy",
                        "mood_emoji": "😊",
                        "mood_label": "Happy",
                        "comment": "Ready",
                        "entry_date": "2026-04-06",
                        "created_at": "2026-04-06T09:00:00",
                        "updated_at": "2026-04-06T09:00:00",
                    }
                ],
            },
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = MoodApiClient(base_url="http://localhost:8000")

    save_response = client.save_entry(
        EntryCreateRequest(
            user="Alice",
            mood=Mood.HAPPY,
            comment="Ready",
        )
    )
    today_entry = client.get_today_entry("Alice", today=date(2026, 4, 6))

    assert save_response.entry.id == 1
    assert today_entry is not None
    assert today_entry.entry_date == date(2026, 4, 6)


def test_api_client_surfaces_server_and_network_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API client should raise readable exceptions for failures."""

    def status_error(
        self: httpx.Client,
        method: str,
        url: str,
        json: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        request = httpx.Request(method, url, json=json, params=params)
        return httpx.Response(422, json={"detail": "Broken payload"}, request=request)

    monkeypatch.setattr(httpx.Client, "request", status_error)
    client = MoodApiClient(base_url="http://localhost:8000")

    with pytest.raises(ApiClientError, match="Broken payload"):
        client.save_entry(EntryCreateRequest(user="Alice", mood=Mood.HAPPY, comment=None))

    def network_error(
        self: httpx.Client,
        method: str,
        url: str,
        json: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        request = httpx.Request(method, url, json=json, params=params)
        raise httpx.ConnectError("network down", request=request)

    monkeypatch.setattr(httpx.Client, "request", network_error)

    with pytest.raises(ApiClientError, match="unavailable"):
        client.get_summary(date_from=date(2026, 4, 1), date_to=date(2026, 4, 6))


def test_api_client_builds_query_params(monkeypatch: pytest.MonkeyPatch) -> None:
    """The API client should pass date filters and sorting parameters through."""

    seen: dict[str, str] = {}

    def fake_request(
        self: httpx.Client,
        method: str,
        url: str,
        json: dict[str, object] | None = None,
        params: dict[str, str] | None = None,
    ) -> httpx.Response:
        request = httpx.Request(method, url, json=json, params=params)
        if params:
            seen.update(params)
        return httpx.Response(
            200,
            json={
                "scope": "team",
                "user": None,
                "points": [{"entry_date": "2026-04-06", "average_score": 2.0}],
            },
            request=request,
        )

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = MoodApiClient(base_url="http://localhost:8000")

    response = client.get_trends(
        user="Alice",
        date_from=date(2026, 4, 1),
        date_to=date(2026, 4, 6),
    )

    assert response.points[0].average_score == 2.0
    assert seen == {"user": "Alice", "date_from": "2026-04-01", "date_to": "2026-04-06"}
