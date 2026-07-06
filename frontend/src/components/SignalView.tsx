import React, { useState, useEffect } from 'react';
import { Loader2, RefreshCw, Heart, Archive, X, ExternalLink, Star, AlertCircle } from 'lucide-react';
import { api, SignalData } from '../services/api';
import { FilmStatus } from './FilmCard';
import { MatchBar } from './MatchMeter';

function SignalContext({ context }: Readonly<{ context: string }>) {
  const isHeadlines = context.startsWith("Today's headlines:");

  if (isHeadlines) {
    const lines = context
      .replace(/^Today's headlines:\n/, '')
      .split('\n')
      .filter(l => l.startsWith('- '))
      .map(l => l.slice(2).trim())
      .filter(Boolean);

    return (
      <div className="mt-5 border border-border/50 bg-card/30">
        <div className="border-b border-border/50 px-4 py-2 flex items-center gap-3">
          <span className="font-mono text-[9px] uppercase tracking-[0.25em] text-amber/80">
            Signal Context
          </span>
          <span className="h-px flex-1 bg-border/40" />
          <span className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground/50">
            Today's Headlines
          </span>
        </div>
        <ul className="divide-y divide-border/30">
          {lines.map((headline, i) => (
            <li key={headline} className="flex items-start gap-4 px-4 py-2.5">
              <span className="font-mono text-[10px] tabular-nums text-primary/40 mt-px shrink-0 w-5">
                {String(i + 1).padStart(2, '0')}
              </span>
              <p className="font-mono text-[11px] leading-snug text-muted-foreground">
                {headline}
              </p>
            </li>
          ))}
        </ul>
      </div>
    );
  }

  return (
    <p className="mt-2 font-mono text-[11px] uppercase tracking-[0.16em] text-muted-foreground/70">
      {context}
    </p>
  );
}

const META_BAR = [
  ['SIGNAL', 'ACTIVE'],
  ['SOURCE', 'VAULT + CONTEXT'],
  ['MODE', 'EDITORIAL_PICK'],
  ['REFRESH', 'ON_DEMAND'],
];

export function SignalView({
  onSetStatus,
}: {
  onSetStatus: (id: number, s: FilmStatus) => void;
}) {
  const [signal, setSignal] = useState<SignalData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<FilmStatus>('none');

  const fetchSignal = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSignal();
      setSignal(data);
      setStatus('none');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to generate signal';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSignal(); }, []);

  const handleStatus = (s: FilmStatus) => {
    if (!signal) return;
    const next: FilmStatus = status === s ? 'none' : s;
    setStatus(next);
    onSetStatus(signal.movie.id, next);
    if (next !== 'none') {
      api.markMovieWatched(signal.movie.id, { status: next, movie_title: signal.movie.title })
        .catch(console.error);
    }
  };

  const movie = signal?.movie;
  const year = movie?.release_date ? new Date(movie.release_date).getFullYear() : null;
  const matchPct = movie?.score != null ? Math.round(movie.score * 100) : null;
  const letterboxdSlug = movie ? movie.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') : '';

  return (
    <div>
      {/* status bar */}
      <div className="border-b border-border/60 bg-card/40">
        <div className="no-scrollbar mx-auto flex max-w-[1600px] gap-6 overflow-x-auto px-4 py-2.5 sm:px-6 lg:px-10">
          {META_BAR.map(([k, v]) => (
            <span key={k} className="whitespace-nowrap font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
              {k}: <span className="text-amber">{loading && k === 'SIGNAL' ? 'PROCESSING' : v}</span>
            </span>
          ))}
        </div>
      </div>

      <div className="mx-auto max-w-[1600px] px-4 py-8 sm:px-6 lg:px-10">
        {/* header */}
        <div className="mb-8">
          <div className="flex items-start justify-between gap-4">
            <h1 className="font-display text-3xl font-bold uppercase italic tracking-tight text-amber sm:text-4xl lg:text-5xl">
              Tonight's Signal
            </h1>
            <button
              onClick={fetchSignal}
              disabled={loading}
              aria-label="Regenerate"
              className="flex items-center gap-2 border border-border/70 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground transition-colors hover:border-primary hover:text-primary disabled:opacity-40"
            >
              <RefreshCw className={`size-3.5 ${loading ? 'animate-spin' : ''}`} />
              Regenerate
            </button>
          </div>
          {signal?.context && <SignalContext context={signal.context} />}
        </div>

        {/* error */}
        {error && (
          <div className="border border-dashed border-border/60 py-20 text-center">
            <AlertCircle className="size-8 text-muted-foreground mx-auto mb-3" />
            <p className="font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground mb-2">{error}</p>
            <p className="font-mono text-[10px] text-muted-foreground/60">Add films to your vault so the Signal can curate for you</p>
          </div>
        )}

        {/* loading skeleton */}
        {loading && !signal && (
          <div className="flex flex-col items-center justify-center py-32 gap-4">
            <Loader2 className="size-8 text-primary animate-spin" />
            <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">
              Curating your signal…
            </p>
          </div>
        )}

        {/* film feature */}
        {movie && (
          <div className="grid lg:grid-cols-[1fr_2fr] gap-8 lg:gap-12">
            {/* poster */}
            <div className="relative aspect-[2/3] w-full max-w-sm mx-auto lg:mx-0 overflow-hidden border border-border/60 noir-grain">
              <img
                src={movie.poster_url || ''}
                alt={`Poster for ${movie.title}`}
                referrerPolicy="no-referrer"
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background/60 via-transparent to-transparent" />
              {matchPct != null && matchPct > 0 && (
                <span className="absolute left-3 top-3 bg-background/80 px-2 py-1 font-mono text-[10px] tabular-nums text-primary backdrop-blur-sm">
                  {matchPct}% MATCH
                </span>
              )}
            </div>

            {/* details */}
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="font-display text-4xl font-bold uppercase italic leading-none tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                  {movie.title}
                </h2>
                <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                  {year && <span className="text-amber">{year}</span>}
                  {movie.genres?.slice(0, 3).map(g => <span key={g}>{g}</span>)}
                </div>
                {movie.genres && movie.genres.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {movie.genres.map(g => (
                      <span key={g} className="border border-border/70 px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em] text-muted-foreground">
                        {g}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* match bar */}
              {matchPct != null && matchPct > 0 && (
                <div>
                  <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground mb-1.5">
                    <span>Match</span>
                    <span className="text-primary">{matchPct}%</span>
                  </div>
                  <MatchBar value={matchPct} />
                </div>
              )}

              {/* signal reason */}
              {signal?.signal_reason && (
                <div className="border-l-2 border-primary pl-5">
                  <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-primary/60 mb-2">Why this film, tonight</p>
                  <p className="font-sans text-base leading-relaxed text-foreground/90 italic">
                    {signal.signal_reason}
                  </p>
                </div>
              )}

              {/* overview */}
              {movie.overview && (
                <div>
                  <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-muted-foreground mb-2">Synopsis</p>
                  <p className="font-sans text-sm leading-relaxed text-foreground/80">{movie.overview}</p>
                </div>
              )}

              {/* actions */}
              <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-border/50">
                <button
                  onClick={() => handleStatus('liked')}
                  className={`flex items-center gap-1.5 border px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${
                    status === 'liked'
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border/70 text-muted-foreground hover:border-primary hover:text-primary'
                  }`}
                >
                  <Heart className={`size-3.5 ${status === 'liked' ? 'fill-current' : ''}`} />
                  {status === 'liked' ? 'Liked' : 'Like'}
                </button>
                <button
                  onClick={() => handleStatus('watched')}
                  className={`flex items-center gap-1.5 border px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${
                    status === 'watched'
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border/70 text-muted-foreground hover:border-primary hover:text-primary'
                  }`}
                >
                  <Archive className="size-3.5" />
                  {status === 'watched' ? 'Archived' : 'Archive'}
                </button>
                <button
                  onClick={() => handleStatus('disliked')}
                  className={`flex items-center gap-1.5 border px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.14em] transition-colors ${
                    status === 'disliked'
                      ? 'border-muted-foreground/60 bg-muted text-foreground'
                      : 'border-border/70 text-muted-foreground hover:border-muted-foreground hover:text-foreground'
                  }`}
                >
                  <X className="size-3.5" />
                  Skip
                </button>
                <a
                  href={`https://letterboxd.com/film/${letterboxdSlug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ml-auto flex items-center gap-1.5 border border-border/70 px-3 py-2.5 font-mono text-[10px] uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-primary hover:text-primary"
                >
                  Letterboxd <ExternalLink className="size-3" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
