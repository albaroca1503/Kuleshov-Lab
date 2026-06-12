"""
Pydantic models for API requests and responses
"""
from pydantic import BaseModel, Field
from typing import Optional


class VibeRequest(BaseModel):
    """Request model for vibe-based recommendations"""
    vibe: str = Field(..., description="Vibe description (e.g., 'neon-drenched 80s thriller')")
    limit: int = Field(default=10, ge=1, le=50, description="Number of recommendations")
    filters: Optional[dict] = Field(default=None, description="Optional filters (genre, year, etc.)")


class MovieResponse(BaseModel):
    """Response model for a single movie"""
    id: int
    title: str
    original_title: Optional[str] = None
    overview: Optional[str] = None
    release_date: Optional[str] = None
    genres: list[str] = []
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    score: float = Field(..., description="Recommendation score (0-1)")
    reason: Optional[str] = Field(default=None, description="Why this movie was recommended")


class RecommendationResponse(BaseModel):
    """Response model for recommendations"""
    vibe: str
    movies: list[MovieResponse]
    total: int


class MarkWatchedRequest(BaseModel):
    """Request to mark a movie as watched"""
    status: str = Field(default="watched", pattern="^(watched|liked|disliked)$")
    rating: Optional[float] = Field(default=None, ge=0, le=10)
    movie_title: Optional[str] = None


class UserStatsResponse(BaseModel):
    """User statistics response"""
    total_watched: int
    total_liked: int
    total_disliked: int
    favorite_genres: list[tuple[str, int]]
    watch_time_hours: float


class UserSettingsRequest(BaseModel):
    country_code: str = "ES"
    streaming_service_ids: list[int] = []


class SignalResponse(BaseModel):
    """Response model for the Movie of the Day/Week signal"""
    movie: MovieResponse
    signal_reason: str = Field(..., description="Why this film is THE one to watch right now")
    context: str = Field(default="", description="Contextual framing (season, mood, moment)")

