"""
TMDB API client for fetching movie data
"""
import requests
from typing import Optional
from app.config import get_settings

settings = get_settings()

BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p"


class TMDBClient:
    """Client for TMDB API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
    
    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """Make GET request to TMDB API"""
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        url = f"{BASE_URL}{endpoint}"
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_movie(self, movie_id: int) -> dict:
        """Get movie details by ID"""
        return self._get(f"/movie/{movie_id}")
    
    def search_movies(self, query: str, page: int = 1) -> dict:
        """Search movies by query"""
        return self._get("/search/movie", {"query": query, "page": page})
    
    def discover_movies(self, **kwargs) -> dict:
        """
        Discover movies with filters
        
        Args:
            with_genres: Genre IDs (comma-separated)
            primary_release_year: Year
            sort_by: Sort order (e.g., 'popularity.desc')
            page: Page number
        """
        return self._get("/discover/movie", kwargs)
    
    def get_trending(self, time_window: str = "week", page: int = 1) -> dict:
        """Get trending movies"""
        return self._get(f"/trending/movie/{time_window}", {"page": page})
    
    def get_popular(self, page: int = 1) -> dict:
        """Get popular movies"""
        return self._get("/movie/popular", {"page": page})
    
    def get_top_rated(self, page: int = 1) -> dict:
        """Get top rated movies"""
        return self._get("/movie/top_rated", {"page": page})
    
    @staticmethod
    def get_poster_url(poster_path: Optional[str], size: str = "w500") -> Optional[str]:
        """Get full poster URL"""
        if not poster_path:
            return None
        return f"{IMAGE_BASE_URL}/{size}{poster_path}"
    
    @staticmethod
    def get_backdrop_url(backdrop_path: Optional[str], size: str = "w1280") -> Optional[str]:
        """Get full backdrop URL"""
        if not backdrop_path:
            return None
        return f"{IMAGE_BASE_URL}/{size}{backdrop_path}"


# Global client instance
_client: Optional[TMDBClient] = None


def get_tmdb_client() -> TMDBClient:
    """Get or create TMDB client instance"""
    global _client
    if _client is None:
        _client = TMDBClient(settings.tmdb_api_key)
    return _client

# Made with Bob
