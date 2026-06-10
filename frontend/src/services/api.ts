/**
 * API Service for Kuleshov Lab
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

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

export interface Filters {
  year_min?: number;
  year_max?: number;
  year?: number;
  genres?: string[];
  streaming_service_ids?: number[];
}

export interface VibeRequest {
  vibe: string;
  limit?: number;
  filters?: Filters;
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
  movie_title?: string;
}

export interface WatchedMovieItem {
  id: number;
  title: string;
  release_date?: string;
  genres?: string[];
  poster_url?: string;
  status: 'watched' | 'liked' | 'disliked';
  watched_at: string;
}

export interface StreamingProvider {
  id: number;
  name: string;
  logo_url?: string;
}

export interface MovieReview {
  author: string;
  content: string;
  url: string;
}

export interface MovieDetails {
  id: number;
  title: string;
  tagline?: string;
  runtime?: number;
  vote_average?: number;
  vote_count?: number;
  director?: string;
  cast: string[];
  imdb_id?: string;
  streaming: {
    flatrate: StreamingProvider[];
    rent: StreamingProvider[];
    buy: StreamingProvider[];
  };
  reviews: MovieReview[];
  trailer_key?: string;
}

export interface UserSettings {
  country_code: string;
  streaming_service_ids: number[];
}

export interface SignalData {
  movie: Movie;
  signal_reason: string;
  context: string;
}

class ApiService {
  private readonly baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    try {
      const response = await fetch(url, {
        ...options,
        headers: { 'Content-Type': 'application/json', ...options.headers },
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

  async healthCheck(): Promise<{ status: string }> {
    return this.fetchApi('/health');
  }

  async getRecommendationsByVibe(request: VibeRequest): Promise<RecommendationResponse> {
    return this.fetchApi('/api/recommend/vibe', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getVaultRecommendations(): Promise<RecommendationResponse> {
    return this.fetchApi('/api/recommend/vault', { method: 'POST', body: '{}' });
  }

  async getSignal(): Promise<SignalData> {
    return this.fetchApi('/api/recommend/signal');
  }

  async markMovieWatched(
    movieId: number,
    request: MarkWatchedRequest
  ): Promise<{ success: boolean; message: string }> {
    return this.fetchApi(`/api/movies/${movieId}/watched`, {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getUserStats(): Promise<UserStats> {
    return this.fetchApi('/api/user/stats');
  }

  async getWatchedMovies(): Promise<{ watched: number[]; total: number }> {
    return this.fetchApi('/api/user/watched');
  }

  async getWatchedMovieDetails(): Promise<{ movies: WatchedMovieItem[]; total: number }> {
    return this.fetchApi('/api/user/watched-movies');
  }

  async getMovieDetails(movieId: number): Promise<MovieDetails> {
    return this.fetchApi(`/api/movies/${movieId}/details`);
  }

  async getUserSettings(): Promise<UserSettings> {
    return this.fetchApi('/api/user/settings');
  }

  async updateUserSettings(settings: UserSettings): Promise<{ success: boolean }> {
    return this.fetchApi('/api/user/settings', {
      method: 'PUT',
      body: JSON.stringify(settings),
    });
  }
}

export const api = new ApiService();
export default ApiService;
