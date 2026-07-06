"""
Configuration settings for Kuleshov Lab backend
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # API Keys
    tmdb_api_key: str
    ai_api_key: str | None = None

    # AI models — must be set in .env (any litellm-compatible model string)
    # e.g. "claude-haiku-4-5-20251001", "gpt-4o-mini", "gemini/gemini-2.0-flash", "ollama/llama3"
    ai_model_fast: str | None = None
    ai_model_smart: str | None = None

    # Database
    database_url: str

    # Server
    host: str
    port: int
    environment: str

    # CORS
    frontend_url: str

    # Embeddings
    embedding_model: str


@lru_cache()
def get_settings() -> Settings:
    return Settings()

