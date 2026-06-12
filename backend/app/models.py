"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field


class VibeRequest(BaseModel):
    vibe: str = Field(..., description="Vibe description (e.g., 'neon-drenched 80s thriller')")
    limit: int = Field(default=10, ge=1, le=50)
    filters: dict | None = None


class MovieResponse(BaseModel):
    id: int
    title: str
    original_title: str | None = None
    overview: str | None = None
    release_date: str | None = None
    genres: list[str] = []
    poster_url: str | None = None
    backdrop_url: str | None = None
    score: float
    reason: str | None = None


class RecommendationResponse(BaseModel):
    vibe: str
    movies: list[MovieResponse]
    total: int


class MarkWatchedRequest(BaseModel):
    status: str = Field(default="watched", pattern="^(watched|liked|disliked)$")
    rating: float | None = Field(default=None, ge=0, le=10)
    movie_title: str | None = None


class UserStatsResponse(BaseModel):
    total_watched: int
    total_liked: int
    total_disliked: int
    favorite_genres: list[tuple[str, int]]
    watch_time_hours: float


class UserSettingsRequest(BaseModel):
    country_code: str = "ES"
    streaming_service_ids: list[int] = []


class SignalResponse(BaseModel):
    movie: MovieResponse
    signal_reason: str
    context: str = ""

