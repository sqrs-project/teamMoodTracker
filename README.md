# Team Mood Tracker

**Team Mood Tracker** is a lightweight internal tool for agile teams to record one mood per user per day and review historical well-being trends. The stack is *FastAPI* + *Streamlit* + *SQLite*, with *Poetry* for dependency management.

## What It Does

- Saves one mood per user for the current day
- Updates the same-day entry when the user submits again
- Supports three fixed moods with emoji:
  - `happy` / `😊`
  - `neutral` / `😐`
  - `stressed` / `😫`
- Stores an optional comment
- Shows team trend, per-user trend, summary metrics, and mood distribution
- Exposes documented API endpoints in Swagger

## Main Docs

- Implementation and deployment notes:
  - [docs/IMPLEMENTATION_AND_DEPLOYMENT.md](/Users/vladkuznetsov/inno/teamMoodTracker/docs/IMPLEMENTATION_AND_DEPLOYMENT.md)
- Prompt compliance matrix:
  - [docs/PROMPT_COMPLIANCE.md](/Users/vladkuznetsov/inno/teamMoodTracker/docs/PROMPT_COMPLIANCE.md)

## Local Setup

```bash
poetry install
cp .env.example .env
```

Run the API:

```bash
poetry run uvicorn team_mood_tracker.backend.main:app --reload --host 0.0.0.0 --port 8000
```

Run the UI in a second terminal:

```bash
poetry run streamlit run src/team_mood_tracker/frontend/app.py
```

Open:

- API docs: `http://localhost:8000/docs`
- UI: `http://localhost:8501`

## Docker

Local Docker run:

```bash
docker compose up --build
```

Server-oriented Compose file:

- [docker-compose.server.yml](/Users/vladkuznetsov/inno/teamMoodTracker/docker-compose.server.yml)

It is intended for environments where the reverse proxy already exists outside this repository.

## Quality Gates

```bash
poetry run black --check src tests
poetry run ruff check src tests
poetry run mypy src
poetry run radon cc -a -s src
poetry run radon mi -s src
poetry run pytest
poetry run bandit -r src
poetry run pip-audit
poetry run interrogate -vv src
```

Performance script:

```bash
poetry run locust -f locustfile.py --host http://127.0.0.1:8000 --headless -u 10 -r 1 -t 1m
```

## CI

The repository includes:

- [CI workflow](/Users/vladkuznetsov/inno/teamMoodTracker/.github/workflows/CI.yml)
- [Release workflow](/Users/vladkuznetsov/inno/teamMoodTracker/.github/workflows/release.yml)

They validate formatting, linting, typing, coverage, security, docstrings, and OpenAPI documentation completeness.

The `main` branch is protected and requires the `ci` check to pass before merge.


