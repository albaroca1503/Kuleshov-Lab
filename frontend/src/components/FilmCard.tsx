import React from 'react';
import { Heart, Archive, X, ArrowRight } from 'lucide-react';
import { Movie } from '../services/api';
import { MatchBar } from './MatchMeter';

export type FilmStatus = 'liked' | 'watched' | 'disliked' | 'none';

const STATUS_LABEL: Record<Exclude<FilmStatus, 'none'>, string> = {
  liked: 'Liked',
  watched: 'Archived',
  disliked: 'Rejected',
};

export function FilmCard({
  movie,
  status,
  onOpen,
  onSetStatus,
}: {
  movie: Movie;
  status: FilmStatus;
  onOpen: () => void;
  onSetStatus: (s: FilmStatus) => void;
}) {
  const matchPct = Math.round((movie.score ?? 0) * 100);
  const year = movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A';

  const action = (s: FilmStatus) => (e: React.MouseEvent) => {
    e.stopPropagation();
    onSetStatus(status === s ? 'none' : s);
  };

  return (
    <article className="group relative flex flex-col">
      <button
        onClick={onOpen}
        className="relative aspect-[2/3] w-full overflow-hidden border border-border/60 bg-card text-left"
      >
        <img
          src={movie.poster_url || ''}
          alt={`Poster for ${movie.title}`}
          referrerPolicy="no-referrer"
          className="object-cover w-full h-full transition-all duration-500 group-hover:scale-[1.04] group-hover:brightness-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/10 to-transparent" />

        <span className="absolute left-2 top-2 bg-background/80 px-1.5 py-0.5 font-mono text-[10px] tabular-nums text-primary backdrop-blur-sm">
          {matchPct}% MATCH
        </span>

        {status !== 'none' && (
          <span className="absolute right-2 top-2 border border-primary/60 bg-background/80 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-[0.14em] text-primary backdrop-blur-sm">
            {STATUS_LABEL[status as Exclude<FilmStatus, 'none'>]}
          </span>
        )}

        <div className="absolute inset-x-0 bottom-0 flex translate-y-2 items-center justify-center gap-2 p-3 opacity-0 transition-all duration-300 group-hover:translate-y-0 group-hover:opacity-100">
          <QuickAction label="Like" active={status === 'liked'} onClick={action('liked')}>
            <Heart className={`size-3.5 ${status === 'liked' ? 'fill-current' : ''}`} />
          </QuickAction>
          <QuickAction label="Archive" active={status === 'watched'} onClick={action('watched')}>
            <Archive className="size-3.5" />
          </QuickAction>
          <QuickAction label="Skip" active={status === 'disliked'} onClick={action('disliked')}>
            <X className="size-3.5" />
          </QuickAction>
        </div>
      </button>

      <div className="mt-3 flex flex-col gap-1.5">
        <h3 className="font-display text-sm font-semibold uppercase italic tracking-wide text-foreground">
          {movie.title}
        </h3>
        <div className="flex items-center gap-2 font-mono text-[11px] text-muted-foreground">
          <span className="text-amber">{year}</span>
          <span className="text-primary">{matchPct}% match</span>
        </div>
        <MatchBar value={matchPct} className="mt-0.5" />
        {movie.reason && (
          <p className="mt-1 line-clamp-2 font-sans text-[13px] italic leading-relaxed text-muted-foreground">
            {movie.reason}
          </p>
        )}
        <button
          onClick={onOpen}
          className="mt-1 flex items-center gap-1.5 self-start font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground transition-colors hover:text-primary"
        >
          View Details <ArrowRight className="size-3" />
        </button>
      </div>
    </article>
  );
}

function QuickAction({
  children, label, active, onClick,
}: Readonly<{
  children: React.ReactNode;
  label: string;
  active: boolean;
  onClick: (e: React.MouseEvent) => void;
}>) {
  return (
    <button
      onClick={onClick}
      aria-label={label}
      title={label}
      className={`flex size-8 items-center justify-center border backdrop-blur-sm transition-colors ${
        active
          ? 'border-primary bg-primary text-primary-foreground'
          : 'border-border/70 bg-background/70 text-foreground hover:border-primary hover:text-primary'
      }`}
    >
      {children}
    </button>
  );
}
