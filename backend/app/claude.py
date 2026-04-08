"""
Claude AI client for intelligent re-ranking and explanations
"""
import json
from typing import Optional
from anthropic import Anthropic
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
            self.client = Anthropic(api_key=self.api_key)
            print("✅ Claude client initialized")
    
    def is_available(self) -> bool:
        """Check if Claude is available"""
        return self.client is not None
    
    async def rerank_and_explain(
        self,
        vibe: str,
        candidates: list[dict],
        user_profile: Optional[dict] = None,
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
        prompt = self._build_rerank_prompt(vibe, movies_text, user_profile)
        
        try:
            # Call Claude with prompt caching
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=2000,
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
        user_profile: Optional[dict]
    ) -> str:
        """Build prompt for Claude"""
        
        profile_text = ""
        if user_profile:
            profile_text = f"\n\nUser Profile:\n- Watched: {user_profile.get('total_watched', 0)} movies\n- Favorite genres: {', '.join([g[0] for g in user_profile.get('favorite_genres', [])[:3]])}"
        
        return f"""I need you to re-rank these movie recommendations based on how well they match the user's vibe.

User's Vibe: "{vibe}"{profile_text}

Candidate Movies (pre-ranked by semantic similarity):
{movies_text}

Your task:
1. Understand the FEELING and ATMOSPHERE the user wants (not just genre)
2. Re-rank these movies from best to worst match
3. For each movie, provide a brief explanation (1-2 sentences) of why it matches the vibe
4. Consider cultural context, era, mood, visual style, and emotional tone

Return your response as a JSON array with this exact format:
[
  {{
    "title": "Movie Title",
    "rank": 1,
    "reason": "Brief explanation of why this matches the vibe"
  }},
  ...
]

Important:
- Focus on the VIBE, not just genre matching
- Be specific about what makes each movie fit
- Consider the emotional and aesthetic qualities
- Return ONLY the JSON array, no markdown code blocks, no other text
- Do NOT wrap the JSON in ```json or ``` markers"""
    
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
                title_lower = item['title'].lower()
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


# Global service instance
_service: Optional[ClaudeService] = None


def get_claude_service() -> ClaudeService:
    """Get or create Claude service instance"""
    global _service
    if _service is None:
        _service = ClaudeService()
    return _service

# Made with Bob
