import React, { useState } from 'react';
import { Clapperboard, Sparkles, Loader2, X, AlertCircle, Star } from 'lucide-react';
import { AnimatePresence } from 'motion/react';
import { Movie, Filters } from '../services/api';
import { FilmCard, FilmStatus } from './FilmCard';
import { FilmModal } from './FilmModal';

const STATUS_BAR = [
  ['SYSTEM_STATUS', 'OPERATIONAL'],
  ['ENGINE_VERSION', '2.0.4_NOIR'],
  ['STREAMING_FILTERS', 'ACTIVE'],
  ['CURATION_MODE', 'CINEMATIC_ARCHIVE'],
  ['LATENCY', '12MS'],
];

const VIBE_PROMPTS = [
  'A neon-drenched 80s thriller',
  'A melancholic rainy afternoon in Tokyo',
  'Gothic horror in a sun-bleached desert',
  'Paranoid surveillance, cold and fractured',
  'A dream you cannot wake up from',
];

const STREAMING_SERVICES = [
  { id: 8,    name: 'Netflix',    logo: '/t2yyOv40HZeVlLjYsCsPHnWLk4W.jpg' },
  { id: 119,  name: 'Prime',      logo: '/68MNrwlkpF7WnmNPXLah69CR5cb.jpg' },
  { id: 337,  name: 'Disney+',    logo: '/7rwgEs15tFwyR9NPQ5vpzxTj19Q.jpg' },
  { id: 350,  name: 'Apple TV+',  logo: '/6uhKBfmtzFqOcLousHwZuzcrScK.jpg' },
  { id: 11,   name: 'MUBI',       logo: '/x570VpH2C9EKDf1riP83rYc5dnL.jpg' },
  { id: 63,   name: 'Filmin',     logo: '/kO2SWXvDCHAquaUuTJBuZkTBAuU.jpg' },
  { id: 1899, name: 'Max',        logo: '/jbe4gVSfRlbPTdESXhEKpornsfu.jpg' },
  { id: 531,  name: 'Paramount+', logo: '/h5DcR0J2EESLitnhR8xLG1QymTE.jpg' },
  { id: 149,  name: 'Movistar+',  logo: '/f6TRLB3H4jDpFEZ0z2KWSSvu1SB.jpg' },
];

export function EngineView({
  onSearch,
  onVaultSearch,
  loading,
  error,
  onClearError,
  movies,
  statuses,
  onSetStatus,
}: {
  onSearch: (vibe: string, filters?: Filters) => Promise<void>;
  onVaultSearch: (filters?: Filters) => Promise<void>;
  loading: boolean;
  error: string | null;
  onClearError: () => void;
  movies: Movie[];
  statuses: Record<number, FilmStatus>;
  onSetStatus: (id: number, s: FilmStatus) => void;
}) {
  const [vibe, setVibe] = useState('');
  const [activePlatforms, setActivePlatforms] = useState<number[]>([]);
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [vaultLoading, setVaultLoading] = useState(false);

  const togglePlatform = (id: number) =>
    setActivePlatforms(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);

  const buildFilters = (): Filters | undefined =>
    activePlatforms.length ? { streaming_service_ids: activePlatforms } : undefined;

  const handleSearch = (v: string) => {
    if (!v.trim()) return;
    setVibe(v);
    onSearch(v, buildFilters());
  };

  const handleVaultRecommend = async () => {
    setVaultLoading(true);
    try { await onVaultSearch(buildFilters()); } finally { setVaultLoading(false); }
  };

  const isLoading = loading || vaultLoading;

  return (
    <div>
      {/* terminal status bar */}
      <div className="border-b border-border/60 bg-card/40">
        <div className="no-scrollbar mx-auto flex max-w-[1600px] gap-6 overflow-x-auto px-4 py-2.5 sm:px-6 lg:px-10">
          {STATUS_BAR.map(([k, v]) => (
            <span key={k} className="whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              {k}: <span className="text-amber">{isLoading && k === 'SYSTEM_STATUS' ? 'PROCESSING' : v}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-10">
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 p-4 flex items-center gap-3">
            <AlertCircle className="size-5 text-red-500 shrink-0" />
            <p className="font-mono text-sm text-red-500">{error}</p>
            <button onClick={onClearError} className="ml-auto shrink-0"><X className="size-4 text-red-500" /></button>
          </div>
        )}

        {/* prompt heading */}
        <div className="flex items-start justify-between gap-4">
          <h1 className="font-display text-3xl font-bold uppercase italic tracking-tight text-amber sm:text-4xl lg:text-5xl">
            Describe the vibe...
          </h1>
          {isLoading
            ? <Loader2 className="size-7 shrink-0 text-primary animate-spin sm:size-8" />
            : <Clapperboard className="size-7 shrink-0 text-primary sm:size-8" />}
        </div>

        {/* vibe input */}
        <div className="mt-5 flex items-center gap-3 border-b border-border/70 pb-3 transition-colors focus-within:border-primary">
          <Sparkles className="size-4 text-primary" />
          <input
            value={vibe}
            onChange={(e) => setVibe(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') handleSearch(vibe); }}
            placeholder="e.g. a rain-soaked synth thriller at 3am..."
            disabled={isLoading}
            className="w-full bg-transparent font-mono text-sm text-foreground placeholder:text-muted-foreground/70 focus:outline-none disabled:opacity-50"
          />
        </div>

        {/* vibe chips + vault button */}
        <div className="mt-4 flex flex-wrap items-center gap-2">
          {VIBE_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              disabled={isLoading}
              onClick={() => handleSearch(p)}
              className={`border px-3 py-1.5 text-left font-mono text-[11px] uppercase tracking-[0.1em] transition-colors disabled:opacity-50 ${
                vibe === p
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border/70 text-amber/90 hover:border-primary/60 hover:text-primary'
              }`}
            >
              &quot;{p}&quot;
            </button>
          ))}
          <button
            type="button"
            disabled={isLoading}
            onClick={handleVaultRecommend}
            className="ml-auto flex items-center gap-2 rounded-full border border-primary/60 bg-primary/10 px-5 py-2 font-mono text-[11px] uppercase tracking-[0.1em] text-primary transition-colors hover:bg-primary/20 disabled:opacity-50"
          >
            {vaultLoading
              ? <Loader2 className="size-4 animate-spin" />
              : <Star className="size-4 fill-primary/60 stroke-primary" />}
            Surprise Me
          </button>
        </div>

        {/* platform filter — icons */}
        <div className="mt-7 flex flex-wrap items-center gap-x-4 gap-y-3 border-y border-border/50 py-4">
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground shrink-0">
            Where to watch
          </span>
          <div className="flex flex-wrap gap-2">
            {STREAMING_SERVICES.map((svc) => {
              const active = activePlatforms.includes(svc.id);
              return (
                <button
                  key={svc.id}
                  onClick={() => togglePlatform(svc.id)}
                  title={svc.name}
                  className={`flex items-center border p-1.5 transition-all ${
                    active ? 'border-primary bg-primary/10' : 'border-border/70 hover:border-primary/60'
                  }`}
                >
                  <img
                    src={`https://image.tmdb.org/t/p/w92${svc.logo}`}
                    alt={svc.name}
                    className={`size-7 rounded object-cover transition-opacity ${active ? 'opacity-100' : 'opacity-40'}`}
                  />
                </button>
              );
            })}
          </div>
          {activePlatforms.length > 0 && (
            <button
              type="button"
              onClick={() => setActivePlatforms([])}
              className="ml-auto font-mono text-[10px] uppercase tracking-[0.12em] text-muted-foreground hover:text-foreground transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* results header */}
        <p className="mt-7 font-mono text-xs uppercase tracking-[0.2em] text-primary">
          Found {movies.length} match{movies.length === 1 ? '' : 'es'}
        </p>

        {/* grid */}
        {movies.length === 0 ? (
          <div className="mt-10 border border-dashed border-border/60 py-20 text-center font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
            No signals match those filters
          </div>
        ) : (
          <div className="mt-5 grid grid-cols-2 gap-x-5 gap-y-9 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {movies.map((movie) => (
              <FilmCard
                key={String(movie.id)}
                movie={movie}
                status={statuses[movie.id] ?? 'none'}
                onOpen={() => setSelectedMovie(movie)}
                onSetStatus={(s) => onSetStatus(movie.id, s)}
              />
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {selectedMovie && (
          <FilmModal
            movie={selectedMovie}
            status={statuses[selectedMovie.id] ?? 'none'}
            onClose={() => setSelectedMovie(null)}
            onSetStatus={(s) => { onSetStatus(selectedMovie.id, s); }}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
