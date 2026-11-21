
import asyncio
from types import SimpleNamespace

import pytest

from app.llm.async_service import (
    ask_questions_concurrent,
    ask_questions_sequential,
)


class FakeAsyncCompletions:
    """Mock asynchronous LLM completion endpoint."""

    def __init__(self):
        self.active_requests = 0
        self.max_active_requests = 0
        self.total_requests = 0

    async def create(self, **kwargs):
        prompt = kwargs["messages"][0]["content"]

        self.active_requests += 1
        self.total_requests += 1

        self.max_active_requests = max(
            self.max_active_requests,
            self.active_requests,
        )

        try:
            # Simulate a small network delay.
            await asyncio.sleep(0.01)

            if "FAIL" in prompt:
                raise RuntimeError("Simulated LLM failure")

            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=f"Response to: {prompt}"
                        )
                    )
                ],
                usage=SimpleNamespace(
                    prompt_tokens=10,
                    completion_tokens=20,
                ),
                model="fake-model",
            )

        finally:
            self.active_requests -= 1


class FakeAsyncClient:
    """Provide the same client structure used by AsyncOpenAI."""

    def __init__(self):
        self.completions = FakeAsyncCompletions()
        self.chat = SimpleNamespace(
            completions=self.completions
        )


@pytest.mark.asyncio
async def test_sequential_execution():
    client = FakeAsyncClient()

    prompts = [
        f"Question {number}"
        for number in range(1, 11)
    ]

    result = await ask_questions_sequential(
        prompts,
        client=client,
    )

    assert result["execution_mode"] == "sequential"
    assert result["total_questions"] == 10
    assert result["successful_requests"] == 10
    assert result["failed_requests"] == 0

    # Sequential execution should never overlap requests.
    assert client.completions.max_active_requests == 1


@pytest.mark.asyncio
async def test_concurrent_execution_respects_semaphore_limit():
    client = FakeAsyncClient()

    prompts = [
        f"Question {number}"
        for number in range(1, 11)
    ]

    result = await ask_questions_concurrent(
        prompts,
        client=client,
        max_concurrency=3,
    )

    assert result["execution_mode"] == "concurrent"
    assert result["total_questions"] == 10
    assert result["successful_requests"] == 10
    assert result["failed_requests"] == 0

    # Never allow more than three simultaneous requests.
    assert client.completions.max_active_requests <= 3

    # Confirm that requests actually overlapped.
    assert client.completions.max_active_requests > 1


@pytest.mark.asyncio
async def test_concurrent_execution_isolates_failures():
    client = FakeAsyncClient()

    prompts = [
        "Question 1",
        "FAIL question",
        "Question 3",
    ]

    result = await ask_questions_concurrent(
        prompts,
        client=client,
        max_concurrency=3,
    )

    assert result["total_questions"] == 3
    assert result["successful_requests"] == 2
    assert result["failed_requests"] == 1

    failed_results = [
        item
        for item in result["results"]
        if not item["success"]
    ]

    assert len(failed_results) == 1
    assert "Simulated LLM failure" in failed_results[0]["error"]


@pytest.mark.asyncio
async def test_sequential_execution_isolates_failures():
    client = FakeAsyncClient()

    prompts = [
        "Question 1",
        "FAIL question",
        "Question 3",
    ]

    result = await ask_questions_sequential(
        prompts,
        client=client,
    )

    assert result["total_questions"] == 3
    assert result["successful_requests"] == 2
    assert result["failed_requests"] == 1


@pytest.mark.asyncio
async def test_concurrent_execution_rejects_invalid_limit():
    client = FakeAsyncClient()

    with pytest.raises(ValueError):
        await ask_questions_concurrent(
            ["Question 1"],
            client=client,
            max_concurrency=0,
        )


@pytest.mark.asyncio
async def test_empty_prompt_list():
    client = FakeAsyncClient()

    result = await ask_questions_concurrent(
        [],
        client=client,
    )

    assert result["total_questions"] == 0
    assert result["successful_requests"] == 0
    assert result["failed_requests"] == 0
