"""Configuration helpers for the application."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Runtime settings loaded from environment variables."""

    database_url: str
    api_host: str
    api_port: int
    api_base_url: str
    streamlit_server_port: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///./team_mood_tracker.db"),
        api_host=os.getenv("API_HOST", "127.0.0.1"),
        api_port=int(os.getenv("API_PORT", "8000")),
        api_base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
        streamlit_server_port=int(os.getenv("STREAMLIT_SERVER_PORT", "8501")),
    )


def sqlite_path_from_url(database_url: str) -> Path:
    """Translate a SQLite URL into a filesystem path."""

    if not database_url.startswith("sqlite:///"):
        msg = "Only sqlite:/// URLs are supported."
        raise ValueError(msg)
    raw_path = database_url.removeprefix("sqlite:///")
    if raw_path.startswith("/"):
        return Path(raw_path)
    return Path.cwd() / raw_path
