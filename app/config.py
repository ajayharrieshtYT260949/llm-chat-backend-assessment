
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Ollama local server
    ollama_base_url: str = "http://localhost:11434"

    # Both SDKs use the same local model
    openai_model: str = "qwen2.5:1.5b"
    anthropic_model: str = "qwen2.5:1.5b"

    # Ollama accepts placeholder API keys
    openai_api_key: str = "ollama"
    anthropic_api_key: str = "ollama"

    # Application security
    chat_api_key: str = "replace-with-a-long-random-secret"

    # Token limits
    token_budget: int = 6000
    max_output_tokens: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
