
import json
from datetime import datetime, timezone

from app.llm.cost import calculate_cost
from app.llm.token_counter import count_tokens
from app.llm.usage_tracker import get_daily_usage, log_usage


def test_count_tokens_returns_positive_count():
    messages = [
        {"role": "user", "content": "Explain Python functions."}
    ]

    assert count_tokens(messages) > 0


def test_calculate_ollama_cost():
    cost = calculate_cost("ollama", 1_000_000, 1_000_000)

    assert cost == 0.0


def test_calculate_unsupported_provider():
    import pytest

    with pytest.raises(ValueError):
        calculate_cost("openai", 1000, 500)

    with pytest.raises(ValueError):
        calculate_cost("anthropic", 1000, 500)


def test_usage_logging_and_daily_summary(tmp_path, monkeypatch):
    import app.llm.usage_tracker as tracker

    usage_file = tmp_path / "usage.jsonl"
    monkeypatch.setattr(tracker, "USAGE_FILE", usage_file)

    today = datetime.now(timezone.utc).date()

    record = log_usage(
        provider="openai",
        model="test-model",
        input_tokens=100,
        output_tokens=50,
        cost=0.000045,
    )

    assert record["total_tokens"] == 150

    summary = get_daily_usage(today)

    assert summary["requests"] == 1
    assert summary["input_tokens"] == 100
    assert summary["output_tokens"] == 50
    assert summary["total_tokens"] == 150
    assert summary["cost_usd"] == 0.000045

    saved_record = json.loads(usage_file.read_text(encoding="utf-8"))
    assert saved_record["provider"] == "openai"
