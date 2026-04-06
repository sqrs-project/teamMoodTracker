"""Locust performance scenarios for the Team Mood Tracker API."""

from __future__ import annotations

from datetime import date
from random import choice

from locust import HttpUser, between, task


class TeamMoodUser(HttpUser):
    """Locust user that exercises the core read and write endpoints."""

    wait_time = between(1, 2)

    @task(2)
    def upsert_entry(self) -> None:
        """Create or update today's mood for a synthetic user."""

        mood = choice(["happy", "neutral", "stressed"])
        self.client.post(
            "/entries",
            json={"user": f"user-{choice(range(10))}", "mood": mood, "comment": "Load test"},
        )

    @task(2)
    def list_entries(self) -> None:
        """Fetch the recent entry list."""

        today = date.today().isoformat()
        self.client.get("/entries", params={"date_from": today, "date_to": today})

    @task(1)
    def analytics(self) -> None:
        """Fetch analytics endpoints."""

        self.client.get("/analytics/summary")
        self.client.get("/analytics/trends")
        self.client.get("/analytics/distribution")

