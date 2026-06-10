import React, { useEffect, useState } from 'react';
import { X, ExternalLink, Heart, Archive, Star, Play, Check } from 'lucide-react';
import { Movie, MovieDetails, UserSettings, api } from '../services/api';
import { FilmStatus } from './FilmCard';

export function FilmModal({
  movie,
  status,
  onClose,
  onSetStatus,
}: {
  movie: Movie | null;
  status: FilmStatus;
  onClose: () => void;
  onSetStatus: (s: FilmStatus) => void;
}) {
  const [details, setDetails] = useState<MovieDetails | null>(null);
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);

  useEffect(() => {
    if (!movie) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [movie, onClose]);

  useEffect(() => {
    if (!movie) return;
    setDetails(null);
    Promise.all([api.getMovieDetails(movie.id), api.getUserSettings()])
      .then(([d, s]) => { setDetails(d); setUserSettings(s); })
      .catch(() => {});
  }, [movie?.id]);

  if (!movie) return null;

  const toggle = (s: FilmStatus) => onSetStatus(status === s ? 'none' : s);

  const year = movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';
  const runtime = details?.runtime ? `${Math.floor(details.runtime / 60)}h ${details.runtime % 60}m` : null;
  const imdbUrl = details?.imdb_id ? `https://www.imdb.com/title/${details.imdb_id}` : null;
  const letterboxdSlug = movie.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const letterboxdUrl = `https://letterboxd.com/film/${letterboxdSlug}`;

  const subscribedIds = new Set(userSettings?.streaming_service_ids ?? []);
  const subscribed = details?.streaming.flatrate.filter(p => subscribedIds.has(p.id)) ?? [];
  const other = details?.streaming.flatrate.filter(p => !subscribedIds.has(p.id)) ?? [];
  const matchPct = Math.round((movie.score ?? 0) * 100);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-background/85 p-0 backdrop-blur-sm sm:p-6 lg:p-10"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`${movie.title} details`}
    >
      <div
        className="relative my-auto w-full max-w-4xl border border-border/70 bg-card noir-grain"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 z-20 flex size-9 items-center justify-center border border-border/60 bg-background/70 text-foreground backdrop-blur-sm transition-colors hover:border-primary hover:text-primary"
        >
          <X className="size-4" />
        </button>

        {/* backdrop */}
        <div className="relative h-48 w-full overflow-hidden sm:h-64">
          <img
            src={movie.backdrop_url || movie.poster_url || ''}
            alt=""
            referrerPolicy="no-referrer"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-card via-card/50 to-card/10" />
        </div>

        <div className="relative -mt-24 px-5 pb-8 sm:px-8">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-end">
            <div className="relative aspect-[2/3] w-28 shrink-0 overflow-hidden border border-border/70 shadow-2xl sm:w-36">
              <img
                src={movie.poster_url || ''}
                alt={`Poster for ${movie.title}`}
                referrerPolicy="no-referrer"
                className="w-full h-full object-cover"
              />
            </div>
            <div className="flex flex-col gap-3 pb-1">
              <h2 className="font-display text-3xl font-bold uppercase italic leading-none tracking-tight text-foreground sm:text-4xl">
                {movie.title}
              </h2>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 font-mono text-xs uppercase tracking-[0.12em] text-muted-foreground">
                <span className="text-amber">{year}</span>
                {runtime && <span>{runtime}</span>}
                {details?.director && <span>{details.director}</span>}
                {matchPct > 0 && <span className="text-primary">{matchPct}% match</span>}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {movie.genres?.map((g) => (
                  <span key={g} className="border border-border/70 px-2 py-0.5 font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                    {g}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* rating + actions */}
          <div className="mt-6 flex flex-wrap items-center gap-3">
            {details?.vote_average != null && (
              <span className="flex items-baseline gap-1 font-display text-2xl font-bold text-primary">
                <Star className="size-4 translate-y-0.5 fill-current" />
                {details.vote_average.toFixed(1)}
                <span className="font-mono text-xs text-muted-foreground">/10</span>
              </span>
            )}
            <div className="ml-auto flex flex-wrap gap-2">
              <ActionBtn active={status === 'liked'} onClick={() => toggle('liked')}>
                <Heart className={`size-3.5 ${status === 'liked' ? 'fill-current' : ''}`} />
                {status === 'liked' ? 'Liked' : 'Like'}
              </ActionBtn>
              <ActionBtn active={status === 'watched'} onClick={() => toggle('watched')}>
                <Archive className="size-3.5" />
                {status === 'watched' ? 'Archived' : 'Archive'}
              </ActionBtn>
              {details?.trailer_key && (
                <a
                  href={`https://www.youtube.com/watch?v=${details.trailer_key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 border border-primary/60 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.14em] text-primary transition-colors hover:bg-primary/10"
                >
                  <Play className="size-3 fill-current" />
                  Trailer
                </a>
              )}
              {imdbUrl && (
                <a href={imdbUrl} target="_blank" rel="noopener noreferrer"
                  className="flex items-center gap-1.5 border border-border/70 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-primary hover:text-primary">
                  IMDb <ExternalLink className="size-3" />
                </a>
              )}
              <a href={letterboxdUrl} target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 border border-border/70 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.14em] text-muted-foreground transition-colors hover:border-primary hover:text-primary">
                Letterboxd <ExternalLink className="size-3" />
              </a>
            </div>
          </div>

          {/* why this film */}
          {movie.reason && (
            <Section title="Why this film">
              <p className="border-l-2 border-primary pl-4 font-mono text-sm italic leading-relaxed text-primary/90">
                &quot;{movie.reason}&quot;
              </p>
            </Section>
          )}

          {/* where to watch */}
          {(subscribed.length > 0 || other.length > 0) && (
            <Section title="Where to watch">
              <div className="flex flex-wrap gap-2">
                {subscribed.map((p) => (
                  <span key={p.id} className="flex items-center gap-1.5 border border-primary/60 bg-primary/10 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.12em] text-primary">
                    <Check className="size-3" />
                    {p.name}
                  </span>
                ))}
                {other.map((p) => (
                  <span key={p.id} className="flex items-center gap-1.5 border border-border/70 px-3 py-1.5 font-mono text-xs uppercase tracking-[0.12em] text-muted-foreground">
                    <Play className="size-3" />
                    {p.name}
                  </span>
                ))}
              </div>
              {subscribed.length === 0 && other.length > 0 && (
                <p className="mt-2 font-mono text-xs uppercase tracking-[0.1em] text-muted-foreground">
                  Not on your subscriptions — available to rent or on other platforms
                </p>
              )}
            </Section>
          )}

          {/* synopsis */}
          {movie.overview && (
            <Section title="Synopsis">
              <p className="font-sans text-[15px] leading-relaxed text-foreground/90">{movie.overview}</p>
            </Section>
          )}

          {/* cast */}
          {details?.cast && details.cast.length > 0 && (
            <Section title="Cast">
              <p className="font-mono text-sm text-muted-foreground">{details.cast.join('  ·  ')}</p>
            </Section>
          )}

          {/* press */}
          {details?.reviews && details.reviews.length > 0 && (
            <Section title="Press">
              <div className="flex flex-col gap-4">
                {details.reviews.slice(0, 3).map((r, i) => (
                  <blockquote key={i} className="font-sans">
                    <p className="text-sm italic leading-relaxed text-foreground/80">
                      &quot;{r.content.slice(0, 200)}{r.content.length > 200 ? '…' : ''}&quot;
                    </p>
                    <footer className="mt-1 font-mono text-xs uppercase tracking-[0.16em] text-amber">
                      — {r.author}
                    </footer>
                  </blockquote>
                ))}
              </div>
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-7">
      <h3 className="mb-3 font-mono text-xs uppercase tracking-[0.24em] text-muted-foreground">{title}</h3>
      {children}
    </section>
  );
}

function ActionBtn({ children, active, onClick }: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 border px-3 py-1.5 font-mono text-xs uppercase tracking-[0.14em] transition-colors ${
        active
          ? 'border-primary bg-primary text-primary-foreground'
          : 'border-border/70 text-muted-foreground hover:border-primary hover:text-primary'
      }`}
    >
      {children}
    </button>
  );
}
