"""Time utilities used by the application."""

from __future__ import annotations

from datetime import date, datetime


def current_date() -> date:
    """Return the current local date."""

    return date.today()


def current_timestamp() -> datetime:
    """Return the current local timestamp."""

    return datetime.now().replace(microsecond=0)
