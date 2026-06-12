"""
Local embeddings using Sentence-Transformers
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import Optional
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Service for generating and comparing embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding model
        
        Args:
            model_name: HuggingFace model name (default: all-MiniLM-L6-v2)
                       - Fast and lightweight (80MB)
                       - Good for semantic similarity
        """
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print(f"✅ Model loaded successfully")
    
    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for text
        
        Args:
            text: Input text
            
        Returns:
            Numpy array of embeddings
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of input texts
            
        Returns:
            Numpy array of embeddings (batch_size, embedding_dim)
        """
        return self.model.encode(texts, convert_to_numpy=True)
    
    def to_bytes(self, embedding: np.ndarray) -> bytes:
        """Convert embedding to bytes for storage"""
        return embedding.tobytes()
    
    def from_bytes(self, data: bytes, dtype=np.float32) -> np.ndarray:
        """Convert bytes back to embedding"""
        return np.frombuffer(data, dtype=dtype)
    
    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            a: First embedding
            b: Second embedding
            
        Returns:
            Similarity score (-1 to 1, higher is more similar)
            Returns only positive values (0 to 1) by clipping negatives
        """
        # Normalize vectors
        a_norm = a / np.linalg.norm(a)
        b_norm = b / np.linalg.norm(b)
        
        # Compute cosine similarity (-1 to 1)
        similarity = np.dot(a_norm, b_norm)
        
        # Clip negative values to 0 for better discrimination
        return float(max(0, similarity))
    
    def create_movie_text(self, movie: dict) -> str:
        """
        Create enriched text representation of movie for embedding
        
        Args:
            movie: Movie data dict (with optional credits and keywords)
            
        Returns:
            Combined text for embedding with weighted information
        """
        parts = []
        
        # Title with year (contextual information)
        if movie.get('title'):
            title = movie['title']
            if movie.get('release_date'):
                year = movie['release_date'][:4]
                parts.append(f"{title} ({year})")
            else:
                parts.append(title)
        
        # Overview (MOST IMPORTANT - the core description)
        if movie.get('overview'):
            parts.append(movie['overview'])
        
        # Genres (important for vibe matching)
        if movie.get('genres'):
            if isinstance(movie['genres'], list):
                if movie['genres'] and isinstance(movie['genres'][0], dict):
                    genres = [g['name'] for g in movie['genres']]
                else:
                    genres = movie['genres']
                parts.append(f"Genres: {', '.join(genres)}")
        
        # Keywords/Themes (semantic richness)
        if movie.get('keywords'):
            keywords_data = movie['keywords']
            if isinstance(keywords_data, dict) and 'keywords' in keywords_data:
                keywords = [k['name'] for k in keywords_data['keywords'][:10]]
            elif isinstance(keywords_data, list):
                keywords = [k['name'] if isinstance(k, dict) else k for k in keywords_data[:10]]
            else:
                keywords = []
            
            if keywords:
                parts.append(f"Themes: {', '.join(keywords)}")
        
        # Director (auteur style matters)
        if movie.get('credits'):
            credits = movie['credits']
            if isinstance(credits, dict):
                crew = credits.get('crew', [])
                directors = [c['name'] for c in crew if c.get('job') == 'Director']
                if directors:
                    parts.append(f"Director: {', '.join(directors[:2])}")
                
                # Main cast (star power and acting style)
                cast = credits.get('cast', [])
                if cast:
                    actors = [c['name'] for c in cast[:5]]
                    parts.append(f"Starring: {', '.join(actors)}")
        
        return " | ".join(parts)
    
    def expand_vibe(self, vibe: str) -> str:
        """
        Expand vibe description with related terms for better matching
        
        Args:
            vibe: Original vibe description
            
        Returns:
            Expanded vibe with synonyms and related concepts
        """
        # Lowercase for matching
        vibe_lower = vibe.lower()
        
        # Cinematic term expansions
        expansions = {
            # Decades
            '80s': 'eighties 1980s retro',
            '90s': 'nineties 1990s',
            '70s': 'seventies 1970s',
            '60s': 'sixties 1960s',
            
            # Visual styles
            'neon': 'neon-lit cyberpunk futuristic glowing',
            'dark': 'noir shadowy gritty atmospheric',
            'colorful': 'vibrant vivid bright saturated',
            'black and white': 'monochrome noir classic',
            
            # Moods
            'thriller': 'suspense tension mystery psychological',
            'comedy': 'funny humorous hilarious laugh',
            'horror': 'scary terrifying frightening creepy',
            'romantic': 'love romance relationship emotional',
            'action': 'explosive intense adrenaline fast-paced',
            'drama': 'emotional serious character-driven',
            
            # Themes
            'dystopian': 'post-apocalyptic bleak future totalitarian',
            'space': 'sci-fi science-fiction cosmic interstellar',
            'crime': 'criminal gangster heist underworld',
            'war': 'military combat battlefield soldier',
            'western': 'cowboy frontier wild-west',
            
            # Tones
            'quirky': 'offbeat eccentric unconventional unique',
            'epic': 'grand sweeping spectacular monumental',
            'intimate': 'personal small-scale character-focused',
            'surreal': 'dreamlike bizarre abstract strange',
        }
        
        expanded_parts = [vibe]
        
        # Add relevant expansions
        for key, expansion in expansions.items():
            if key in vibe_lower:
                expanded_parts.append(expansion)
        
        return ' '.join(expanded_parts)
    
    def generate_movie_embedding(self, movie: dict) -> np.ndarray:
        """
        Generate embedding for a movie
        
        Args:
            movie: Movie data dict
            
        Returns:
            Movie embedding
        """
        text = self.create_movie_text(movie)
        return self.encode(text)


# Global service instance
_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service instance"""
    global _service
    if _service is None:
        _service = EmbeddingService(settings.embedding_model)
    return _service

