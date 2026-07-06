"""
AI client for intelligent re-ranking and explanations
"""
import json
import re
from typing import Optional
import litellm
from app.config import get_settings

settings = get_settings()


class AIClient:
    """
    Provider-agnostic AI service for re-ranking and generating film curation text.

    Uses litellm, so `ai_model_fast` / `ai_model_smart` in config can point at any
    supported provider (e.g. "claude-sonnet-4-6", "gpt-4o", "gemini/gemini-2.0-flash",
    "ollama/llama3") without changing this file.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ai_api_key
        self.available = bool(self.api_key)
        if not self.available:
            print("⚠️  AI API key not configured - re-ranking disabled")
        else:
            print("✅ AI client initialized")

    def is_available(self) -> bool:
        return self.available

    async def _complete(self, model: str, messages: list[dict], max_tokens: int) -> str:
        response = await litellm.acompletion(
            model=model,
            api_key=self.api_key,
            max_tokens=max_tokens,
            messages=messages,
        )
        return response.choices[0].message.content.strip()
    
    async def expand_vibe(self, vibe: str) -> str:
        """Expand a vibe query into a richer semantic description for better embedding quality."""
        if not self.is_available():
            return vibe

        prompt = f"""You are helping a movie recommendation system find films by semantic similarity.

Expand this search query into a rich cinematic description:
"{vibe}"

Write 2-3 sentences describing the aesthetic, mood, visual style, themes, and cinematic qualities this evokes. Include relevant directors, genres, film titles as examples, and descriptive atmospheric words. This will be embedded as a vector to find similar movies.

Return only the expanded description, no explanation or preamble."""

        try:
            expanded = await self._complete(
                model=settings.ai_model_fast,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            print(f"🔍 Vibe expanded: {expanded[:100]}…")
            return expanded
        except Exception as e:
            print(f"⚠️  Vibe expansion failed: {e}")
            return vibe

    async def build_taste_profile(
        self,
        liked: list[str],
        disliked: list[str],
        current_profile: str | None = None,
    ) -> str | None:
        """
        Generate or incrementally update a taste profile.
        - First call: generate from scratch with all liked/disliked so far
        - Subsequent calls: update current_profile with only the new movies
        """
        if not self.is_available():
            return None
        if not liked and not disliked:
            return None

        liked_text = ", ".join(f'"{t}"' for t in liked) if liked else "none"
        disliked_text = ", ".join(f'"{t}"' for t in disliked) if disliked else "none"

        if current_profile:
            prompt = f"""You are updating a cinematic taste profile.

Current profile:
"{current_profile}"

New movies this user liked: {liked_text}
New movies this user disliked: {disliked_text}

Rewrite the profile incorporating these new signals. Keep it 3-4 sentences, specific and cinematic."""
        else:
            prompt = f"""You are building a cinematic taste profile for a film enthusiast.

Movies they liked: {liked_text}
Movies they disliked: {disliked_text}

Write a taste profile of 3-4 sentences describing:
- Their preferred aesthetic, mood, tone and visual style
- Eras, genres or directors they gravitate toward
- What they clearly avoid

Be specific and cinematic, not generic. No bullet points, just prose."""

        try:
            return await self._complete(
                model=settings.ai_model_smart,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
        except Exception as e:
            print(f"❌ Error building taste profile: {e}")
            return current_profile

    async def rerank_and_explain(
        self,
        vibe: str,
        candidates: list[dict],
        user_profile: Optional[dict] = None,
        taste_profile: Optional[str] = None,
        limit: int = 10
    ) -> list[dict]:
        """
        Re-rank candidates and add explanations.

        Args:
            vibe: User's vibe description
            candidates: List of candidate movies (top 20-30 from embeddings)
            user_profile: Optional user profile data
            limit: Number of final recommendations
            
        Returns:
            List of re-ranked movies with explanations
        """
        if not self.is_available():
            return candidates[:limit]

        movies_text = self._format_movies_for_prompt(candidates)
        prompt = self._build_rerank_prompt(vibe, movies_text, user_profile, taste_profile)
        
        try:
            result_text = await self._complete(
                model=settings.ai_model_smart,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a cinematic expert and curator with deep knowledge of film history, genres, and cultural context. Your task is to recommend movies based on vibes and feelings, not just genres.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                max_tokens=900,
            )
            recommendations = self._parse_rerank_response(result_text, candidates)
            print(f"✨ Re-ranked {len(recommendations)} movies")
            return recommendations[:limit]

        except Exception as e:
            print(f"❌ Error calling AI: {e}")
            return candidates[:limit]

    def _format_movies_for_prompt(self, movies: list[dict]) -> str:
        lines = []
        for i, movie in enumerate(movies, 1):
            # Handle genres - could be list of strings or list of dicts
            genres_raw = movie.get('genres', [])
            if genres_raw and isinstance(genres_raw[0], dict):
                genres = ', '.join([g['name'] for g in genres_raw])
            elif genres_raw:
                genres = ', '.join(genres_raw)
            else:
                genres = 'Unknown'
            
            # Get overview
            overview = movie.get('overview', 'No overview available')
            if len(overview) > 200:
                overview = overview[:200] + '...'
            
            lines.append(
                f"{i}. {movie.get('title', 'Unknown')} ({movie.get('release_date', 'N/A')[:4]})\n"
                f"   Genres: {genres}\n"
                f"   Overview: {overview}\n"
                f"   Score: {movie.get('score', 0):.3f}"
            )
        return '\n\n'.join(lines)
    
    def _build_rerank_prompt(
        self,
        vibe: str,
        movies_text: str,
        user_profile: Optional[dict],
        taste_profile: Optional[str] = None,
    ) -> str:

        profile_text = ""
        if user_profile:
            profile_text = f"\n\nUser Profile:\n- Watched: {user_profile.get('total_watched', 0)} movies\n- Favorite genres: {', '.join([g[0] for g in user_profile.get('favorite_genres', [])[:3]])}"

        taste_text = ""
        if taste_profile:
            taste_text = f"\n\nUser's cinematic taste profile:\n{taste_profile}\nLet this inform your ranking — prioritise films that match both the vibe AND the user's established aesthetic."

        return f"""You are curating a personalised film list. From the candidates below, select ONLY the films that genuinely match the user's vibe — skip any that don't fit well.

User's Vibe: "{vibe}"{profile_text}{taste_text}

Candidate Movies (pre-ranked by semantic similarity):
{movies_text}

Your task:
1. Understand the FEELING and ATMOSPHERE the user wants (not just genre)
2. Select only the films that are a real match — drop poor fits entirely
3. Rank the selected films from best to worst match
4. For each selected film write one specific sentence on why it fits the vibe (not why it doesn't)
5. Consider mood, visual style, era, pacing, emotional tone and cultural context

Return your response as a JSON array with this exact format:
[
  {{
    "title": "Movie Title",
    "rank": 1,
    "reason": "One sentence on why this fits the vibe"
  }},
  ...
]

Rules:
- Include ONLY genuine matches — if a film clearly doesn't fit the vibe, omit it
- Never include a film just to fill the list
- reason must explain why the film FITS, never why it doesn't
- Return ONLY the JSON array, no markdown, no extra text"""
    
    def _parse_rerank_response(self, response_text: str, candidates: list[dict]) -> list[dict]:
        try:
            # Remove markdown code blocks if present
            if '```json' in response_text:
                # Extract content between ```json and ```
                start_marker = response_text.find('```json') + 7
                end_marker = response_text.find('```', start_marker)
                if end_marker != -1:
                    response_text = response_text[start_marker:end_marker].strip()
            elif '```' in response_text:
                # Extract content between ``` and ```
                start_marker = response_text.find('```') + 3
                end_marker = response_text.find('```', start_marker)
                if end_marker != -1:
                    response_text = response_text[start_marker:end_marker].strip()
            
            # Extract JSON from response
            start = response_text.find('[')
            end = response_text.rfind(']') + 1
            if start == -1 or end == 0:
                raise ValueError("No JSON array found in response")
            
            json_text = response_text[start:end]
            rankings = json.loads(json_text)
            
            title_map = {movie['title'].lower(): movie for movie in candidates}
            num_ranked = len(rankings)

            reranked = []
            for item in rankings:
                title_lower = re.sub(r'\s*\(\d{4}\)\s*$', '', item['title']).lower().strip()
                if title_lower in title_map:
                    movie = title_map[title_lower].copy()
                    movie['reason'] = item.get('reason', '')
                    rank = item.get('rank', num_ranked)
                    # Replace ChromaDB score with AI rank-based score (rank 1 → ~1.0, last → ~0.6)
                    movie['score'] = round(1.0 - (rank - 1) / max(num_ranked, 1) * 0.4, 3)
                    reranked.append(movie)

            # Fill remaining slots with ChromaDB candidates (no reason — shown without curation text)
            reranked_titles = {m['title'].lower() for m in reranked}
            for movie in candidates:
                if movie['title'].lower() not in reranked_titles:
                    reranked.append(movie)

            return reranked
            
        except Exception as e:
            print(f"⚠️  Error parsing AI response: {e}")
            return candidates


    async def generate_signal(
        self,
        candidates: list[dict],
        taste_profile: str | None,
        context: str,
    ) -> tuple[str | None, str]:
        """Pick THE one film of the day and write a cinematic signal reason."""
        if not self.is_available() or not candidates:
            return None, ""

        movies_text = "\n".join(
            f"- {m.get('title', 'Unknown')} ({str(m.get('release_date', 'N/A'))[:4]})"
            for m in candidates[:10]
        )
        taste_text = f"\n\nUser's cinematic taste profile:\n{taste_profile}" if taste_profile else ""

        prompt = f"""You are a film curator choosing the single most compelling film to watch right now.

{context}{taste_text}

Pre-selected candidates:
{movies_text}

Pick ONE film from the list. If today's headlines are provided, consider how they set the emotional mood of the day — choose a film that either resonates with those themes or offers the perfect counterpoint. Write a 2–3 sentence paragraph explaining why THIS film is the right watch for tonight. Be specific, evocative, and cinematic.

Respond in this exact format:
FILM: [exact title from the list]
REASON: [2-3 sentence paragraph]"""

        try:
            text = await self._complete(
                model=settings.ai_model_fast,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
            )
            film_line = next((l for l in text.split("\n") if l.startswith("FILM:")), None)
            film = film_line.replace("FILM:", "").strip() if film_line else None
            reason_start = text.find("REASON:")
            reason = text[reason_start + 7:].strip() if reason_start != -1 else text
            return film, reason
        except Exception as e:
            print(f"⚠️  Signal generation failed: {e}")
            return None, ""


_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    global _client
    if _client is None:
        _client = AIClient()
    return _client
