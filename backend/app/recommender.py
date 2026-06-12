"""
Recommendation engine — vibe-based movie recommendations via ChromaDB vector search
"""
import numpy as np
import aiosqlite
from typing import Optional

from app.embeddings import get_embedding_service
from app.tmdb import get_tmdb_client
from app.ai_client import get_ai_client
from app.vector_store import get_vector_store
from app.database import (
    get_watched_movies, get_user_stats, get_movies_by_status_pair,
    get_taste_profile, save_taste_profile, get_liked_disliked_since,
)
from app.models import MovieResponse


class RecommendationEngine:
    """Engine for generating movie recommendations"""

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.tmdb_client = get_tmdb_client()
        self.ai_client = get_ai_client()
        self.vector_store = get_vector_store()

    async def recommend_by_vibe(
        self,
        db: aiosqlite.Connection,
        vibe: str,
        user_id: int = 1,
        limit: int = 10,
        filters: Optional[dict] = None,
    ) -> list[MovieResponse]:
        """
        Generate recommendations based on a vibe description.

        Steps:
        1. Expand + embed the vibe
        2. Query ChromaDB for the top candidates (entire indexed catalogue)
        3. Exclude watched movies
        4. Apply genre filter post-query (ChromaDB metadata only supports year)
        5. AI re-ranks and adds explanations
        """
        indexed = self.vector_store.count()
        print(f"🎬 Vibe: '{vibe}' — searching {indexed} indexed movies")

        if indexed == 0:
            print("⚠️  ChromaDB is empty. Run: python ingest_movies.py")
            return []

        # 1. Expand vibe with AI, fall back to local rules
        expanded = await self.ai_client.expand_vibe(vibe)
        if expanded == vibe:
            expanded = self.embedding_service.expand_vibe(vibe)
        vibe_embedding = self.embedding_service.encode(expanded)

        # 2. Adjust query with liked/disliked feedback (Rocchio algorithm)
        liked_ids, disliked_ids = await get_movies_by_status_pair(db, user_id)
        query_embedding = self._apply_feedback(vibe_embedding, liked_ids, disliked_ids)

        # 2. Query ChromaDB — fetch plenty of candidates to account for filtering
        fetch_n = min(max(limit * 20, 200), indexed)
        candidates = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=fetch_n,
            filters=filters,
        )
        print(f"🔍 ChromaDB returned {len(candidates)} candidates")

        # 3. Exclude watched movies
        watched_ids = await get_watched_movies(db, user_id)
        candidates = [m for m in candidates if m["id"] not in watched_ids]
        print(f"📋 {len(candidates)} candidates after excluding {len(watched_ids)} watched")

        # 4. Genre filter (post-query, since ChromaDB can't filter on CSV metadata)
        if filters and filters.get("genres"):
            required = set(filters["genres"])
            genre_filtered = []
            for m in candidates:
                # genres are stored as list[str] after the vector_store.search() call
                tmdb_genre_ids = set(m.get("genres", []))
                if tmdb_genre_ids & required:
                    genre_filtered.append(m)
            candidates = genre_filtered
            print(f"🎭 {len(candidates)} candidates after genre filter")

        if not candidates:
            return []

        top_candidates = candidates[:25]

        if self.ai_client.is_available():
            user_profile = await get_user_stats(db, user_id)
            taste_profile = await self._get_or_update_taste_profile(db, user_id)
            reranked = await self.ai_client.rerank_and_explain(
                vibe=vibe,
                candidates=top_candidates,
                user_profile=user_profile,
                taste_profile=taste_profile,
                limit=limit,
            )
        else:
            reranked = top_candidates[:limit]

        recommendations = [self._movie_to_response(m, m.get("score", 0)) for m in reranked]
        print(f"✨ Returning {len(recommendations)} recommendations")
        return recommendations

    async def _get_or_update_taste_profile(
        self, db: aiosqlite.Connection, user_id: int, update_every: int = 5
    ) -> str | None:
        """
        Return the cached taste profile, regenerating it when the user has
        added `update_every` new liked/disliked movies since the last build.
        """
        cached = await get_taste_profile(db, user_id)
        movies_used = cached["movies_used_count"] if cached else 0

        liked_new, disliked_new = await get_liked_disliked_since(db, user_id, offset=movies_used)
        new_count = len(liked_new) + len(disliked_new)

        # Not enough new data yet — return cached profile as-is
        if new_count < update_every and cached:
            return cached["profile_text"]

        # Not enough total data to build a useful profile
        total = movies_used + new_count
        if total < 3:
            return None

        print(f"🎭 Building taste profile ({new_count} new movies, {total} total)…")
        new_profile = await self.ai_client.build_taste_profile(
            liked=liked_new,
            disliked=disliked_new,
            current_profile=cached["profile_text"] if cached else None,
        )

        if new_profile:
            await save_taste_profile(db, user_id, new_profile, total)
            print("✅ Taste profile updated")

        return new_profile

    async def recommend_from_vault(
        self,
        db: aiosqlite.Connection,
        user_id: int = 1,
        limit: int = 20,
    ) -> list[MovieResponse]:
        """Recommend films based on the user's vault (taste profile + liked history)."""
        taste = await get_taste_profile(db, user_id)
        if taste and taste.get("profile_text"):
            vibe = taste["profile_text"]
        else:
            stats = await get_user_stats(db, user_id)
            genres = [g[0] for g in stats.get("favorite_genres", [])[:3]]
            liked_ids, _ = await get_movies_by_status_pair(db, user_id)
            if genres:
                vibe = f"films with {', '.join(genres)} themes — rich, atmospheric, and cinematically bold"
            elif liked_ids:
                vibe = "deeply personal and visually distinctive films with strong atmosphere"
            else:
                return []
        return await self.recommend_by_vibe(db, vibe, user_id, limit)

    async def get_signal(
        self,
        db: aiosqlite.Connection,
        user_id: int = 1,
    ) -> Optional[dict]:
        """Get the movie of the day — one curated recommendation."""
        from datetime import datetime
        month_name = datetime.now().strftime("%B")
        context = f"A film perfect for a {month_name} evening"

        taste = await get_taste_profile(db, user_id)
        taste_text = taste["profile_text"] if taste and taste.get("profile_text") else None

        vibe = taste_text or "a cinematic masterpiece that rewards close attention"
        candidates = await self.recommend_by_vibe(db, vibe, user_id, limit=10)

        if not candidates:
            return None

        signal_reason = candidates[0].reason or "A film worth watching tonight."

        if self.ai_client.is_available():
            film_title, reason = await self.ai_client.generate_signal(
                candidates=[c.model_dump() for c in candidates],
                taste_profile=taste_text,
                context=context,
            )
            if film_title:
                for c in candidates:
                    if c.title.lower() == film_title.lower():
                        return {"movie": c, "signal_reason": reason or signal_reason, "context": context}

        return {"movie": candidates[0], "signal_reason": signal_reason, "context": context}

    def _apply_feedback(
        self,
        vibe_embedding: np.ndarray,
        liked_ids: list[int],
        disliked_ids: list[int],
        liked_weight: float = 0.3,
        disliked_weight: float = 0.2,
        min_movies: int = 2,
    ) -> np.ndarray:
        """
        Rocchio algorithm: shift the query vector toward liked movies
        and away from disliked ones.
        Only applied when there are enough examples to avoid noisy feedback.
        """
        query = vibe_embedding.astype(np.float64).copy()
        applied = []

        if len(liked_ids) >= min_movies:
            liked_vecs = self.vector_store.get_embeddings_by_ids(liked_ids)
            if liked_vecs:
                liked_profile = np.mean(liked_vecs, axis=0)
                query += liked_weight * liked_profile
                applied.append(f"+liked({len(liked_vecs)})")

        if len(disliked_ids) >= min_movies:
            disliked_vecs = self.vector_store.get_embeddings_by_ids(disliked_ids)
            if disliked_vecs:
                disliked_profile = np.mean(disliked_vecs, axis=0)
                query -= disliked_weight * disliked_profile
                applied.append(f"-disliked({len(disliked_vecs)})")

        if applied:
            print(f"🎯 Feedback applied: {', '.join(applied)}")

        norm = np.linalg.norm(query)
        if norm > 0:
            query = query / norm

        return query.astype(np.float32)

    def _movie_to_response(self, movie: dict, score: float) -> MovieResponse:
        """Build MovieResponse from a ChromaDB result dict"""
        genres = movie.get("genres", [])
        # Ensure genres is a list of strings (it already is from vector_store.search)
        if genres and isinstance(genres[0], dict):
            genres = [g["name"] for g in genres]

        poster_path = movie.get("poster_path", "")
        backdrop_path = movie.get("backdrop_path", "")

        return MovieResponse(
            id=movie["id"],
            title=movie.get("title", ""),
            original_title=movie.get("original_title") or None,
            overview=movie.get("overview") or None,
            release_date=movie.get("release_date") or None,
            genres=genres,
            poster_url=self.tmdb_client.get_poster_url(poster_path) if poster_path else None,
            backdrop_url=self.tmdb_client.get_backdrop_url(backdrop_path) if backdrop_path else None,
            score=round(score, 3),
            reason=movie.get("reason") or None,
        )


_engine: Optional[RecommendationEngine] = None


def get_recommendation_engine() -> RecommendationEngine:
    """Get or create recommendation engine singleton"""
    global _engine
    if _engine is None:
        _engine = RecommendationEngine()
    return _engine
