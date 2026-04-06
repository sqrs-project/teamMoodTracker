# Team Mood Tracker: Implementation And Deployment

## 1. What Was Built

This repository contains a complete implementation of the Team Mood Tracker from `prompt.md`.

The application consists of:

- FastAPI backend
- Streamlit frontend
- SQLite storage
- Poetry-based dependency management
- Docker packaging for future deployment
- CI and release checks in GitHub Actions

The product lets a team member submit one mood per current day, re-submit to update the same day's record, browse historical data, and view team and per-user trends.

## 2. Business Rules

The implementation follows these domain rules:

- No authentication
- User identity is a plain `user` string
- The supported moods are fixed:
  - `happy` / `😊`
  - `neutral` / `😐`
  - `stressed` / `😫`
- Comment is optional
- Entries are created only for the current day
- One user can have only one entry per day
- Re-submitting the same day updates the existing row instead of creating a duplicate

For analytics, moods are mapped to numeric scores:

- `happy = 3`
- `neutral = 2`
- `stressed = 1`

## 3. Architecture

Repository structure:

- `src/team_mood_tracker/backend`
  - FastAPI app factory and HTTP routes
- `src/team_mood_tracker/domain`
  - service layer and pure analytics helpers
- `src/team_mood_tracker/storage`
  - SQLite schema and repository
- `src/team_mood_tracker/shared`
  - config, enums, entities, Pydantic models
- `src/team_mood_tracker/frontend`
  - Streamlit UI, API client, presentation helpers
- `tests`
  - API, service, repository, config, frontend and client tests

Runtime flow:

1. Streamlit submits a payload to FastAPI.
2. FastAPI validates the request with Pydantic models.
3. The service layer normalizes input and applies the "today only" rule.
4. The repository performs a create-or-update operation in SQLite.
5. Analytics endpoints aggregate stored entries into trends, summary metrics, and mood distribution.
6. Streamlit renders charts and tables from typed API responses.

## 4. API Surface

Implemented endpoints:

- `POST /entries`
  - create or update today's entry for a user
- `GET /entries`
  - list entries with optional filtering and sorting
- `GET /entries/{entry_id}`
  - fetch one entry
- `DELETE /entries/{entry_id}`
  - delete one entry
- `GET /analytics/trends`
  - team-average or per-user daily trend
- `GET /analytics/distribution`
  - mood distribution for a selected period
- `GET /analytics/summary`
  - aggregate counts and average score
- `GET /health`
  - health check for Docker and CI

OpenAPI requirements from the prompt are covered:

- every endpoint is visible in Swagger UI
- every endpoint has `summary`
- every endpoint has `description`
- every endpoint has at least one example response

## 5. Frontend Behavior

The Streamlit UI includes:

- a "today's mood" form
- a hint that re-submitting today updates the current record
- automatic prefill when a user already has an entry for today
- team-level summary metrics
- team trend chart
- mood distribution chart
- optional per-user trend selector
- recent entries table

There is no calendar and no historical manual entry creation, which matches the clarified scope in `prompt.md`.

## 6. Persistence

SQLite schema:

- table: `mood_entries`
- unique constraint: `(user, entry_date)`
- indexes:
  - `entry_date`
  - `user`

Stored fields:

- `id`
- `user`
- `mood`
- `comment`
- `entry_date`
- `created_at`
- `updated_at`

## 7. Local Run

With Poetry:

```bash
poetry install
cp .env.example .env
poetry run uvicorn team_mood_tracker.backend.main:app --reload --host 0.0.0.0 --port 8000
poetry run streamlit run src/team_mood_tracker/frontend/app.py
```

URLs:

- API docs: `http://localhost:8000/docs`
- UI: `http://localhost:8501`

## 8. Docker Run

This repository is dockerized for future deployment.

Local Compose:

```bash
docker compose up --build
```

Containers:

- `api`
- `ui`

Ports:

- `8000` for FastAPI
- `8501` for Streamlit

Persistent storage:

- named volume `mood-data`

Server-oriented Compose:

- `docker-compose.server.yml`
- designed to join an external Docker network called `backend_default`
- intended for environments where reverse proxying already exists outside this repository

## 9. Production Deployment That Was Performed

The target VPS already had an nginx container owned by another project. Because of that, the deployment was split into two parts:

### 9.1 Application Stack

This repository was deployed as an isolated Docker stack:

- `team-mood-api`
- `team-mood-ui`

The stack was attached to the shared Docker network:

- `backend_default`

That allowed the pre-existing nginx container to proxy requests to the new services without opening extra public ports for the app containers.

### 9.2 Reverse Proxy And TLS

The existing nginx lived in another repository on the server:

- remote path: `/home/user1/backend`

To expose `team-mood.duckdns.org`, the following production steps were applied there:

1. Add a virtual host for `team-mood.duckdns.org`.
2. Proxy `/` to `team-mood-ui:8501`.
3. Proxy `/api/` to `team-mood-api:8000`.
4. Generalize DuckDNS certbot hooks so they derive the subdomain from `CERTBOT_DOMAIN`.
5. Add `scripts/request_tls.sh` for one-command certificate issuance.
6. Request a Let's Encrypt certificate for `team-mood.duckdns.org`.
7. Recreate nginx so the bind-mounted config file is re-read.
8. Verify:
   - `http -> https` redirect
   - UI on HTTPS
   - `/api/health` on HTTPS

Production certificate result:

- domain: `team-mood.duckdns.org`
- issuer: Let's Encrypt
- expiration: `2026-07-05`

## 10. CI/CD Situation

This repository contains:

- CI workflow: [`.github/workflows/CI.yml`](/Users/vladkuznetsov/inno/teamMoodTracker/.github/workflows/CI.yml)
- release gate workflow: [`.github/workflows/release.yml`](/Users/vladkuznetsov/inno/teamMoodTracker/.github/workflows/release.yml)

Those workflows validate:

- formatting
- linting
- typing
- complexity
- maintainability index
- tests and coverage
- bandit
- pip-audit
- docstring coverage
- OpenAPI route/documentation coverage

Production CD currently lives in the separate infrastructure repository that owns the shared nginx stack. That repository has a `ci-cd.yml` workflow which deploys to the VPS on push to `main`. This is acceptable for the course prompt because CD was explicitly optional.

## 11. How Production Now Works

Request path:

1. Client opens `team-mood.duckdns.org`.
2. Shared nginx on the VPS terminates TLS.
3. nginx proxies `/` to `team-mood-ui`.
4. nginx proxies `/api/` to `team-mood-api`.
5. API uses SQLite data mounted on the server volume.

Operational dependency:

- The app stack depends on the external reverse proxy network `backend_default`.

## 12. Main Files To Know

- [README.md](/Users/vladkuznetsov/inno/teamMoodTracker/README.md)
- [pyproject.toml](/Users/vladkuznetsov/inno/teamMoodTracker/pyproject.toml)
- [docker-compose.yml](/Users/vladkuznetsov/inno/teamMoodTracker/docker-compose.yml)
- [docker-compose.server.yml](/Users/vladkuznetsov/inno/teamMoodTracker/docker-compose.server.yml)
- [backend/app.py](/Users/vladkuznetsov/inno/teamMoodTracker/src/team_mood_tracker/backend/app.py)
- [frontend/app.py](/Users/vladkuznetsov/inno/teamMoodTracker/src/team_mood_tracker/frontend/app.py)
- [repository.py](/Users/vladkuznetsov/inno/teamMoodTracker/src/team_mood_tracker/storage/repository.py)
- [CI.yml](/Users/vladkuznetsov/inno/teamMoodTracker/.github/workflows/CI.yml)
- [release.yml](/Users/vladkuznetsov/inno/teamMoodTracker/.github/workflows/release.yml)
