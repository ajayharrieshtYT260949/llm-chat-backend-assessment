
import asyncio
import time

from openai import AsyncOpenAI

from app.config import get_settings
from app.llm.cost import calculate_cost
from app.llm.retry import retry_llm_request
from app.llm.token_counter import validate_token_budget
from app.llm.usage_tracker import log_usage


def get_async_openai_client() -> AsyncOpenAI:
    """Create an asynchronous OpenAI-compatible Ollama client."""

    settings = get_settings()

    return AsyncOpenAI(
        base_url=f"{settings.ollama_base_url}/v1/",
        api_key=settings.openai_api_key,
    )


async def _ask_with_client(prompt: str, client: AsyncOpenAI) -> dict:
    """Send one asynchronous LLM request with retry support."""

    settings = get_settings()

    messages = [{"role": "user", "content": prompt}]
    validate_token_budget(messages)

    @retry_llm_request
    async def make_request():
        return await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
            max_tokens=settings.max_output_tokens,
        )

    response = await make_request()

    answer = response.choices[0].message.content or ""

    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    cost = calculate_cost(
        "ollama",
        input_tokens,
        output_tokens,
    )

    usage = log_usage(
        provider="openai_sdk_ollama_async",
        model=response.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
    )

    return {
        "answer": answer,
        "provider": "openai_sdk_ollama_async",
        "model": response.model,
        "usage": usage,
    }


async def _safe_ask(prompt: str, client: AsyncOpenAI) -> dict:
    """Isolate individual request failures."""

    try:
        result = await _ask_with_client(prompt, client)

        return {
            "prompt": prompt,
            "success": True,
            **result,
        }

    except Exception as error:
        return {
            "prompt": prompt,
            "success": False,
            "error": str(error),
        }


async def _execute_questions(
    prompts: list[str],
    client: AsyncOpenAI,
    concurrent: bool,
    max_concurrency: int = 3,
) -> list[dict]:
    """Execute questions sequentially or concurrently."""

    if not concurrent:
        results = []

        for prompt in prompts:
            result = await _safe_ask(prompt, client)
            results.append(result)

        return results

    if max_concurrency < 1:
        raise ValueError("max_concurrency must be at least 1")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def limited_request(prompt: str):
        async with semaphore:
            return await _safe_ask(prompt, client)

    return await asyncio.gather(
        *(limited_request(prompt) for prompt in prompts)
    )


def _build_report(
    results: list[dict],
    elapsed: float,
    execution_mode: str,
) -> dict:
    successful = sum(
        1 for result in results if result["success"]
    )

    return {
        "execution_mode": execution_mode,
        "total_questions": len(results),
        "successful_requests": successful,
        "failed_requests": len(results) - successful,
        "elapsed_seconds": round(elapsed, 3),
        "results": results,
    }


async def ask_questions_sequential(
    prompts: list[str],
    client: AsyncOpenAI | None = None,
) -> dict:
    """Execute questions one after another."""

    start = time.perf_counter()

    if client is None:
        async with get_async_openai_client() as owned_client:
            results = await _execute_questions(
                prompts,
                owned_client,
                concurrent=False,
            )
    else:
        results = await _execute_questions(
            prompts,
            client,
            concurrent=False,
        )

    elapsed = time.perf_counter() - start

    return _build_report(
        results,
        elapsed,
        "sequential",
    )


async def ask_questions_concurrent(
    prompts: list[str],
    client: AsyncOpenAI | None = None,
    max_concurrency: int = 3,
) -> dict:
    """Execute questions concurrently with a semaphore limit."""

    if max_concurrency < 1:
        raise ValueError("max_concurrency must be at least 1")

    start = time.perf_counter()

    if client is None:
        async with get_async_openai_client() as owned_client:
            results = await _execute_questions(
                prompts,
                owned_client,
                concurrent=True,
                max_concurrency=max_concurrency,
            )
    else:
        results = await _execute_questions(
            prompts,
            client,
            concurrent=True,
            max_concurrency=max_concurrency,
        )

    elapsed = time.perf_counter() - start

    return _build_report(
        results,
        elapsed,
        "concurrent",
    )


async def benchmark_async_execution(
    prompts: list[str],
    max_concurrency: int = 3,
) -> dict:
    """Compare sequential and concurrent execution."""

    sequential = await ask_questions_sequential(prompts)

    concurrent = await ask_questions_concurrent(
        prompts,
        max_concurrency=max_concurrency,
    )

    sequential_time = sequential["elapsed_seconds"]
    concurrent_time = concurrent["elapsed_seconds"]

    speedup = (
        round(sequential_time / concurrent_time, 2)
        if concurrent_time > 0
        else None
    )

    return {
        "sequential": sequential,
        "concurrent": concurrent,
        "speedup": speedup,
    }
