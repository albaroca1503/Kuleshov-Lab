"""
Recommendation engine - Core logic for vibe-based movie recommendations
Uses TMDB as the source of truth, only caches embeddings locally
FASE 3: Integrates Claude for intelligent re-ranking
"""
import json
import numpy as np
from typing import Optional
import aiosqlite

from app.embeddings import get_embedding_service
from app.tmdb import get_tmdb_client
from app.claude import get_claude_service
from app.database import (
    get_watched_movies,
    get_user_stats,
    get_all_cached_movies,
    get_cache_stats
)
from app.models import MovieResponse


class RecommendationEngine:
    """Engine for generating movie recommendations"""
    
    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.tmdb_client = get_tmdb_client()
        self.claude_service = get_claude_service()
        self.embedding_cache = {}  # In-memory cache for embeddings
    
    async def recommend_by_vibe(
        self,
        db: aiosqlite.Connection,
        vibe: str,
        user_id: int = 1,
        limit: int = 10,
        filters: Optional[dict] = None
    ) -> list[MovieResponse]:
        """
        Generate recommendations based on vibe description
        
        Strategy:
        1. Fetch movies from TMDB (always fresh data)
        2. Generate/retrieve embeddings (cached)
        3. Calculate similarity with vibe
        4. Exclude watched movies
        5. Return top matches
        
        Args:
            db: Database connection (only for user data)
            vibe: Vibe description (e.g., "neon-drenched 80s thriller")
            user_id: User ID
            limit: Number of recommendations
            filters: Optional filters (genre, year, etc.)
            
        Returns:
            List of recommended movies with scores
        """
        print(f"🎬 Generating recommendations for vibe: '{vibe}'")
        
        # 1. Get vibe embedding
        vibe_embedding = self.embedding_service.encode(vibe)
        print(f"✅ Vibe embedding generated")
        
        # 2. Get watched movies to exclude
        watched_ids = await get_watched_movies(db, user_id)
        print(f"📋 Excluding {len(watched_ids)} watched movies")
        
        # 3. Fetch candidate movies from TMDB
        print(f"📥 Fetching movies from TMDB...")
        candidate_movies = await self._fetch_tmdb_candidates(filters)
        print(f"🎥 Found {len(candidate_movies)} candidate movies from TMDB")
        
        # 4. Calculate similarity scores
        scored_movies = []
        for movie_data in candidate_movies:
            # Skip watched movies
            if movie_data['id'] in watched_ids:
                continue
            
            # Get or generate movie embedding
            movie_embedding = self._get_movie_embedding(movie_data)
            
            # Calculate similarity
            similarity = self.embedding_service.cosine_similarity(vibe_embedding, movie_embedding)
            scored_movies.append((movie_data, similarity))
        
        print(f"🎯 Scored {len(scored_movies)} candidate movies")
        
        # 5. Sort by score and take top 50 for Claude
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        top_candidates = scored_movies[:min(50, len(scored_movies))]
        
        # 6. Convert to dict format for Claude
        candidate_dicts = []
        for movie, score in top_candidates:
            movie_dict = movie.copy()
            movie_dict['score'] = score
            candidate_dicts.append(movie_dict)
        
        # 7. Use Claude to re-rank and explain (FASE 3)
        if self.claude_service.is_available():
            print("🤖 Using Claude for intelligent re-ranking...")
            
            # Get user profile for context
            user_profile = await get_user_stats(db, user_id)
            
            # Claude re-ranks and adds explanations
            reranked = await self.claude_service.rerank_and_explain(
                vibe=vibe,
                candidates=candidate_dicts,
                user_profile=user_profile,
                limit=limit
            )
            
            # Convert to response format
            recommendations = []
            for movie in reranked:
                recommendations.append(self._movie_to_response(movie, movie.get('score', 0)))
        else:
            print("⚠️  Claude not available, using embedding scores only")
            # Fallback: use embedding scores
            recommendations = []
            for movie, score in top_candidates[:limit]:
                recommendations.append(self._movie_to_response(movie, score))
        
        print(f"✨ Returning {len(recommendations)} recommendations")
        return recommendations
    
    async def _fetch_tmdb_candidates(self, filters: Optional[dict] = None, num_pages: int = 5) -> list[dict]:
        """
        Fetch candidate movies from TMDB based on filters
        
        Strategy: Cast a WIDE net - fetch from multiple sources and time periods
        
        Args:
            filters: Optional filters (genre, year, etc.)
            num_pages: Number of pages to fetch per source (default 5 = ~100 movies per source)
            
        Returns:
            List of movie data from TMDB with full details
        """
        movies = []
        seen_ids = set()
        
        # Base discover parameters - MINIMAL filtering for maximum diversity
        base_params = {
            'include_adult': False,
            'vote_count.gte': 100,  # Back to 100 as requested
        }
        
        # Apply user filters if provided
        if filters:
            if 'genres' in filters and filters['genres']:
                base_params['with_genres'] = ','.join(map(str, filters['genres']))
            
            if 'year' in filters and filters['year']:
                base_params['primary_release_year'] = filters['year']
            
            if 'year_min' in filters and filters['year_min']:
                base_params['primary_release_date.gte'] = f"{filters['year_min']}-01-01"
            
            if 'year_max' in filters and filters['year_max']:
                base_params['primary_release_date.lte'] = f"{filters['year_max']}-12-31"
            
            if 'max_runtime' in filters and filters['max_runtime']:
                base_params['with_runtime.lte'] = filters['max_runtime']
        
        # Fetch from MANY different sources for maximum diversity
        sources = [
            ('vote_average.desc', num_pages // 4),   # Top rated
            ('popularity.desc', num_pages // 4),      # Popular
            ('primary_release_date.desc', num_pages // 4),  # Recent
            ('revenue.desc', num_pages // 4),         # Box office hits
        ]
        
        for sort_by, pages in sources:
            discover_params = base_params.copy()
            discover_params['sort_by'] = sort_by
            
            print(f"🔍 Fetching {pages} pages sorted by {sort_by}...")
            
            for page in range(1, pages + 1):
                try:
                    discover_params['page'] = page
                    response = self.tmdb_client.discover_movies(**discover_params)
                    page_movies = response.get('results', [])
                    
                    # Get full details for each movie (includes genres)
                    for movie_basic in page_movies:
                        movie_id = movie_basic['id']
                        
                        # Skip duplicates
                        if movie_id in seen_ids:
                            continue
                        seen_ids.add(movie_id)
                        
                        try:
                            # Fetch full movie details (includes genres, runtime, etc.)
                            full_movie = self.tmdb_client.get_movie(movie_id)
                            movies.append(full_movie)
                        except Exception as e:
                            print(f"⚠️  Error fetching movie {movie_id}: {e}")
                            continue
                    
                except Exception as e:
                    print(f"⚠️  Error fetching page {page} with sort {sort_by}: {e}")
                    continue
        
        print(f"📚 Fetched {len(movies)} unique movies from TMDB")
        return movies
    
    def _get_movie_embedding(self, movie_data: dict) -> np.ndarray:
        """
        Get or generate embedding for a movie (with caching)
        
        Args:
            movie_data: Movie data from TMDB
            
        Returns:
            Movie embedding vector
        """
        movie_id = movie_data['id']
        
        # Check cache
        if movie_id in self.embedding_cache:
            return self.embedding_cache[movie_id]
        
        # Generate new embedding
        embedding = self.embedding_service.generate_movie_embedding(movie_data)
        
        # Cache it
        self.embedding_cache[movie_id] = embedding
        
        return embedding
    
    def _matches_filters(self, movie: dict, filters: dict) -> bool:
        """
        Check if movie matches provided filters
        
        Args:
            movie: Movie data
            filters: Filter criteria
            
        Returns:
            True if movie matches all filters
        """
        # Genre filter
        if 'genres' in filters and filters['genres']:
            movie_genres = json.loads(movie.get('genres', '[]'))
            if not any(g in movie_genres for g in filters['genres']):
                return False
        
        # Year filter
        if 'year' in filters and filters['year']:
            release_date = movie.get('release_date', '')
            if release_date:
                movie_year = int(release_date[:4])
                if movie_year != filters['year']:
                    return False
        
        # Year range filter
        if 'year_min' in filters and filters['year_min']:
            release_date = movie.get('release_date', '')
            if release_date:
                movie_year = int(release_date[:4])
                if movie_year < filters['year_min']:
                    return False
        
        if 'year_max' in filters and filters['year_max']:
            release_date = movie.get('release_date', '')
            if release_date:
                movie_year = int(release_date[:4])
                if movie_year > filters['year_max']:
                    return False
        
        # Runtime filter (max duration in minutes)
        if 'max_runtime' in filters and filters['max_runtime']:
            runtime = movie.get('runtime')
            if runtime and runtime > filters['max_runtime']:
                return False
        
        return True
    
    def _movie_to_response(self, movie: dict, score: float) -> MovieResponse:
        """
        Convert TMDB movie data to response format
        
        Args:
            movie: Movie data from TMDB (full details)
            score: Recommendation score
            
        Returns:
            MovieResponse object
        """
        # Extract genres (TMDB returns list of dicts with 'name' key)
        genres = []
        if 'genres' in movie and movie['genres']:
            if isinstance(movie['genres'][0], dict):
                genres = [g['name'] for g in movie['genres']]
            else:
                genres = movie['genres']
        
        return MovieResponse(
            id=movie['id'],
            title=movie.get('title', ''),
            original_title=movie.get('original_title'),
            overview=movie.get('overview'),
            release_date=movie.get('release_date'),
            genres=genres,
            poster_url=self.tmdb_client.get_poster_url(movie.get('poster_path')),
            backdrop_url=self.tmdb_client.get_backdrop_url(movie.get('backdrop_path')),
            score=round(score, 3)
        )


# Global engine instance
_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine instance"""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine

# Made with Bob
