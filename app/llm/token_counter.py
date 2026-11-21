
import tiktoken

from app.config import get_settings


def count_tokens(messages: list[dict]) -> int:
    """Estimate tokens used by a list of chat messages."""
    try:
        encoding = tiktoken.encoding_for_model(
            get_settings().openai_model
        )
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    total_tokens = 0

    for message in messages:
        total_tokens += 4

        for value in message.values():
            if isinstance(value, str):
                total_tokens += len(encoding.encode(value))

    return total_tokens + 2


def validate_token_budget(messages: list[dict]) -> int:
    """Return the estimated token count or reject an oversized prompt."""
    token_count = count_tokens(messages)
    budget = get_settings().token_budget

    if token_count > budget:
        raise ValueError(
            f"Token budget exceeded: {token_count} tokens "
            f"(maximum {budget})."
        )

    return token_count
