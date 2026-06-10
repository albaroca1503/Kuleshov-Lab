import React, { useState, useEffect, useMemo } from 'react';
import { Download, Loader2 } from 'lucide-react';
import { AnimatePresence } from 'motion/react';
import { api, WatchedMovieItem, UserStats, Movie } from '../services/api';
import { FilmModal } from './FilmModal';
import { FilmStatus } from './FilmCard';

const STATUS_LABEL: Record<string, string> = {
  liked: 'LIKED',
  watched: 'ARCHIVED',
  disliked: 'REJECTED',
};

function toFilmStatus(s: string): FilmStatus {
  if (s === 'liked' || s === 'watched' || s === 'disliked') return s;
  return 'none';
}

function toMovie(item: WatchedMovieItem): Movie {
  return {
    id: item.id,
    title: item.title,
    release_date: item.release_date,
    genres: item.genres,
    poster_url: item.poster_url,
  };
}

export function VaultView() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [movies, setMovies] = useState<WatchedMovieItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<WatchedMovieItem | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<FilmStatus>('none');

  useEffect(() => {
    Promise.all([api.getUserStats(), api.getWatchedMovieDetails()])
      .then(([s, m]) => { setStats(s); setMovies(m.movies); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selected) setSelectedStatus(toFilmStatus(selected.status));
  }, [selected]);

  const palette = useMemo(() => {
    const counts = new Map<string, number>();
    movies.forEach(m => (m.genres ?? []).forEach(g => counts.set(g, (counts.get(g) ?? 0) + 1)));
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([genre], i) => ({
        genre,
        color: ['bg-primary', 'bg-amber', 'bg-primary/60', 'bg-muted-foreground/50', 'bg-muted-foreground/30'][i],
      }));
  }, [movies]);

  const syncIndex = stats && (stats.total_liked + stats.total_disliked) > 0
    ? Math.round((stats.total_liked / (stats.total_liked + stats.total_disliked)) * 100)
    : 0;

  const totalCatalog = stats ? stats.total_watched + stats.total_liked + stats.total_disliked : 0;

  const handleStatusChange = async (s: FilmStatus) => {
    if (!selected) return;
    setSelectedStatus(s);
    if (s !== 'none') {
      try {
        await api.markMovieWatched(selected.id, { status: s, movie_title: selected.title });
        setMovies(prev => prev.map(m => m.id === selected.id ? { ...m, status: s } : m));
      } catch (err) { console.error(err); }
    }
  };

  return (
    <div className="mx-auto max-w-[1400px] px-5 py-10 md:px-10 md:py-14">
      {/* Hero */}
      <div className="flex flex-col gap-8 md:flex-row md:items-end md:justify-between">
        <div className="max-w-xl">
          <h1 className="font-display text-5xl uppercase italic tracking-tight text-foreground md:text-7xl">
            The Vault
          </h1>
          <p className="mt-4 max-w-md font-sans text-base leading-relaxed text-amber/90">
            A curated repository of cinematic experiences. Your personal chronology of sight and sound, indexed for the discerning eye.
          </p>
        </div>
        <button className="inline-flex items-center gap-2 bg-primary px-6 py-3 font-mono text-xs uppercase tracking-[0.2em] text-primary-foreground transition-colors hover:bg-primary/90">
          <Download className="size-4" />
          Export Dossier
        </button>
      </div>

      {/* Stats */}
      <div className="mt-10 grid grid-cols-1 border border-border/60 bg-card/40 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Archived">
          <span className="font-display text-5xl italic text-foreground">{movies.length}</span>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Films Logged</span>
        </StatCard>
        <StatCard label="Mood Palette">
          {palette.length > 0 ? (
            <>
              <div className="flex h-12 gap-1.5">
                {palette.map(p => <div key={p.genre} className={`flex-1 ${p.color}`} />)}
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {palette.map(p => (
                  <span key={p.genre} className="font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
                    {p.genre}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="flex h-12 gap-1.5 opacity-20">
              <div className="flex-1 bg-primary" /><div className="flex-1 bg-amber" /><div className="flex-1 bg-muted-foreground" />
            </div>
          )}
        </StatCard>
        <StatCard label="Sync Index">
          <span className="font-display text-5xl italic text-foreground">{syncIndex}%</span>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Taste Coherence</span>
        </StatCard>
        <StatCard label="Catalog Count">
          <span className="font-display text-5xl italic text-foreground">{totalCatalog}</span>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">Active Acquisitions</span>
        </StatCard>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="size-8 text-primary animate-spin" />
        </div>
      ) : movies.length === 0 ? (
        <div className="mt-10 border border-dashed border-border/60 py-20 text-center font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Your vault is empty — start by recommending films in the Engine
        </div>
      ) : (
        <div className="mt-10 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          {movies.map((movie) => (
            <button
              key={movie.id}
              onClick={() => setSelected(movie)}
              className="group relative overflow-hidden border border-border/40 text-left transition-colors hover:border-primary/60"
            >
              <div className="relative aspect-[2/3] w-full overflow-hidden">
                <img
                  src={movie.poster_url || ''}
                  alt={`Poster for ${movie.title}`}
                  referrerPolicy="no-referrer"
                  className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-background/10 to-transparent" />
                <span className={`absolute right-2 top-2 border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.15em] bg-background/80 ${
                    movie.status === 'disliked'
                      ? 'border-muted-foreground/40 text-muted-foreground'
                      : 'border-primary/50 text-primary'
                  }`}>
                    {STATUS_LABEL[movie.status] ?? movie.status.toUpperCase()}
                  </span>
              </div>
              <div className="absolute bottom-0 left-0 right-0 p-3">
                <h3 className="font-display text-sm uppercase italic leading-tight text-foreground">{movie.title}</h3>
                <span className="font-mono text-[10px] tracking-[0.15em] text-amber">
                  {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      <AnimatePresence>
        {selected && (
          <FilmModal
            movie={toMovie(selected)}
            status={selectedStatus}
            onClose={() => setSelected(null)}
            onSetStatus={handleStatusChange}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

function StatCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-4 border-r border-border/60 px-6 py-7 last:border-r-0">
      <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-muted-foreground">{label}</span>
      {children}
    </div>
  );
}
