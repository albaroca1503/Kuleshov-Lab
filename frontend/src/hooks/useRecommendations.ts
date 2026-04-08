import { useState, useCallback } from 'react';
import { api, Movie, RecommendationResponse } from '../services/api';

interface UseRecommendationsReturn {
  movies: Movie[];
  loading: boolean;
  error: string | null;
  getRecommendations: (vibe: string, limit?: number) => Promise<void>;
  markWatched: (movieId: number, status: 'watched' | 'liked' | 'disliked') => Promise<void>;
  clearError: () => void;
}

export function useRecommendations(): UseRecommendationsReturn {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRecommendations = useCallback(async (vibe: string, limit: number = 10) => {
    if (!vibe.trim()) {
      setError('Please enter a vibe description');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response: RecommendationResponse = await api.getRecommendationsByVibe({
        vibe,
        limit,
      });
      
      setMovies(response.movies);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get recommendations';
      setError(errorMessage);
      console.error('Error getting recommendations:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const markWatched = useCallback(async (
    movieId: number,
    status: 'watched' | 'liked' | 'disliked'
  ) => {
    try {
      await api.markMovieWatched(movieId, { status });
      
      // Remove the movie from the current list
      setMovies(prev => prev.filter(m => m.id !== movieId));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to mark movie';
      setError(errorMessage);
      console.error('Error marking movie:', err);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    movies,
    loading,
    error,
    getRecommendations,
    markWatched,
    clearError,
  };
}

// Made with Bob
