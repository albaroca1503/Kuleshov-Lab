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
            Similarity score (0-1, higher is more similar)
        """
        # Normalize vectors
        a_norm = a / np.linalg.norm(a)
        b_norm = b / np.linalg.norm(b)
        
        # Compute cosine similarity
        similarity = np.dot(a_norm, b_norm)
        
        # Convert to 0-1 range
        return float((similarity + 1) / 2)
    
    def create_movie_text(self, movie: dict) -> str:
        """
        Create text representation of movie for embedding
        
        Args:
            movie: Movie data dict
            
        Returns:
            Combined text for embedding
        """
        parts = []
        
        # Title
        if movie.get('title'):
            parts.append(movie['title'])
        
        # Overview
        if movie.get('overview'):
            parts.append(movie['overview'])
        
        # Genres
        if movie.get('genres'):
            if isinstance(movie['genres'], list):
                if isinstance(movie['genres'][0], dict):
                    genres = [g['name'] for g in movie['genres']]
                else:
                    genres = movie['genres']
                parts.append(f"Genres: {', '.join(genres)}")
        
        return " | ".join(parts)
    
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

# Made with Bob
