"""ASGI entry point for the FastAPI application."""

from team_mood_tracker.backend.app import create_app

app = create_app()
