"""
Configuration settings for Kuleshov Lab backend
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # API Keys
    tmdb_api_key: str
    claude_api_key: str | None = None

    # AI models (override to use a different provider/model)
    ai_model_fast: str = "claude-haiku-4-5-20251001"
    ai_model_smart: str = "claude-sonnet-4-6"

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/movies.db"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    # CORS
    frontend_url: str = "http://localhost:3000"

    # Embeddings
    embedding_model: str = "all-mpnet-base-v2"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

