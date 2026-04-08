#!/usr/bin/env python3
"""
Script to populate the movie cache with TMDB data and embeddings
Run this periodically to keep the cache fresh
"""
import asyncio
import aiosqlite
import numpy as np
from app.tmdb import get_tmdb_client
from app.embeddings import get_embedding_service
from app.database import save_movie_to_cache, get_cache_stats


async def populate_cache(num_pages: int = 50):
    """
    Populate cache with movies from TMDB
    
    Args:
        num_pages: Number of pages to fetch per source (50 pages = ~1000 movies per source)
    """
    print("🎬 Starting cache population...")
    
    tmdb = get_tmdb_client()
    embeddings = get_embedding_service()
    
    # Connect to database
    db = await aiosqlite.connect("data/kuleshov.db")
    
    try:
        movies_added = 0
        movies_skipped = 0
        seen_ids = set()
        
        # Fetch from multiple sources for diversity
        sources = [
            ('vote_average.desc', num_pages),      # Top rated
            ('popularity.desc', num_pages),         # Popular
            ('primary_release_date.desc', num_pages),  # Recent
            ('revenue.desc', num_pages),            # Box office
        ]
        
        base_params = {
            'include_adult': False,
            'vote_count.gte': 100,
        }
        
        for sort_by, pages in sources:
            print(f"\n📥 Fetching {pages} pages sorted by {sort_by}...")
            
            discover_params = base_params.copy()
            discover_params['sort_by'] = sort_by
            
            for page in range(1, pages + 1):
                try:
                    discover_params['page'] = page
                    response = tmdb.discover_movies(**discover_params)
                    page_movies = response.get('results', [])
                    
                    for movie_basic in page_movies:
                        movie_id = movie_basic['id']
                        
                        # Skip duplicates
                        if movie_id in seen_ids:
                            movies_skipped += 1
                            continue
                        seen_ids.add(movie_id)
                        
                        try:
                            # Get full movie details
                            full_movie = tmdb.get_movie(movie_id)
                            
                            # Generate embedding
                            embedding = embeddings.generate_movie_embedding(full_movie)
                            embedding_bytes = embedding.tobytes()
                            
                            # Save to cache
                            await save_movie_to_cache(db, full_movie, embedding_bytes)
                            
                            movies_added += 1
                            
                            if movies_added % 50 == 0:
                                print(f"  ✅ Cached {movies_added} movies...")
                            
                        except Exception as e:
                            print(f"  ⚠️  Error processing movie {movie_id}: {e}")
                            continue
                    
                except Exception as e:
                    print(f"  ⚠️  Error fetching page {page}: {e}")
                    continue
        
        # Print final stats
        stats = await get_cache_stats(db)
        print(f"\n✨ Cache population complete!")
        print(f"📊 Added: {movies_added} movies")
        print(f"⏭️  Skipped: {movies_skipped} duplicates")
        print(f"💾 Total in cache: {stats['total_cached_movies']} movies")
        
    finally:
        await db.close()


if __name__ == "__main__":
    import sys
    
    # Get number of pages from command line (default 50)
    num_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    
    print(f"🚀 Populating cache with {num_pages} pages per source...")
    print(f"📝 This will fetch approximately {num_pages * 20 * 4} movies")
    print(f"⏱️  Estimated time: {num_pages * 2} minutes\n")
    
    asyncio.run(populate_cache(num_pages))

# Made with Bob
