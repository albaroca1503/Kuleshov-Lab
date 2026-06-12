"""
SQLite database setup and operations
"""
import aiosqlite
import json
from pathlib import Path
from typing import Optional
from app.config import get_settings

settings = get_settings()


async def init_db():
    """
    Initialize database with required tables
    
    Note: We only store user data locally. Movie data comes from TMDB API.
    """
    db_path = Path("data/kuleshov.db")
    db_path.parent.mkdir(exist_ok=True)
    
    async with aiosqlite.connect(db_path) as db:
        # User movies table - tracks what users have watched
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                movie_id INTEGER NOT NULL,
                movie_title TEXT,
                status TEXT CHECK(status IN ('watched', 'liked', 'disliked')),
                rating REAL,
                watched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, movie_id)
            )
        """)
        
        # Movie cache table - stores basic movie info and embeddings
        await db.execute("""
            CREATE TABLE IF NOT EXISTS movie_cache (
                movie_id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                original_title TEXT,
                overview TEXT,
                release_date TEXT,
                genres TEXT,
                vote_average REAL,
                vote_count INTEGER,
                popularity REAL,
                poster_path TEXT,
                backdrop_path TEXT,
                embedding BLOB NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Legacy embedding cache table (for backwards compatibility)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS embedding_cache (
                movie_id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Taste profile — cached AI-generated summary of user taste
        await db.execute("""
            CREATE TABLE IF NOT EXISTS taste_profile (
                user_id INTEGER PRIMARY KEY,
                profile_text TEXT NOT NULL,
                movies_used_count INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # User settings — country and streaming subscriptions
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                country_code TEXT DEFAULT 'ES',
                streaming_service_ids TEXT DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_movies_user ON user_movies(user_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_movies_movie ON user_movies(movie_id)")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_user_movies_status ON user_movies(status)")
        
        await db.commit()
        print("✅ Database initialized successfully")


async def get_db():
    """Get database connection"""
    db = await aiosqlite.connect("data/kuleshov.db")
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()


async def mark_movie_watched(
    db: aiosqlite.Connection,
    user_id: int,
    movie_id: int,
    movie_title: str,
    status: str = "watched",
    rating: Optional[float] = None
):
    """Mark a movie as watched/liked/disliked"""
    await db.execute("""
        INSERT OR REPLACE INTO user_movies
        (user_id, movie_id, movie_title, status, rating, watched_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (user_id, movie_id, movie_title, status, rating))
    await db.commit()


async def get_watched_movies(db: aiosqlite.Connection, user_id: int = 1) -> set[int]:
    """Get set of watched movie IDs for a user"""
    async with db.execute(
        "SELECT movie_id FROM user_movies WHERE user_id = ?", 
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return {row[0] for row in rows}


async def get_user_stats(db: aiosqlite.Connection, user_id: int = 1) -> dict:
    """
    Get user statistics
    
    Note: Since we don't store full movie data, some stats are simplified
    """
    stats = {
        'total_watched': 0,
        'total_liked': 0,
        'total_disliked': 0,
        'favorite_genres': [],  # Would need TMDB API calls to populate
        'watch_time_hours': 0.0  # Would need TMDB API calls to calculate
    }
    
    # Count by status
    async with db.execute("""
        SELECT status, COUNT(*) as count
        FROM user_movies
        WHERE user_id = ?
        GROUP BY status
    """, (user_id,)) as cursor:
        async for row in cursor:
            if row[0] == 'watched':
                stats['total_watched'] = row[1]
            elif row[0] == 'liked':
                stats['total_liked'] = row[1]
            elif row[0] == 'disliked':
                stats['total_disliked'] = row[1]
    
    return stats


async def save_embedding_cache(db: aiosqlite.Connection, movie_id: int, embedding: bytes):
    """Cache an embedding for a movie"""
    await db.execute("""
        INSERT OR REPLACE INTO embedding_cache (movie_id, embedding, cached_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (movie_id, embedding))
    await db.commit()


async def get_embedding_cache(db: aiosqlite.Connection, movie_id: int) -> Optional[bytes]:
    """Get cached embedding for a movie"""
    async with db.execute(
        "SELECT embedding FROM embedding_cache WHERE movie_id = ?",
        (movie_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return row[0]
    return None


async def save_movie_to_cache(
    db: aiosqlite.Connection, movie_data: dict, embedding: bytes, commit: bool = True
):
    """Save movie data and embedding to cache"""
    genres_json = json.dumps(movie_data.get('genres', []))

    await db.execute("""
        INSERT OR REPLACE INTO movie_cache
        (movie_id, title, original_title, overview, release_date, genres,
         vote_average, vote_count, popularity, poster_path, backdrop_path,
         embedding, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        movie_data['id'],
        movie_data.get('title'),
        movie_data.get('original_title'),
        movie_data.get('overview'),
        movie_data.get('release_date'),
        genres_json,
        movie_data.get('vote_average'),
        movie_data.get('vote_count'),
        movie_data.get('popularity'),
        movie_data.get('poster_path'),
        movie_data.get('backdrop_path'),
        embedding
    ))
    if commit:
        await db.commit()


async def get_all_cached_movies(db: aiosqlite.Connection) -> list[dict]:
    """Get all cached movies with their embeddings"""
    movies = []
    async with db.execute("""
        SELECT movie_id, title, original_title, overview, release_date, genres,
               vote_average, vote_count, popularity, poster_path, backdrop_path, embedding
        FROM movie_cache
    """) as cursor:
        async for row in cursor:
            movie = {
                'id': row[0],
                'title': row[1],
                'original_title': row[2],
                'overview': row[3],
                'release_date': row[4],
                'genres': json.loads(row[5]) if row[5] else [],
                'vote_average': row[6],
                'vote_count': row[7],
                'popularity': row[8],
                'poster_path': row[9],
                'backdrop_path': row[10],
                'embedding': row[11]
            }
            movies.append(movie)
    return movies


async def get_taste_profile(db: aiosqlite.Connection, user_id: int = 1) -> dict | None:
    """Return the cached taste profile or None if it doesn't exist yet"""
    async with db.execute(
        "SELECT profile_text, movies_used_count FROM taste_profile WHERE user_id = ?",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return {"profile_text": row[0], "movies_used_count": row[1]}
        return None


async def save_taste_profile(
    db: aiosqlite.Connection, user_id: int, profile_text: str, movies_used_count: int
) -> None:
    """Upsert the taste profile for a user"""
    await db.execute(
        """INSERT INTO taste_profile (user_id, profile_text, movies_used_count, updated_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
               profile_text = excluded.profile_text,
               movies_used_count = excluded.movies_used_count,
               updated_at = CURRENT_TIMESTAMP""",
        (user_id, profile_text, movies_used_count)
    )
    await db.commit()


async def get_liked_disliked_since(
    db: aiosqlite.Connection, user_id: int = 1, offset: int = 0
) -> tuple[list[str], list[str]]:
    """Return (liked_titles, disliked_titles) starting from the given offset (for incremental updates)"""
    liked, disliked = [], []
    async with db.execute(
        """SELECT movie_title, status FROM user_movies
           WHERE user_id = ? AND status IN ('liked', 'disliked') AND movie_title IS NOT NULL
           ORDER BY watched_at ASC LIMIT -1 OFFSET ?""",
        (user_id, offset)
    ) as cursor:
        async for row in cursor:
            if row[1] == 'liked':
                liked.append(row[0])
            else:
                disliked.append(row[0])
    return liked, disliked


async def get_recent_liked_movies(
    db: aiosqlite.Connection, user_id: int = 1, limit: int = 5
) -> list[str]:
    """Return titles of the most recently liked movies"""
    async with db.execute(
        """SELECT movie_title FROM user_movies
           WHERE user_id = ? AND status = 'liked' AND movie_title IS NOT NULL
           ORDER BY watched_at DESC LIMIT ?""",
        (user_id, limit)
    ) as cursor:
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def get_movies_by_status_pair(
    db: aiosqlite.Connection, user_id: int = 1
) -> tuple[list[int], list[int]]:
    """Return (liked_ids, disliked_ids) for a user"""
    liked, disliked = [], []
    async with db.execute(
        "SELECT movie_id, status FROM user_movies WHERE user_id = ? AND status IN ('liked', 'disliked')",
        (user_id,)
    ) as cursor:
        async for row in cursor:
            if row[1] == 'liked':
                liked.append(row[0])
            else:
                disliked.append(row[0])
    return liked, disliked


async def get_watched_movies_with_status(db: aiosqlite.Connection, user_id: int = 1) -> list[dict]:
    """Get all tracked movies with their status, ordered by most recent"""
    async with db.execute(
        "SELECT movie_id, movie_title, status, rating, watched_at FROM user_movies WHERE user_id = ? ORDER BY watched_at DESC",
        (user_id,)
    ) as cursor:
        rows = await cursor.fetchall()
        return [
            {"movie_id": row[0], "movie_title": row[1], "status": row[2], "rating": row[3], "watched_at": row[4]}
            for row in rows
        ]


async def get_user_settings(db: aiosqlite.Connection, user_id: int = 1) -> dict:
    """Return user settings or sensible defaults"""
    async with db.execute(
        "SELECT country_code, streaming_service_ids FROM user_settings WHERE user_id = ?",
        (user_id,)
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return {
                "country_code": row[0],
                "streaming_service_ids": json.loads(row[1]),
            }
        return {"country_code": "ES", "streaming_service_ids": []}


async def save_user_settings(
    db: aiosqlite.Connection,
    user_id: int,
    country_code: str,
    streaming_service_ids: list[int],
) -> None:
    """Upsert user settings"""
    await db.execute(
        """INSERT INTO user_settings (user_id, country_code, streaming_service_ids, updated_at)
           VALUES (?, ?, ?, CURRENT_TIMESTAMP)
           ON CONFLICT(user_id) DO UPDATE SET
               country_code = excluded.country_code,
               streaming_service_ids = excluded.streaming_service_ids,
               updated_at = CURRENT_TIMESTAMP""",
        (user_id, country_code, json.dumps(streaming_service_ids))
    )
    await db.commit()


async def get_watched_and_feedback_ids(
    db: aiosqlite.Connection, user_id: int = 1
) -> tuple[set[int], list[int], list[int]]:
    """Return (all_watched_ids, liked_ids, disliked_ids) in a single query."""
    watched: set[int] = set()
    liked: list[int] = []
    disliked: list[int] = []
    async with db.execute(
        "SELECT movie_id, status FROM user_movies WHERE user_id = ?",
        (user_id,)
    ) as cursor:
        async for row in cursor:
            watched.add(row[0])
            if row[1] == 'liked':
                liked.append(row[0])
            elif row[1] == 'disliked':
                disliked.append(row[0])
    return watched, liked, disliked


async def get_cache_stats(db: aiosqlite.Connection) -> dict:
    """Get statistics about the movie cache"""
    async with db.execute("SELECT COUNT(*) FROM movie_cache") as cursor:
        row = await cursor.fetchone()
        total_movies = row[0] if row else 0
    
    return {
        'total_cached_movies': total_movies
    }

