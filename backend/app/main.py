"""
Kuleshov Lab - FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import aiosqlite

from app.config import get_settings
from app.database import (
    init_db, get_db, mark_movie_watched, get_user_stats,
    get_user_settings, save_user_settings,
)
from app.models import (
    VibeRequest,
    RecommendationResponse,
    MarkWatchedRequest,
    UserStatsResponse,
    UserSettingsRequest,
    SignalResponse,
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
    background_tasks: BackgroundTasks,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Mark a movie as watched/liked/disliked"""
    try:
        movie_title = request.movie_title
        if not movie_title:
            try:
                from app.tmdb import get_tmdb_client
                movie_title = get_tmdb_client().get_movie(movie_id).get('title', f'Movie {movie_id}')
            except Exception:
                movie_title = f'Movie {movie_id}'

        await mark_movie_watched(
            db=db,
            user_id=1,
            movie_id=movie_id,
            movie_title=movie_title,
            status=request.status,
            rating=request.rating
        )

        # Rebuild taste profile in background so it's ready for the next recommendation
        if request.status in ("liked", "disliked"):
            engine = get_recommendation_engine()
            background_tasks.add_task(engine.refresh_taste_profile, user_id=1)

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


@app.get("/api/user/watched-movies")
async def get_watched_movies_details(db: aiosqlite.Connection = Depends(get_db)):
    """
    Get watched/liked/disliked movies with full details from ChromaDB
    """
    from app.database import get_watched_movies_with_status
    from app.vector_store import get_vector_store

    try:
        watched = await get_watched_movies_with_status(db, user_id=1)
        if not watched:
            return {"movies": [], "total": 0}

        store = get_vector_store()
        status_map = {w["movie_id"]: w for w in watched}
        movie_ids = [w["movie_id"] for w in watched]

        try:
            results = store.collection.get(
                ids=[str(mid) for mid in movie_ids],
                include=["metadatas"],
            )
            movies = []
            for i, mid_str in enumerate(results["ids"]):
                mid = int(mid_str)
                meta = results["metadatas"][i]
                sw = status_map.get(mid, {})
                genres_str = meta.get("genres", "")
                genres = [g.strip() for g in genres_str.split(",") if g.strip()]
                poster_path = meta.get("poster_path", "")
                movies.append({
                    "id": mid,
                    "title": meta.get("title") or sw.get("movie_title", ""),
                    "release_date": meta.get("release_date", ""),
                    "genres": genres,
                    "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
                    "status": sw.get("status", "watched"),
                    "watched_at": sw.get("watched_at", ""),
                })
        except Exception:
            # Fallback: use only SQLite data (no poster)
            movies = [
                {"id": w["movie_id"], "title": w["movie_title"] or "", "release_date": "",
                 "genres": [], "poster_url": None, "status": w["status"], "watched_at": w.get("watched_at", "")}
                for w in watched
            ]

        return {"movies": movies, "total": len(movies)}

    except Exception as e:
        print(f"❌ Error getting watched movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/movies/{movie_id}/details")
async def get_movie_details(
    movie_id: int,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Rich movie details: streaming providers, reviews, director, cast, ratings"""
    try:
        from app.tmdb import get_tmdb_client
        user_settings = await get_user_settings(db, user_id=1)
        country = user_settings.get("country_code", "ES")
        details = get_tmdb_client().get_movie_rich_details(movie_id, country_code=country)
        return details
    except Exception as e:
        print(f"❌ Error fetching movie details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/user/settings")
async def get_user_settings_endpoint(db: aiosqlite.Connection = Depends(get_db)):
    """Get user settings (country, streaming services)"""
    try:
        return await get_user_settings(db, user_id=1)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/user/settings")
async def update_user_settings(
    request: UserSettingsRequest,
    db: aiosqlite.Connection = Depends(get_db)
):
    """Save user settings (country, streaming subscriptions)"""
    try:
        await save_user_settings(db, 1, request.country_code, request.streaming_service_ids)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend/vault", response_model=RecommendationResponse)
async def recommend_from_vault(db: aiosqlite.Connection = Depends(get_db)):
    """Get recommendations based on the user's vault (taste profile)."""
    try:
        engine = get_recommendation_engine()
        movies = await engine.recommend_from_vault(db=db, user_id=1, limit=20)
        return RecommendationResponse(vibe="your vault", movies=movies, total=len(movies))
    except Exception as e:
        print(f"❌ Error generating vault recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/recommend/signal", response_model=SignalResponse)
async def get_signal(db: aiosqlite.Connection = Depends(get_db)):
    """Get the movie of the day — one curated pick based on vault + context."""
    try:
        engine = get_recommendation_engine()
        result = await engine.get_signal(db=db, user_id=1)
        if not result:
            raise HTTPException(status_code=404, detail="No signal available — add films to your vault first")
        return SignalResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating signal: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True if settings.environment == "development" else False
    )

