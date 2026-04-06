"""Tests for frontend app submission behavior."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from team_mood_tracker.frontend import app as frontend_app
from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.shared.models import EntryCreateRequest, EntryResponse, EntryUpsertResponse


@dataclass
class _ClientStub:
    """Small client stub used to test submission flows."""

    response: EntryUpsertResponse | None = None
    called: bool = False

    def save_entry(self, payload: EntryCreateRequest) -> EntryUpsertResponse:
        """Record the call and return the prepared response."""

        self.called = True
        if self.response is None:
            raise AssertionError("Expected a prepared response for save_entry")
        return self.response


def test_save_entry_reports_validation_errors_without_calling_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Blank usernames should show an error instead of raising a traceback."""

    messages: list[str] = []
    client = _ClientStub()

    monkeypatch.setattr(frontend_app.st, "error", messages.append)
    monkeypatch.setattr(frontend_app.st, "success", lambda _: None)

    frontend_app._save_entry(client=client, user_name="   ", mood=Mood.HAPPY, comment="")

    assert client.called is False
    assert messages
    assert "User must not be empty" in messages[0]


def test_save_entry_reports_success_message(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid submissions should surface a user-friendly success message."""

    messages: list[str] = []
    client = _ClientStub(
        response=EntryUpsertResponse(
            action="created",
            entry=EntryResponse(
                id=1,
                user="Alice",
                mood=Mood.HAPPY,
                mood_emoji="😊",
                mood_label="Happy",
                comment=None,
                entry_date="2026-04-06",
                created_at="2026-04-06T09:00:00",
                updated_at="2026-04-06T09:00:00",
            ),
        )
    )

    monkeypatch.setattr(frontend_app.st, "error", lambda _: None)
    monkeypatch.setattr(frontend_app.st, "success", messages.append)

    frontend_app._save_entry(client=client, user_name="Alice", mood=Mood.HAPPY, comment="")

    assert client.called is True
    assert messages == ["Today's mood was saved: 😊 Happy"]
