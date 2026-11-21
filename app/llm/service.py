
import time

from anthropic import Anthropic
from openai import OpenAI

from app.config import get_settings
from app.llm.cost import calculate_cost
from app.llm.token_counter import validate_token_budget
from app.llm.usage_tracker import log_usage


def get_openai_client() -> OpenAI:
    settings = get_settings()

    return OpenAI(
        base_url=f"{settings.ollama_base_url}/v1/",
        api_key=settings.openai_api_key,
    )


def get_anthropic_client() -> Anthropic:
    settings = get_settings()

    return Anthropic(
        base_url=settings.ollama_base_url,
        api_key=settings.anthropic_api_key,
    )


def ask_openai(prompt: str) -> dict:
    settings = get_settings()

    messages = [{"role": "user", "content": prompt}]
    validate_token_budget(messages)

    client = get_openai_client()

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.max_output_tokens,
    )

    answer = response.choices[0].message.content or ""

    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens

    cost = calculate_cost(
        "ollama",
        input_tokens,
        output_tokens,
    )

    usage = log_usage(
        provider="openai_sdk_ollama",
        model=response.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
    )

    result = {
        "answer": answer,
        "provider": "openai_sdk_ollama",
        "model": response.model,
        "usage": usage,
    }

    print("\nOpenAI SDK answer:", answer)
    print("Model:", response.model)
    print("Usage:", usage)

    return result


def ask_claude(prompt: str, system: str) -> dict:
    settings = get_settings()

    messages = [{"role": "user", "content": prompt}]

    validate_token_budget(
        [{"role": "system", "content": system}] + messages
    )

    client = get_anthropic_client()

    response = client.messages.create(
        model=settings.anthropic_model,
        system=system,
        messages=messages,
        max_tokens=settings.max_output_tokens,
    )

    answer = "".join(
        block.text
        for block in response.content
        if block.type == "text"
    )

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens

    cost = calculate_cost(
        "ollama",
        input_tokens,
        output_tokens,
    )

    usage = log_usage(
        provider="anthropic_sdk_ollama",
        model=response.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost=cost,
    )

    result = {
        "answer": answer,
        "provider": "anthropic_sdk_ollama",
        "model": response.model,
        "usage": usage,
    }

    print("\nAnthropic SDK answer:", answer)
    print("Model:", response.model)
    print("Usage:", usage)

    return result


def stream_openai(prompt: str):
    """Stream text deltas and record usage after streaming completes."""

    settings = get_settings()

    messages = [{"role": "user", "content": prompt}]
    validate_token_budget(messages)

    client = get_openai_client()

    usage_data = None
    model_name = settings.openai_model

    stream = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.max_output_tokens,
        stream=True,
        stream_options={"include_usage": True},
    )

    for chunk in stream:
        if chunk.model:
            model_name = chunk.model

        if chunk.usage is not None:
            usage_data = chunk.usage

        if chunk.choices:
            content = chunk.choices[0].delta.content

            if content:
                yield content

    # Record actual usage reported by Ollama.
    if usage_data is not None:
        cost = calculate_cost(
            "ollama",
            usage_data.prompt_tokens,
            usage_data.completion_tokens,
        )

        log_usage(
            provider="openai_sdk_ollama",
            model=model_name,
            input_tokens=usage_data.prompt_tokens,
            output_tokens=usage_data.completion_tokens,
            cost=cost,
        )


def benchmark_openai(prompt: str) -> dict:
    """Compare non-streaming response time with streaming TTFT."""

    settings = get_settings()

    messages = [{"role": "user", "content": prompt}]
    validate_token_budget(messages)

    client = get_openai_client()

    # Non-streaming benchmark
    start = time.perf_counter()

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.max_output_tokens,
    )

    non_stream_time = time.perf_counter() - start

    # Streaming benchmark
    start = time.perf_counter()

    first_token_time = None
    streamed_text = ""

    stream = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.max_output_tokens,
        stream=True,
    )

    for chunk in stream:
        if chunk.choices:
            content = chunk.choices[0].delta.content

            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start

                streamed_text += content

    return {
        "non_streaming_time_seconds": round(
            non_stream_time, 3
        ),
        "streaming_time_to_first_token_seconds": (
            round(first_token_time, 3)
            if first_token_time is not None
            else None
        ),
        "non_streaming_answer": (
            response.choices[0].message.content or ""
        ),
        "streamed_answer": streamed_text,
    }
