
from types import SimpleNamespace

import pytest

import app.llm.service as service


@pytest.fixture
def fake_settings():
    return SimpleNamespace(
        openai_model="qwen2.5:1.5b",
        anthropic_model="qwen2.5:1.5b",
        max_output_tokens=1000,
    )


@pytest.fixture
def fake_usage():
    return {
        "input_tokens": 10,
        "output_tokens": 20,
        "total_tokens": 30,
        "cost_usd": 0.0,
    }


def test_ask_openai_success(monkeypatch, fake_settings, fake_usage):
    monkeypatch.setattr(service, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(service, "validate_token_budget", lambda messages: 10)

    response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="REST API explanation")
            )
        ],
        usage=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=20,
        ),
        model="qwen2.5:1.5b",
    )

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: response
            )
        )
    )

    monkeypatch.setattr(service, "get_openai_client", lambda: client)
    monkeypatch.setattr(service, "log_usage", lambda **kwargs: fake_usage)

    result = service.ask_openai("Explain REST APIs.")

    assert result["answer"] == "REST API explanation"
    assert result["provider"] == "openai_sdk_ollama"
    assert result["model"] == "qwen2.5:1.5b"
    assert result["usage"] == fake_usage


def test_ask_claude_success(monkeypatch, fake_settings, fake_usage):
    monkeypatch.setattr(service, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(service, "validate_token_budget", lambda messages: 10)

    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="text", text="Hello "),
            SimpleNamespace(type="text", text="from the model"),
            SimpleNamespace(type="tool_use", text=""),
        ],
        usage=SimpleNamespace(
            input_tokens=10,
            output_tokens=20,
        ),
        model="qwen2.5:1.5b",
    )

    client = SimpleNamespace(
        messages=SimpleNamespace(
            create=lambda **kwargs: response
        )
    )

    monkeypatch.setattr(service, "get_anthropic_client", lambda: client)
    monkeypatch.setattr(service, "log_usage", lambda **kwargs: fake_usage)

    result = service.ask_claude(
        "Say hello.",
        "You are a helpful assistant.",
    )

    assert result["answer"] == "Hello from the model"
    assert result["provider"] == "anthropic_sdk_ollama"
    assert result["model"] == "qwen2.5:1.5b"
    assert result["usage"] == fake_usage


def test_stream_openai_returns_chunks_and_logs_usage(
    monkeypatch, fake_settings
):
    monkeypatch.setattr(service, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(service, "validate_token_budget", lambda messages: 10)

    chunks = [
        SimpleNamespace(
            model="qwen2.5:1.5b",
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="Hello ")
                )
            ],
            usage=None,
        ),
        SimpleNamespace(
            model="qwen2.5:1.5b",
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="world!")
                )
            ],
            usage=None,
        ),
        SimpleNamespace(
            model="qwen2.5:1.5b",
            choices=[],
            usage=SimpleNamespace(
                prompt_tokens=10,
                completion_tokens=5,
            ),
        ),
    ]

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: iter(chunks)
            )
        )
    )

    logged = []

    monkeypatch.setattr(service, "get_openai_client", lambda: client)
    monkeypatch.setattr(
        service,
        "log_usage",
        lambda **kwargs: logged.append(kwargs),
    )

    result = list(service.stream_openai("Say hello."))

    assert result == ["Hello ", "world!"]
    assert len(logged) == 1
    assert logged[0]["input_tokens"] == 10
    assert logged[0]["output_tokens"] == 5


def test_benchmark_openai(monkeypatch, fake_settings):
    monkeypatch.setattr(service, "get_settings", lambda: fake_settings)
    monkeypatch.setattr(service, "validate_token_budget", lambda messages: 10)

    normal_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="Normal answer")
            )
        ]
    )

    stream_chunks = [
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="Streamed ")
                )
            ]
        ),
        SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(content="answer")
                )
            ]
        ),
    ]

    def fake_create(**kwargs):
        if kwargs.get("stream"):
            return iter(stream_chunks)
        return normal_response

    client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=fake_create)
        )
    )

    monkeypatch.setattr(service, "get_openai_client", lambda: client)

    result = service.benchmark_openai("Explain REST APIs.")

    assert result["non_streaming_answer"] == "Normal answer"
    assert result["streamed_answer"] == "Streamed answer"
    assert isinstance(result["non_streaming_time_seconds"], float)
    assert isinstance(
        result["streaming_time_to_first_token_seconds"],
        float,
    )


def test_ask_openai_rejects_oversized_prompt(
    monkeypatch, fake_settings
):
    monkeypatch.setattr(service, "get_settings", lambda: fake_settings)

    def reject_prompt(messages):
        raise ValueError("Token budget exceeded")

    monkeypatch.setattr(service, "validate_token_budget", reject_prompt)

    with pytest.raises(ValueError, match="Token budget exceeded"):
        service.ask_openai("A very long prompt")
