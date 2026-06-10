"""
Configuration settings for Kuleshov Lab backend
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    tmdb_api_key: str
    claude_api_key: str | None = None
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./data/movies.db"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"
    
    # CORS
    frontend_url: str = "http://localhost:3000"
    
    # Embeddings
    embedding_model: str = "all-mpnet-base-v2"  # Better semantic understanding (768 dim vs 384)
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Made with Bob
