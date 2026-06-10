"""
Claude AI client for intelligent re-ranking and explanations
"""
import json
import re
from typing import Optional
from anthropic import AsyncAnthropic
from app.config import get_settings

settings = get_settings()


class ClaudeService:
    """Service for Claude AI interactions"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude client
        
        Args:
            api_key: Anthropic API key (optional, uses settings if not provided)
        """
        self.api_key = api_key or settings.claude_api_key
        if not self.api_key:
            print("⚠️  Claude API key not configured - re-ranking disabled")
            self.client = None
        else:
            self.client = AsyncAnthropic(api_key=self.api_key)
            print("✅ Claude client initialized")
    
    def is_available(self) -> bool:
        """Check if Claude is available"""
        return self.client is not None
    
    async def expand_vibe(self, vibe: str) -> str:
        """
        Use Claude to expand a vibe query into a rich semantic description
        for better embedding quality. Falls back to the original vibe if unavailable.
        """
        if not self.is_available():
            return vibe

        prompt = f"""You are helping a movie recommendation system find films by semantic similarity.

Expand this search query into a rich cinematic description:
"{vibe}"

Write 2-3 sentences describing the aesthetic, mood, visual style, themes, and cinematic qualities this evokes. Include relevant directors, genres, film titles as examples, and descriptive atmospheric words. This will be embedded as a vector to find similar movies.

Return only the expanded description, no explanation or preamble."""

        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            expanded = response.content[0].text.strip()
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
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
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
        Use Claude to re-rank candidates and provide explanations
        
        Args:
            vibe: User's vibe description
            candidates: List of candidate movies (top 20-30 from embeddings)
            user_profile: Optional user profile data
            limit: Number of final recommendations
            
        Returns:
            List of re-ranked movies with explanations
        """
        if not self.is_available():
            print("⚠️  Claude not available, returning candidates as-is")
            return candidates[:limit]
        
        # Format candidates for Claude
        movies_text = self._format_movies_for_claude(candidates)
        
        # Build prompt
        prompt = self._build_rerank_prompt(vibe, movies_text, user_profile, taste_profile)
        
        try:
            # Call Claude with prompt caching
            response = await self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=[
                    {
                        "type": "text",
                        "text": "You are a cinematic expert and curator with deep knowledge of film history, genres, and cultural context. Your task is to recommend movies based on vibes and feelings, not just genres.",
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            result_text = response.content[0].text
            recommendations = self._parse_claude_response(result_text, candidates)
            
            print(f"✨ Claude re-ranked {len(recommendations)} movies")
            return recommendations[:limit]
            
        except Exception as e:
            print(f"❌ Error calling Claude: {e}")
            return candidates[:limit]
    
    def _format_movies_for_claude(self, movies: list[dict]) -> str:
        """Format movies for Claude prompt"""
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
        """Build prompt for Claude"""

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
    
    def _parse_claude_response(self, response_text: str, candidates: list[dict]) -> list[dict]:
        """Parse Claude's JSON response and match with candidates"""
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
            
            # Create title to movie mapping
            title_map = {movie['title'].lower(): movie for movie in candidates}
            
            # Re-order candidates based on Claude's ranking
            reranked = []
            for item in rankings:
                # Claude often appends " (YYYY)" to titles — strip before lookup
                title_lower = re.sub(r'\s*\(\d{4}\)\s*$', '', item['title']).lower().strip()
                if title_lower in title_map:
                    movie = title_map[title_lower].copy()
                    movie['reason'] = item.get('reason', '')
                    movie['claude_rank'] = item.get('rank', 999)
                    reranked.append(movie)
            
            # Add any missing candidates at the end
            reranked_titles = {m['title'].lower() for m in reranked}
            for movie in candidates:
                if movie['title'].lower() not in reranked_titles:
                    reranked.append(movie)
            
            return reranked
            
        except Exception as e:
            print(f"⚠️  Error parsing Claude response: {e}")
            print(f"Response: {response_text[:500]}")
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

Pick ONE film from the list and write a 2–3 sentence paragraph explaining why THIS film is the perfect watch for this moment. Be specific, evocative, and cinematic. Reference mood, season, or the emotional resonance it carries.

Respond in this exact format:
FILM: [exact title from the list]
REASON: [2-3 sentence paragraph]"""

        try:
            response = await self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.content[0].text.strip()
            lines = text.split("\n")
            film_line = next((l for l in lines if l.startswith("FILM:")), None)
            reason_lines = [l for l in lines if l.startswith("REASON:")]
            film = film_line.replace("FILM:", "").strip() if film_line else None
            reason = reason_lines[0].replace("REASON:", "").strip() if reason_lines else text
            return film, reason
        except Exception as e:
            print(f"⚠️  Signal generation failed: {e}")
            return None, ""


# Global service instance
_service: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance"""
    global _service
    if _service is None:
        _service = ClaudeService()
    return _service

# Made with Bob
