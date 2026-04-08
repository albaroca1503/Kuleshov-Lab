/**
 * API Service for Kuleshov Lab
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types matching backend models
export interface Movie {
  id: number;
  title: string;
  original_title?: string;
  overview?: string;
  release_date?: string;
  genres?: string[];
  poster_url?: string;
  backdrop_url?: string;
  score?: number;
  reason?: string;
}

export interface VibeRequest {
  vibe: string;
  limit?: number;
  filters?: {
    year_min?: number;
    year_max?: number;
    genre?: string;
  };
}

export interface RecommendationResponse {
  vibe: string;
  movies: Movie[];
  total: number;
}

export interface UserStats {
  total_watched: number;
  total_liked: number;
  total_disliked: number;
  favorite_genres: string[];
  watch_time_hours: number;
}

export interface MarkWatchedRequest {
  status: 'watched' | 'liked' | 'disliked';
  rating?: number;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic fetch wrapper with error handling
   */
  private async fetchApi<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API Error (${endpoint}):`, error);
      throw error;
    }
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string }> {
    return this.fetchApi('/health');
  }

  /**
   * Get movie recommendations based on vibe
   */
  async getRecommendationsByVibe(
    request: VibeRequest
  ): Promise<RecommendationResponse> {
    return this.fetchApi('/api/recommend/vibe', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Mark a movie as watched/liked/disliked
   */
  async markMovieWatched(
    movieId: number,
    request: MarkWatchedRequest
  ): Promise<{ success: boolean; message: string }> {
    return this.fetchApi(`/api/movies/${movieId}/watched`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<UserStats> {
    return this.fetchApi('/api/user/stats');
  }

  /**
   * Get list of watched movies
   */
  async getWatchedMovies(): Promise<{ watched: number[]; total: number }> {
    return this.fetchApi('/api/user/watched');
  }
}

// Export singleton instance
export const api = new ApiService();

// Export class for testing
export default ApiService;

// Made with Bob
