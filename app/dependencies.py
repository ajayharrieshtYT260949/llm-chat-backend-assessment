
from collections.abc import AsyncGenerator

from openai import AsyncOpenAI

from app.config import get_settings
from app.llm.async_service import get_async_openai_client
from app.sessions.store import session_store, SessionStore


def get_app_settings():
    """Provide application settings."""
    return get_settings()


def get_session_store() -> SessionStore:
    """Provide the shared session store."""
    return session_store


async def get_llm_client() -> AsyncGenerator[AsyncOpenAI, None]:
    """Provide an asynchronous LLM client and close it after use."""
    client = get_async_openai_client()

    try:
        yield client
    finally:
        await client.close()
