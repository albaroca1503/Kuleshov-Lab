"""
Script to ingest movies from TMDB into ChromaDB vector store.

Usage:
    cd backend
    python ingest_movies.py               # default: 20 pages per source (~1600 movies)
    python ingest_movies.py --pages 100   # ~8000 movies
    python ingest_movies.py --pages 500   # ~40000 movies (takes a while)
    python ingest_movies.py --skip-existing  # skip already-indexed movies
"""
import argparse
import time
import sys
import os

# Allow running from backend/ directory
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.config import get_settings
from app.embeddings import get_embedding_service
from app.tmdb import get_tmdb_client
from app.vector_store import get_vector_store

BATCH_SIZE = 50  # Movies per ChromaDB upsert batch
RATE_LIMIT_DELAY = 0.26  # TMDB allows ~4 req/sec on free tier


def fetch_and_index(pages_per_source: int, skip_existing: bool) -> None:
    settings = get_settings()
    tmdb = get_tmdb_client()
    embedder = get_embedding_service()
    store = get_vector_store()

    print(f"\n🎬 Starting ingestion — {pages_per_source} pages per source")
    print(f"📦 Already indexed: {store.count()} movies\n")

    # Sources: different sort orders to get diverse, quality movies
    sources = [
        ("vote_average.desc", {"vote_count.gte": 500}),   # Critically acclaimed
        ("popularity.desc", {"vote_count.gte": 100}),       # Crowd favourites
        ("primary_release_date.desc", {"vote_count.gte": 50}),  # Recent releases
        ("revenue.desc", {"vote_count.gte": 200}),           # Box office hits
        ("vote_count.desc", {}),                             # Most voted
    ]

    total_indexed = 0
    total_skipped = 0
    total_errors = 0

    for sort_by, extra_params in sources:
        print(f"\n📥 Source: sort_by={sort_by}")
        batch_ids: list[int] = []
        batch_embeddings = []
        batch_movies: list[dict] = []
        batch_texts: list[str] = []

        for page in range(1, pages_per_source + 1):
            params = {
                "sort_by": sort_by,
                "include_adult": False,
                "page": page,
                **extra_params,
            }

            try:
                response = tmdb.discover_movies(**params)
            except Exception as e:
                print(f"  ⚠️  Error fetching page {page}: {e}")
                time.sleep(1)
                continue

            page_movies = response.get("results", [])
            if not page_movies:
                break

            for movie_basic in page_movies:
                movie_id = movie_basic["id"]

                # Skip already indexed if requested
                if skip_existing and store.has_movie(movie_id):
                    total_skipped += 1
                    continue

                try:
                    movie = tmdb.get_movie_with_details(movie_id)
                    time.sleep(RATE_LIMIT_DELAY)
                except Exception as e:
                    print(f"  ⚠️  Error fetching movie {movie_id}: {e}")
                    total_errors += 1
                    time.sleep(1)
                    continue

                text = embedder.create_movie_text(movie)
                embedding = embedder.encode(text)

                batch_ids.append(movie_id)
                batch_embeddings.append(embedding)
                batch_movies.append(movie)
                batch_texts.append(text)

                # Flush batch
                if len(batch_ids) >= BATCH_SIZE:
                    store.add_movies_batch(batch_ids, batch_embeddings, batch_movies, batch_texts)
                    total_indexed += len(batch_ids)
                    print(f"  ✅ Indexed {total_indexed} movies total (latest: {movie.get('title', '?')})")
                    batch_ids, batch_embeddings, batch_movies, batch_texts = [], [], [], []

            print(f"  📄 Page {page}/{pages_per_source} done")

        # Flush remaining
        if batch_ids:
            store.add_movies_batch(batch_ids, batch_embeddings, batch_movies, batch_texts)
            total_indexed += len(batch_ids)

    print(f"\n🎉 Ingestion complete!")
    print(f"   Indexed:  {total_indexed}")
    print(f"   Skipped:  {total_skipped}")
    print(f"   Errors:   {total_errors}")
    print(f"   Total in store: {store.count()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest TMDB movies into ChromaDB")
    parser.add_argument("--pages", type=int, default=20, help="Pages per source (default: 20)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip already-indexed movies")
    args = parser.parse_args()

    fetch_and_index(args.pages, args.skip_existing)


if __name__ == "__main__":
    main()
