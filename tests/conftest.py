"""Shared pytest fixtures for the project."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from team_mood_tracker.backend.app import create_app
from team_mood_tracker.domain.service import MoodService
from team_mood_tracker.shared.constants import Mood
from team_mood_tracker.storage.database import Database
from team_mood_tracker.storage.repository import MoodEntryRepository


@pytest.fixture()
def database_url(tmp_path: Path) -> str:
    """Return a temporary SQLite URL for tests."""

    return f"sqlite:///{tmp_path / 'test.db'}"


@pytest.fixture()
def service(database_url: str) -> MoodService:
    """Return an initialized service bound to a temporary database."""

    repository = MoodEntryRepository(database=Database(database_url))
    mood_service = MoodService(repository=repository)
    mood_service.initialize()
    return mood_service


@pytest.fixture()
def repository(database_url: str) -> MoodEntryRepository:
    """Return an initialized repository bound to a temporary database."""

    database = Database(database_url)
    database.initialize()
    return MoodEntryRepository(database=database)


@pytest.fixture()
def client(service: MoodService) -> TestClient:
    """Return a FastAPI test client backed by the temporary service."""

    app = create_app(service=service)
    return TestClient(app)


@pytest.fixture()
def seed_entries(service: MoodService) -> None:
    """Seed a few records for analytics-oriented tests."""

    repository = service.repository
    repository.upsert_entry(
        user="Alice",
        mood=Mood.HAPPY,
        comment="Great day",
        entry_date=datetime(2026, 4, 4).date(),
        timestamp=datetime(2026, 4, 4, 9, 0, 0),
    )
    repository.upsert_entry(
        user="Bob",
        mood=Mood.NEUTRAL,
        comment=None,
        entry_date=datetime(2026, 4, 4).date(),
        timestamp=datetime(2026, 4, 4, 10, 0, 0),
    )
    repository.upsert_entry(
        user="Alice",
        mood=Mood.STRESSED,
        comment="Busy day",
        entry_date=datetime(2026, 4, 5).date(),
        timestamp=datetime(2026, 4, 5, 9, 0, 0),
    )
