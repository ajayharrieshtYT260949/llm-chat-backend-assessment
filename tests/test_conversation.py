
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

import app.memory.conversation as conversation_module
from app.memory.conversation import Conversation


def test_conversation_initializes_with_system_prompt():
    conversation = Conversation()

    assert conversation.messages[0]["role"] == "system"
    assert conversation.messages[0]["content"] == conversation.system_prompt
    assert conversation.summary == ""
    assert conversation.pinned_messages == []


def test_conversation_rejects_system_prompt_over_500_tokens(monkeypatch):
    monkeypatch.setattr(
        conversation_module,
        "count_tokens",
        lambda messages: 501,
    )

    with pytest.raises(ValueError, match="System prompt exceeds 500 tokens"):
        Conversation("An extremely long system prompt")


def test_add_and_retrieve_messages():
    conversation = Conversation()

    conversation.add_user_message("Hello")
    conversation.add_assistant_message("Hi there!")

    messages = conversation.get_messages()
    history = conversation.get_history_messages()

    assert len(messages) == 3
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


def test_get_messages_returns_copies():
    conversation = Conversation()
    conversation.add_user_message("Original message")

    messages = conversation.get_messages()
    messages[1]["content"] = "Changed externally"

    assert conversation.messages[1]["content"] == "Original message"


def test_get_token_count():
    conversation = Conversation()
    conversation.add_user_message("Hello")

    assert conversation.get_token_count() > 0


@pytest.mark.asyncio
async def test_manage_history_returns_when_within_budget(monkeypatch):
    conversation = Conversation()
    conversation.add_user_message("Hello")

    monkeypatch.setattr(
        conversation_module,
        "count_tokens",
        lambda messages: 10,
    )

    await conversation.manage_history()

    assert conversation.summary == ""
    assert len(conversation.messages) == 2


@pytest.mark.asyncio
async def test_summarize_messages_processes_multiple_chunks(monkeypatch):
    conversation = Conversation()

    monkeypatch.setattr(
        conversation_module,
        "get_settings",
        lambda: SimpleNamespace(openai_model="test-model"),
    )

    class FakeClient:
        def __init__(self):
            self.calls = []

            async def create(**kwargs):
                self.calls.append(kwargs)

                summary = (
                    "First summary"
                    if len(self.calls) == 1
                    else "Updated summary"
                )

                return SimpleNamespace(
                    choices=[
                        SimpleNamespace(
                            message=SimpleNamespace(content=summary)
                        )
                    ]
                )

            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=create)
            )

    client = FakeClient()

    messages = [
        {"role": "user", "content": f"Message {i}"}
        for i in range(10)
    ]

    result = await conversation.summarize_messages(
        messages,
        client=client,
    )

    assert result == "Updated summary"
    assert len(client.calls) == 2
    assert "First summary" in client.calls[1]["messages"][1]["content"]


@pytest.mark.asyncio
async def test_send_adds_user_and_assistant_messages(monkeypatch):
    conversation = Conversation()

    async def fake_tool_loop(messages, client=None):
        return {
            "messages": messages,
            "answer": "Hello from the assistant!",
        }

    monkeypatch.setattr(
        conversation,
        "manage_history",
        AsyncMock(),
    )

    monkeypatch.setattr(
        conversation_module,
        "run_tool_loop",
        fake_tool_loop,
    )

    result = await conversation.send("Hello")

    assert result["answer"] == "Hello from the assistant!"
    assert conversation.messages[-2]["content"] == "Hello"
    assert conversation.messages[-1]["content"] == "Hello from the assistant!"
