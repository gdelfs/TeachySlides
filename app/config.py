"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    llm_provider: str = "openai"
    openai_api_key: str | None = None
    google_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    google_model: str = "gemini-1.5-flash"


settings = Settings()
