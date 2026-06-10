import { useState, useCallback } from 'react';
import { api, Movie, RecommendationResponse, Filters } from '../services/api';
import { FilmStatus } from '../components/FilmCard';

interface UseRecommendationsReturn {
  movies: Movie[];
  loading: boolean;
  error: string | null;
  getRecommendations: (vibe: string, limit?: number, filters?: Filters) => Promise<void>;
  getVaultRecommendations: () => Promise<void>;
  markWatched: (movieId: number, status: FilmStatus) => Promise<void>;
  clearError: () => void;
}

export function useRecommendations(): UseRecommendationsReturn {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResponse = (response: RecommendationResponse) => {
    const sorted = [...response.movies].sort((a, b) => (b.score ?? 0) - (a.score ?? 0));
    setMovies(sorted);
  };

  const getRecommendations = useCallback(async (vibe: string, limit = 10, filters?: Filters) => {
    if (!vibe.trim()) { setError('Please enter a vibe description'); return; }
    setLoading(true);
    setError(null);
    try {
      const response = await api.getRecommendationsByVibe({ vibe, limit, filters });
      handleResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to get recommendations');
    } finally {
      setLoading(false);
    }
  }, []);

  const getVaultRecommendations = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await api.getVaultRecommendations();
      handleResponse(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Your vault is empty — add some films first');
    } finally {
      setLoading(false);
    }
  }, []);

  const markWatched = useCallback(async (movieId: number, status: FilmStatus) => {
    if (status === 'none') return;
    try {
      await api.markMovieWatched(movieId, { status });
    } catch (err) {
      console.error('Error marking movie:', err);
    }
  }, []);

  const clearError = useCallback(() => setError(null), []);

  return { movies, loading, error, getRecommendations, getVaultRecommendations, markWatched, clearError };
}
