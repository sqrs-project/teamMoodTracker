"""API integration tests."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient

from team_mood_tracker.shared.constants import MAX_COMMENT_LENGTH


def test_entry_crud_flow(client: TestClient) -> None:
    """The API should support create, list, fetch, and delete flows."""

    create_response = client.post(
        "/entries",
        json={"user": "Alice", "mood": "happy", "comment": "Great retrospective"},
    )
    entry_id = create_response.json()["entry"]["id"]
    list_response = client.get("/entries")
    fetch_response = client.get(f"/entries/{entry_id}")
    delete_response = client.delete(f"/entries/{entry_id}")
    missing_response = client.get(f"/entries/{entry_id}")

    assert create_response.status_code == 200
    assert create_response.json()["action"] == "created"
    assert list_response.json()["total"] == 1
    assert fetch_response.status_code == 200
    assert delete_response.status_code == 204
    assert missing_response.status_code == 404


def test_analytics_endpoints_return_expected_shapes(client: TestClient) -> None:
    """Analytics endpoints should return documented top-level structures."""

    client.post("/entries", json={"user": "Alice", "mood": "happy", "comment": None})
    client.post("/entries", json={"user": "Bob", "mood": "neutral", "comment": None})

    trends_response = client.get("/analytics/trends")
    distribution_response = client.get("/analytics/distribution")
    summary_response = client.get("/analytics/summary")

    assert trends_response.status_code == 200
    assert distribution_response.json()["items"][0]["mood"] == "happy"
    assert summary_response.json()["total_entries"] == 2


def test_openapi_docs_include_descriptions_and_examples(client: TestClient) -> None:
    """The generated OpenAPI schema should expose summaries, descriptions, and examples."""

    schema = client.get("/openapi.json").json()
    post_entry = schema["paths"]["/entries"]["post"]
    summary_operation = schema["paths"]["/analytics/summary"]["get"]

    assert post_entry["summary"] == "Create or update today's mood entry"
    assert post_entry["description"]
    assert (
        post_entry["responses"]["200"]["content"]["application/json"]["example"]["action"]
        == "created"
    )
    assert summary_operation["description"]


def test_entries_endpoint_applies_query_filters(client: TestClient) -> None:
    """The entries list should honor user and date filters."""

    client.post("/entries", json={"user": "Alice", "mood": "happy", "comment": None})
    filtered_response = client.get(
        "/entries",
        params={
            "user": "Alice",
            "date_from": date.today().isoformat(),
            "date_to": date.today().isoformat(),
        },
    )

    assert filtered_response.status_code == 200
    assert filtered_response.json()["total"] == 1


def test_create_entry_rejects_invalid_payloads(client: TestClient) -> None:
    """The API should validate required fields and enum values."""

    blank_user_response = client.post(
        "/entries",
        json={"user": "   ", "mood": "happy", "comment": None},
    )
    invalid_mood_response = client.post(
        "/entries",
        json={"user": "Alice", "mood": "excited", "comment": None},
    )
    long_comment_response = client.post(
        "/entries",
        json={
            "user": "Alice",
            "mood": "happy",
            "comment": "x" * (MAX_COMMENT_LENGTH + 1),
        },
    )

    assert blank_user_response.status_code == 422
    assert any(item["loc"][-1] == "user" for item in blank_user_response.json()["detail"])
    assert invalid_mood_response.status_code == 422
    assert any(item["loc"][-1] == "mood" for item in invalid_mood_response.json()["detail"])
    assert long_comment_response.status_code == 422
    assert any(item["loc"][-1] == "comment" for item in long_comment_response.json()["detail"])
