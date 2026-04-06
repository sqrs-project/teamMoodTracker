"""SQLite database helpers."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from team_mood_tracker.shared.config import sqlite_path_from_url

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS mood_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    mood TEXT NOT NULL,
    comment TEXT,
    entry_date TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(user, entry_date)
);

CREATE INDEX IF NOT EXISTS idx_mood_entries_entry_date
ON mood_entries(entry_date);

CREATE INDEX IF NOT EXISTS idx_mood_entries_user
ON mood_entries(user);
"""


@dataclass(frozen=True)
class Database:
    """Factory used to create SQLite connections."""

    database_url: str

    def initialize(self) -> None:
        """Create the SQLite schema if it does not already exist."""

        path = sqlite_path_from_url(self.database_url)
        self._ensure_parent_dir(path)
        with self.connect() as connection:
            connection.executescript(SCHEMA_SQL)

    def connect(self) -> sqlite3.Connection:
        """Create a new configured SQLite connection."""

        path = sqlite_path_from_url(self.database_url)
        connection = sqlite3.connect(path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA foreign_keys=ON;")
        return connection

    def _ensure_parent_dir(self, path: Path) -> None:
        """Create the parent directory for the SQLite file when needed."""

        path.parent.mkdir(parents=True, exist_ok=True)
