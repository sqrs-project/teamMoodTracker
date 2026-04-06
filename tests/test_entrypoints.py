"""Entry point coverage tests."""

from __future__ import annotations

from team_mood_tracker.backend.main import app


def test_backend_main_exposes_the_fastapi_app() -> None:
    """The backend entrypoint should expose a FastAPI app instance."""

    assert app.title == "Team Mood Tracker API"
