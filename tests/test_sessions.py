
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import Settings
from app.dependencies import (
    get_app_settings,
    get_llm_client,
    get_session_store,
)
from app.sessions.store import SessionStore


class FakeLLMClient:
    """Mock asynchronous LLM client."""

    def __init__(self):
        self.calls = []

        async def create(**kwargs):
            self.calls.append(kwargs)

            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="Hello! How can I help you?",
                        )
                    )
                ]
            )

        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=create)
        )

    async def close(self):
        pass


@pytest.fixture
def client():
    store = SessionStore()
    llm_client = FakeLLMClient()

    app.dependency_overrides[get_app_settings] = (
        lambda: Settings(chat_api_key="test-secret")
    )

    app.dependency_overrides[get_session_store] = (
        lambda: store
    )

    async def override_llm():
        yield llm_client

    app.dependency_overrides[get_llm_client] = override_llm

    with TestClient(app) as test_client:
        yield test_client, store, llm_client

    app.dependency_overrides.clear()


@pytest.fixture
def headers():
    return {"x-api-key": "test-secret"}


def test_create_session(client, headers):
    test_client, store, _ = client

    response = test_client.post(
        "/sessions",
        headers=headers,
    )

    assert response.status_code == 201
    assert "session_id" in response.json()
    assert "created_at" in response.json()


def test_missing_api_key(client):
    test_client, _, _ = client

    response = test_client.post("/sessions")

    assert response.status_code == 401


def test_invalid_api_key(client):
    test_client, _, _ = client

    response = test_client.post(
        "/sessions",
        headers={"x-api-key": "wrong-secret"},
    )

    assert response.status_code == 403


def test_chat_success(client, headers):
    test_client, _, llm_client = client

    session = test_client.post(
        "/sessions",
        headers=headers,
    ).json()

    response = test_client.post(
        f"/sessions/{session['session_id']}/chat",
        headers=headers,
        json={"message": "Hello"},
    )

    assert response.status_code == 200
    assert response.json()["message"]["content"] == (
        "Hello! How can I help you?"
    )

    assert len(llm_client.calls) == 1


def test_chat_preserves_conversation_history(client, headers):
    test_client, _, llm_client = client

    session = test_client.post(
        "/sessions",
        headers=headers,
    ).json()

    session_id = session["session_id"]

    test_client.post(
        f"/sessions/{session_id}/chat",
        headers=headers,
        json={"message": "My name is Alex."},
    )

    test_client.post(
        f"/sessions/{session_id}/chat",
        headers=headers,
        json={"message": "What is my name?"},
    )

    messages = llm_client.calls[-1]["messages"]

    assert len(messages) == 3
    assert messages[0]["content"] == "My name is Alex."
    assert messages[1]["role"] == "assistant"
    assert messages[2]["content"] == "What is my name?"


def test_get_session_messages(client, headers):
    test_client, _, _ = client

    session = test_client.post(
        "/sessions",
        headers=headers,
    ).json()

    session_id = session["session_id"]

    test_client.post(
        f"/sessions/{session_id}/chat",
        headers=headers,
        json={"message": "Hello"},
    )

    response = test_client.get(
        f"/sessions/{session_id}/messages",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["total_messages"] == 2
    assert len(response.json()["messages"]) == 2


def test_chat_missing_session(client, headers):
    test_client, _, _ = client

    response = test_client.post(
        "/sessions/invalid-session/chat",
        headers=headers,
        json={"message": "Hello"},
    )

    assert response.status_code == 404


def test_get_missing_session_messages(client, headers):
    test_client, _, _ = client

    response = test_client.get(
        "/sessions/invalid-session/messages",
        headers=headers,
    )

    assert response.status_code == 404


def test_chat_rejects_empty_message(client, headers):
    test_client, _, _ = client

    session = test_client.post(
        "/sessions",
        headers=headers,
    ).json()

    response = test_client.post(
        f"/sessions/{session['session_id']}/chat",
        headers=headers,
        json={"message": "   "},
    )

    assert response.status_code == 422


def test_chat_rejects_oversized_message(client, headers):
    test_client, _, _ = client

    session = test_client.post(
        "/sessions",
        headers=headers,
    ).json()

    response = test_client.post(
        f"/sessions/{session['session_id']}/chat",
        headers=headers,
        json={"message": "A" * 2001},
    )

    assert response.status_code == 413


def test_health_remains_public(client):
    test_client, _, _ = client

    response = test_client.get("/health")

    assert response.status_code == 200


def test_chat_handles_llm_failure(client, headers):
    test_client, store, llm_client = client

    session = test_client.post(
        "/sessions",
        headers=headers,
    ).json()

    session_id = session["session_id"]

    async def failing_create(**kwargs):
        raise RuntimeError("LLM unavailable")

    llm_client.chat.completions.create = failing_create

    response = test_client.post(
        f"/sessions/{session_id}/chat",
        headers=headers,
        json={"message": "Hello"},
    )

    assert response.status_code == 502
    assert store.get_messages(session_id) == []
