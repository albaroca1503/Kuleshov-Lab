"""
Kuleshov Lab - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import aiosqlite

from app.config import get_settings
from app.database import init_db, get_db, mark_movie_watched, get_user_stats
from app.models import (
    VibeRequest, 
    RecommendationResponse, 
    MarkWatchedRequest,
    UserStatsResponse
)
from app.recommender import get_recommendation_engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown"""
    # Startup
    print("🚀 Starting Kuleshov Lab Backend...")
    await init_db()
    print("✅ Backend ready!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Kuleshov Lab API",
    description="Cinematic recommendation engine with vibe-based search",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Kuleshov Lab API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.post("/api/recommend/vibe", response_model=RecommendationResponse)
async def recommend_by_vibe(
    request: VibeRequest,
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Get movie recommendations based on vibe description
    
    Args:
        request: Vibe request with description and optional filters
        
    Returns:
        List of recommended movies with scores
        
    Example:
        POST /api/recommend/vibe
        {
            "vibe": "neon-drenched 80s thriller",
            "limit": 10,
            "filters": {
                "year_min": 1980,
                "year_max": 1989
            }
        }
    """
    try:
        engine = get_recommendation_engine()
        movies = await engine.recommend_by_vibe(
            db=db,
            vibe=request.vibe,
            user_id=1,  # Single user for MVP
            limit=request.limit,
            filters=request.filters
        )
        
        return RecommendationResponse(
            vibe=request.vibe,
            movies=movies,
            total=len(movies)
        )
        
    except Exception as e:
        print(f"❌ Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/movies/{movie_id}/watched")
async def mark_watched(
    movie_id: int,
    request: MarkWatchedRequest,
    db: aiosqlite.Connection = Depends(get_db)
):
    """
    Mark a movie as watched/liked/disliked
    
    Args:
        movie_id: TMDB movie ID
        request: Status, optional rating, and movie title
        
    Returns:
        Success message
    """
    try:
        # Get movie title from TMDB if not provided
        from app.tmdb import get_tmdb_client
        tmdb = get_tmdb_client()
        
        try:
            movie_data = tmdb.get_movie(movie_id)
            movie_title = movie_data.get('title', f'Movie {movie_id}')
        except:
            movie_title = f'Movie {movie_id}'
        
        await mark_movie_watched(
            db=db,
            user_id=1,  # Single user for MVP
            movie_id=movie_id,
            movie_title=movie_title,
            status=request.status,
            rating=request.rating
        )
        
        return {
            "success": True,
            "message": f"Movie '{movie_title}' marked as {request.status}"
        }
        
    except Exception as e:
        print(f"❌ Error marking movie: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/stats", response_model=UserStatsResponse)
async def get_stats(db: aiosqlite.Connection = Depends(get_db)):
    """
    Get user statistics
    
    Returns:
        User stats including watched count, favorite genres, etc.
    """
    try:
        stats = await get_user_stats(db, user_id=1)
        return UserStatsResponse(**stats)
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/watched")
async def get_watched(db: aiosqlite.Connection = Depends(get_db)):
    """
    Get list of watched movies
    
    Returns:
        List of watched movie IDs
    """
    try:
        from app.database import get_watched_movies
        watched_ids = await get_watched_movies(db, user_id=1)
        return {
            "watched": list(watched_ids),
            "total": len(watched_ids)
        }
        
    except Exception as e:
        print(f"❌ Error getting watched movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True if settings.environment == "development" else False
    )

# Made with Bob
