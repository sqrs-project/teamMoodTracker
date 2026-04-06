"""Configuration helper tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from team_mood_tracker.shared.config import sqlite_path_from_url


def test_sqlite_path_from_url_handles_relative_and_absolute_paths() -> None:
    """SQLite URL parsing should support both relative and absolute paths."""

    relative_path = sqlite_path_from_url("sqlite:///./team_mood_tracker.db")
    absolute_path = sqlite_path_from_url("sqlite:////tmp/team_mood_tracker.db")

    assert relative_path.name == "team_mood_tracker.db"
    assert absolute_path == Path("/tmp/team_mood_tracker.db")


def test_sqlite_path_from_url_rejects_non_sqlite_urls() -> None:
    """SQLite path parsing should reject unsupported schemes."""

    with pytest.raises(ValueError, match="sqlite"):
        sqlite_path_from_url("postgresql://localhost/example")
