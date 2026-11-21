
import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.routes.chat as chat_route
import app.routes.usage as usage_route


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "LLM Chat Backend is running"


def test_usage_endpoint(client, monkeypatch):
    expected_usage = {
        "date": "2026-11-21",
        "requests": 2,
        "input_tokens": 20,
        "output_tokens": 30,
        "total_tokens": 50,
        "cost_usd": 0.0,
    }

    monkeypatch.setattr(
        usage_route,
        "get_daily_usage",
        lambda: expected_usage,
    )

    response = client.get("/usage")

    assert response.status_code == 200
    assert response.json() == expected_usage


def test_chat_stream_endpoint(client, monkeypatch):
    monkeypatch.setattr(
        chat_route,
        "validate_token_budget",
        lambda messages: 10,
    )

    monkeypatch.setattr(
        chat_route,
        "stream_openai",
        lambda prompt: iter(["Hello ", "world!"]),
    )

    response = client.post(
        "/chat/stream",
        json={"prompt": "Say hello."},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert 'data: {"delta": "Hello "}' in response.text
    assert 'data: {"delta": "world!"}' in response.text
    assert "data: [DONE]" in response.text


def test_chat_stream_rejects_empty_prompt(client):
    response = client.post(
        "/chat/stream",
        json={"prompt": ""},
    )

    assert response.status_code == 422


def test_chat_stream_rejects_missing_prompt(client):
    response = client.post(
        "/chat/stream",
        json={},
    )

    assert response.status_code == 422


def test_chat_stream_rejects_oversized_prompt(client, monkeypatch):
    def reject_prompt(messages):
        raise ValueError("Token budget exceeded")

    monkeypatch.setattr(
        chat_route,
        "validate_token_budget",
        reject_prompt,
    )

    response = client.post(
        "/chat/stream",
        json={"prompt": "A very long prompt"},
    )

    assert response.status_code == 413
    assert "Token budget exceeded" in response.json()["detail"]


def test_chat_stream_handles_llm_error(client, monkeypatch):
    monkeypatch.setattr(
        chat_route,
        "validate_token_budget",
        lambda messages: 10,
    )

    def failing_stream(prompt):
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(
        chat_route,
        "stream_openai",
        failing_stream,
    )

    response = client.post(
        "/chat/stream",
        json={"prompt": "Say hello."},
    )

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "LLM unavailable" in response.text
