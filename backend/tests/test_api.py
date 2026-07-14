import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.chat import sse
from app.core.config import Settings
from app.main import create_app


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(
        app_env="test",
        database_url="sqlite://" + (tmp_path / "test.db").as_posix(),
        generate_schemas=True,
        groq_api_key="",
    )
    return TestClient(create_app(settings))


def test_settings_normalize_railway_postgresql_url():
    settings = Settings(
        database_url="postgresql://assistant:secret@postgres:5432/assistant"
    )

    assert settings.database_url == (
        "postgres://assistant:secret@postgres:5432/assistant"
    )


def test_health_reports_configuration_state(tmp_path: Path):
    with make_client(tmp_path) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["configured"] is False
    assert response.json()["database"] == "connected"


def test_sse_serializes_database_values():
    message_id = UUID("a6eca963-b9c9-45d6-8bb4-39ad8c4336da")
    created_at = datetime(2026, 7, 14, 15, 0, tzinfo=timezone.utc)

    encoded = sse(
        "user",
        {"message": {"id": message_id, "created_at": created_at}},
    )
    payload = json.loads(encoded.split("data: ", 1)[1])

    assert encoded.startswith("event: user\n")
    assert payload["message"]["id"] == str(message_id)
    assert payload["message"]["created_at"] == "2026-07-14T15:00:00+00:00"


def test_conversation_lifecycle(tmp_path: Path):
    with make_client(tmp_path) as client:
        created = client.post(
            "/api/conversations",
            json={"title": "Architecture ideas"},
        )
        conversation_id = created.json()["id"]

        listed = client.get("/api/conversations")
        renamed = client.patch(
            "/api/conversations/" + conversation_id,
            json={"title": "System design"},
        )
        repository = client.app.state.repository
        first_message = client.portal.call(
            repository.add_message,
            conversation_id,
            "user",
            "Explain the architecture",
        )
        second_message = client.portal.call(
            repository.add_message,
            conversation_id,
            "assistant",
            "The application has a React frontend and FastAPI backend.",
        )
        fetched = client.get("/api/conversations/" + conversation_id)
        deleted = client.delete("/api/conversations/" + conversation_id)
        missing = client.get("/api/conversations/" + conversation_id)

    assert created.status_code == 201
    assert listed.json()[0]["id"] == conversation_id
    assert renamed.json()["title"] == "System design"
    assert first_message["position"] == 0
    assert second_message["position"] == 1
    assert [message["role"] for message in fetched.json()["messages"]] == [
        "user",
        "assistant",
    ]
    assert deleted.status_code == 204
    assert missing.status_code == 404
