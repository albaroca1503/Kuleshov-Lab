"""
ChromaDB vector store for movie embeddings
"""
import chromadb
from pathlib import Path
from typing import Optional
import numpy as np

COLLECTION_NAME = "movies"
CHROMA_DIR = "./data/chroma"


class MovieVectorStore:
    """ChromaDB-backed vector store for movie embeddings"""

    def __init__(self, persist_dir: str = CHROMA_DIR):
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        print(f"✅ ChromaDB loaded — {self.collection.count()} movies indexed")

    def count(self) -> int:
        return self.collection.count()

    def has_movie(self, movie_id: int) -> bool:
        result = self.collection.get(ids=[str(movie_id)])
        return len(result["ids"]) > 0

    def add_movies_batch(
        self,
        movie_ids: list[int],
        embeddings: list[np.ndarray],
        movies_data: list[dict],
        texts: list[str],
    ) -> None:
        """Upsert a batch of movies"""
        self.collection.upsert(
            ids=[str(mid) for mid in movie_ids],
            embeddings=[e.tolist() for e in embeddings],
            documents=texts,
            metadatas=[self._build_metadata(m) for m in movies_data],
        )

    def get_metadata_by_ids(self, movie_ids: list[int]) -> dict[int, dict]:
        """Return {movie_id: metadata} for the given IDs"""
        if not movie_ids:
            return {}
        try:
            results = self.collection.get(
                ids=[str(mid) for mid in movie_ids],
                include=["metadatas"],
            )
            out = {}
            for i, mid_str in enumerate(results["ids"]):
                meta = results["metadatas"][i]
                genres_str = meta.get("genres", "")
                out[int(mid_str)] = {
                    "title": meta.get("title", ""),
                    "release_date": meta.get("release_date", ""),
                    "genres": [g.strip() for g in genres_str.split(",") if g.strip()],
                }
            return out
        except Exception as e:
            print(f"⚠️  Error fetching metadata by id: {e}")
            return {}

    def get_embeddings_by_ids(self, movie_ids: list[int]) -> list[np.ndarray]:
        """Retrieve stored embeddings for given movie IDs (for feedback vectors)"""
        if not movie_ids:
            return []
        try:
            results = self.collection.get(
                ids=[str(mid) for mid in movie_ids],
                include=["embeddings"],
            )
            embeddings = results.get("embeddings")
            if embeddings is None or len(embeddings) == 0:
                return []
            return [np.array(e, dtype=np.float32) for e in embeddings]
        except Exception as e:
            print(f"⚠️  Error fetching embeddings by id: {e}")
            return []

    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 50,
        filters: Optional[dict] = None,
    ) -> list[dict]:
        """
        Find the n most similar movies to the query embedding.
        Returns list of dicts ready for re-ranking and MovieResponse.
        """
        total = self.collection.count()
        if total == 0:
            return []

        n = min(n_results, total)

        kwargs: dict = {
            "query_embeddings": [query_embedding.tolist()],
            "n_results": n,
            "include": ["metadatas", "distances", "documents"],
        }

        where = self._build_where(filters) if filters else None
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        movies = []
        for i, movie_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            # cosine distance 0=identical, 2=opposite → convert to 0-1 similarity
            score = 1.0 - (distance / 2.0)

            genres_str = metadata.get("genres", "")
            genres = [g.strip() for g in genres_str.split(",") if g.strip()]

            movies.append({
                "id": int(movie_id),
                "title": metadata.get("title", ""),
                "original_title": metadata.get("original_title", ""),
                "overview": metadata.get("overview", ""),
                "release_date": metadata.get("release_date", ""),
                "vote_average": metadata.get("vote_average", 0.0),
                "genres": genres,
                "poster_path": metadata.get("poster_path", ""),
                "backdrop_path": metadata.get("backdrop_path", ""),
                "streaming_provider_ids": metadata.get("streaming_provider_ids", ""),
                "score": score,
            })

        return movies

    @staticmethod
    def _build_metadata(movie: dict) -> dict:
        """Extract flat metadata dict (ChromaDB requires primitive values)"""
        genres = movie.get("genres", [])
        if genres and isinstance(genres[0], dict):
            genre_names = [g["name"] for g in genres]
        else:
            genre_names = [*genres]

        release_date = movie.get("release_date", "") or ""
        year = int(release_date[:4]) if len(release_date) >= 4 else 0

        # Collect all flatrate provider IDs across all countries
        provider_ids: set[int] = set()
        for country_data in movie.get("watch/providers", {}).get("results", {}).values():
            for p in country_data.get("flatrate", []):
                pid = p.get("provider_id")
                if pid:
                    provider_ids.add(int(pid))

        return {
            "title": movie.get("title", "") or "",
            "original_title": movie.get("original_title", "") or "",
            "overview": (movie.get("overview", "") or "")[:1000],
            "release_date": release_date,
            "year": year,
            "vote_average": float(movie.get("vote_average", 0.0) or 0.0),
            "vote_count": int(movie.get("vote_count", 0) or 0),
            "popularity": float(movie.get("popularity", 0.0) or 0.0),
            "poster_path": movie.get("poster_path", "") or "",
            "backdrop_path": movie.get("backdrop_path", "") or "",
            "genres": ",".join(genre_names),
            "streaming_provider_ids": ",".join(str(p) for p in sorted(provider_ids)),
        }

    @staticmethod
    def _build_where(filters: dict) -> Optional[dict]:
        """Convert app filters to ChromaDB where clause (year filtering only)"""
        conditions = []

        if filters.get("year"):
            year = int(filters["year"])
            conditions.append({"year": {"$eq": year}})

        if filters.get("year_min"):
            conditions.append({"year": {"$gte": int(filters["year_min"])}})

        if filters.get("year_max"):
            conditions.append({"year": {"$lte": int(filters["year_max"])}})

        if not conditions:
            return None
        if len(conditions) == 1:
            return conditions[0]
        return {"$and": conditions}


_store: Optional[MovieVectorStore] = None


def get_vector_store() -> MovieVectorStore:
    """Get or create vector store singleton"""
    global _store
    if _store is None:
        _store = MovieVectorStore()
    return _store
