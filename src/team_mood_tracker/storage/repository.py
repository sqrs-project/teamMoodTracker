"""SQLite repository for mood entries."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from sqlite3 import Row

from team_mood_tracker.shared.constants import Mood, SortBy, SortOrder
from team_mood_tracker.shared.entities import MoodEntryRecord, UpsertResult
from team_mood_tracker.storage.database import Database


@dataclass(frozen=True)
class MoodEntryRepository:
    """Repository that stores and retrieves mood entries."""

    database: Database

    MOOD_SORT_SQL = (
        "CASE mood "
        "WHEN 'stressed' THEN 1 "
        "WHEN 'neutral' THEN 2 "
        "WHEN 'happy' THEN 3 "
        "ELSE 99 END"
    )

    def upsert_entry(
        self,
        *,
        user: str,
        mood: Mood,
        comment: str | None,
        entry_date: date,
        timestamp: datetime,
    ) -> UpsertResult:
        """Insert or update a mood entry for a user and date."""

        action = "created"
        with self.database.connect() as connection:
            existing = connection.execute(
                "SELECT id FROM mood_entries WHERE user = ? AND entry_date = ?",
                (user, entry_date.isoformat()),
            ).fetchone()
            if existing is None:
                cursor = connection.execute(
                    """
                    INSERT INTO mood_entries (
                        user,
                        mood,
                        comment,
                        entry_date,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user,
                        mood.value,
                        comment,
                        entry_date.isoformat(),
                        timestamp.isoformat(),
                        timestamp.isoformat(),
                    ),
                )
                if cursor.lastrowid is None:
                    msg = "Failed to persist mood entry."
                    raise RuntimeError(msg)
                entry_id = int(cursor.lastrowid)
            else:
                action = "updated"
                entry_id = int(existing["id"])
                connection.execute(
                    """
                    UPDATE mood_entries
                    SET mood = ?, comment = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (mood.value, comment, timestamp.isoformat(), entry_id),
                )
            connection.commit()
            row = self._require_row(self._fetch_row_by_id(connection=connection, entry_id=entry_id))
        return UpsertResult(action=action, entry=self._row_to_record(row))

    def get_entry(self, entry_id: int) -> MoodEntryRecord | None:
        """Return a single entry by identifier."""

        with self.database.connect() as connection:
            row = self._fetch_row_by_id(connection=connection, entry_id=entry_id)
        if row is None:
            return None
        return self._row_to_record(row)

    def delete_entry(self, entry_id: int) -> bool:
        """Delete an entry by identifier."""

        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM mood_entries WHERE id = ?", (entry_id,))
            connection.commit()
        return cursor.rowcount > 0

    def list_entries(
        self,
        *,
        user: str | None = None,
        mood: Mood | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        sort_by: SortBy = SortBy.ENTRY_DATE,
        sort_order: SortOrder = SortOrder.DESC,
    ) -> list[MoodEntryRecord]:
        """Return entries filtered and sorted by the supplied criteria."""

        query = "SELECT * FROM mood_entries"
        clauses, params = self._build_filters(
            user=user,
            mood=mood,
            date_from=date_from,
            date_to=date_to,
        )
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        order_clause = self._order_clause(sort_by)
        query += f" ORDER BY {order_clause} {sort_order.value.upper()}, id DESC"
        with self.database.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _build_filters(
        self,
        *,
        user: str | None,
        mood: Mood | None,
        date_from: date | None,
        date_to: date | None,
    ) -> tuple[list[str], list[str]]:
        """Build SQL where clauses and parameter values."""

        clauses: list[str] = []
        params: list[str] = []
        if user:
            clauses.append("user = ?")
            params.append(user)
        if mood:
            clauses.append("mood = ?")
            params.append(mood.value)
        if date_from:
            clauses.append("entry_date >= ?")
            params.append(date_from.isoformat())
        if date_to:
            clauses.append("entry_date <= ?")
            params.append(date_to.isoformat())
        return clauses, params

    def _order_clause(self, sort_by: SortBy) -> str:
        """Return the SQL expression used for sorting."""

        if sort_by is SortBy.MOOD:
            return self.MOOD_SORT_SQL
        return sort_by.value

    def _fetch_row_by_id(self, *, connection: sqlite3.Connection, entry_id: int) -> Row | None:
        """Fetch a raw row by identifier using an existing connection."""

        row = connection.execute("SELECT * FROM mood_entries WHERE id = ?", (entry_id,)).fetchone()
        return row

    def _row_to_record(self, row: Row) -> MoodEntryRecord:
        """Convert a SQLite row into a domain record."""

        return MoodEntryRecord(
            id=int(row["id"]),
            user=str(row["user"]),
            mood=Mood(str(row["mood"])),
            comment=str(row["comment"]) if row["comment"] is not None else None,
            entry_date=date.fromisoformat(str(row["entry_date"])),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            updated_at=datetime.fromisoformat(str(row["updated_at"])),
        )

    def _require_row(self, row: Row | None) -> Row:
        """Ensure a row lookup returned data."""

        if row is None:
            msg = "Mood entry disappeared during persistence."
            raise RuntimeError(msg)
        return row
