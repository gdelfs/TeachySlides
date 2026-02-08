"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    llm_request_timeout_seconds: int = 60

    # Concurrency: max simultaneous slide generations (avoids API rate limits and OOM)
    max_concurrent_generations: int = 10

    # Optional response cache (identical requests return cached result)
    cache_enabled: bool = False
    cache_ttl_seconds: int = 300
    cache_max_size: int = 100


settings = Settings()
