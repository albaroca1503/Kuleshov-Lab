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
    
    def get_movie(self, movie_id: int, append_to_response: Optional[str] = None) -> dict:
        """
        Get movie details by ID
        
        Args:
            movie_id: TMDB movie ID
            append_to_response: Comma-separated list of additional data to fetch
                               (e.g., 'credits,keywords')
        """
        params = {}
        if append_to_response:
            params['append_to_response'] = append_to_response
        return self._get(f"/movie/{movie_id}", params)
    
    def get_movie_with_details(self, movie_id: int) -> dict:
        """Get movie with credits and keywords included"""
        return self.get_movie(movie_id, append_to_response='credits,keywords')
    
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
    
    def get_movie_rich_details(self, movie_id: int, country_code: str = "ES") -> dict:
        """
        Fetch comprehensive movie data in a single TMDB request:
        credits, watch providers, reviews, external IDs, videos.
        """
        data = self.get_movie(
            movie_id,
            append_to_response="credits,watch/providers,reviews,external_ids,videos"
        )

        # Director
        director = None
        crew = data.get("credits", {}).get("crew", [])
        for member in crew:
            if member.get("job") == "Director":
                director = member.get("name")
                break

        # Top cast (first 5)
        cast = [
            m.get("name") for m in data.get("credits", {}).get("cast", [])[:5]
        ]

        # IMDb ID
        imdb_id = data.get("external_ids", {}).get("imdb_id")

        # Streaming providers for the requested country
        providers_raw = data.get("watch/providers", {}).get("results", {}).get(country_code, {})
        streaming: dict[str, list[dict]] = {}
        for category in ("flatrate", "rent", "buy"):
            items = providers_raw.get(category, [])
            streaming[category] = [
                {
                    "id": p.get("provider_id"),
                    "name": p.get("provider_name"),
                    "logo_url": self.get_poster_url(p.get("logo_path"), size="w92"),
                }
                for p in items
            ]

        # Reviews (first 3, trimmed)
        reviews = []
        for r in data.get("reviews", {}).get("results", [])[:3]:
            content = r.get("content", "")
            reviews.append({
                "author": r.get("author", ""),
                "content": content[:400] + ("…" if len(content) > 400 else ""),
                "url": r.get("url", ""),
            })

        # YouTube trailer
        trailer_key = None
        for v in data.get("videos", {}).get("results", []):
            if v.get("site") == "YouTube" and v.get("type") == "Trailer":
                trailer_key = v.get("key")
                break

        return {
            "id": movie_id,
            "title": data.get("title", ""),
            "tagline": data.get("tagline", ""),
            "runtime": data.get("runtime"),
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "director": director,
            "cast": cast,
            "imdb_id": imdb_id,
            "streaming": streaming,
            "reviews": reviews,
            "trailer_key": trailer_key,
        }

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
