import React, { useState, useEffect, useMemo } from 'react';
import { Download, Loader2, Search, X } from 'lucide-react';
import { AnimatePresence } from 'motion/react';
import { api, WatchedMovieItem, UserStats, Movie } from '../services/api';
import { FilmModal } from './FilmModal';
import { FilmStatus } from './FilmCard';

type StatusFilter = 'all' | 'liked' | 'watched' | 'disliked';

const STATUS_LABEL: Record<string, string> = {
  liked: 'LIKED',
  watched: 'ARCHIVED',
  disliked: 'REJECTED',
};

const FILTER_LABELS: Record<StatusFilter, string> = {
  all: 'All',
  liked: 'Liked',
  watched: 'Archived',
  disliked: 'Rejected',
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

function buildDossierHtml(movies: WatchedMovieItem[]): string {
  const liked    = movies.filter(m => m.status === 'liked');
  const disliked = movies.filter(m => m.status === 'disliked');
  const watched  = movies.filter(m => m.status === 'watched');

  // Top genres from liked films
  const genreCounts = new Map<string, number>();
  liked.forEach(m => (m.genres ?? []).forEach(g =>
    genreCounts.set(g, (genreCounts.get(g) ?? 0) + 1)
  ));
  const sortedGenres = [...genreCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
  const topGenre = sortedGenres[0]?.[0]?.toUpperCase() ?? '—';

  // Favorite decade
  const decadeCounts = new Map<number, number>();
  liked.forEach(m => {
    if (m.release_date) {
      const decade = Math.floor(new Date(m.release_date).getFullYear() / 10) * 10;
      decadeCounts.set(decade, (decadeCounts.get(decade) ?? 0) + 1);
    }
  });
  const favDecade = [...decadeCounts.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;

  // Cinematic age
  const years = liked.filter(m => m.release_date).map(m => new Date(m.release_date!).getFullYear());
  const avgYear = years.length > 0 ? Math.round(years.reduce((a, b) => a + b, 0) / years.length) : null;
  const cinematicAge = avgYear ? new Date().getFullYear() - avgYear : null;

  // Sync index / temperature
  const syncIndex = liked.length + disliked.length > 0
    ? Math.round(liked.length / (liked.length + disliked.length) * 100)
    : 0;
  const syncTemp =
    syncIndex >= 90 ? 'gélido y exigente' :
    syncIndex >= 70 ? 'frío y selectivo' :
    syncIndex >= 50 ? 'templado y curioso' :
    syncIndex >= 30 ? 'volátil e inestable' : 'febril e impredecible';

  const acquisitionRatio = movies.length > 0 ? Math.round(liked.length / movies.length * 100) : 0;

  const today = new Date().toLocaleDateString('es-ES', { day: 'numeric', month: 'long', year: 'numeric' });

  const maxGenreCount = sortedGenres[0]?.[1] ?? 1;
  const genreBarsHtml = sortedGenres.map(([genre, count]) => `
    <div class="genre-row">
      <span class="genre-name">${genre.toUpperCase()}</span>
      <div class="genre-bar-track">
        <div class="genre-bar-fill" style="width:${Math.round(count / maxGenreCount * 100)}%"></div>
      </div>
      <span class="genre-count">${count}</span>
    </div>`).join('');

  const filmsHtml = liked.slice(0, 8).map((m, i) => {
    const year = m.release_date ? new Date(m.release_date).getFullYear() : '';
    return `
    <div class="film-row">
      <span class="film-num">${String(i + 1).padStart(2, '0')}</span>
      <span class="film-title">${m.title.toUpperCase()}</span>
      ${year ? `<span class="film-year">(${year})</span>` : ''}
    </div>`;
  }).join('');

  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>Kuleshov Lab — Dossier</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;600;700&family=JetBrains+Mono:wght@300;400;700&display=swap" rel="stylesheet">
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    @page { size:A4; margin:18mm 20mm; }
    @media print {
      body { -webkit-print-color-adjust:exact; print-color-adjust:exact; }
      .corner { display:block; }
    }
    body {
      background:#191510;
      color:#ede8df;
      font-family:'JetBrains Mono','Courier New',monospace;
      font-size:11px;
      line-height:1.65;
      padding:52px 60px;
    }
    /* ── corners ── */
    .corner { position:fixed; width:28px; height:28px; opacity:0.35; }
    .corner-tl { top:18px; left:18px; border-top:2px solid #e8355a; border-left:2px solid #e8355a; }
    .corner-tr { top:18px; right:18px; border-top:2px solid #e8355a; border-right:2px solid #e8355a; }
    .corner-bl { bottom:18px; left:18px; border-bottom:2px solid #e8355a; border-left:2px solid #e8355a; }
    .corner-br { bottom:18px; right:18px; border-bottom:2px solid #e8355a; border-right:2px solid #e8355a; }
    /* ── header ── */
    .header { text-align:center; margin-bottom:36px; }
    .logo {
      font-family:'Oswald','Arial Narrow',sans-serif;
      font-size:48px; font-weight:700;
      letter-spacing:0.45em;
      color:#ede8df;
    }
    .subtitle {
      font-size:10px; letter-spacing:0.35em;
      color:#d4a843; text-transform:uppercase; margin-top:6px;
    }
    .badge {
      display:inline-block;
      border:1px solid #e8355a;
      color:#e8355a;
      font-size:9px; letter-spacing:0.3em;
      padding:3px 14px; margin-top:14px;
      text-transform:uppercase;
    }
    /* ── dividers ── */
    hr { border:none; border-top:1px solid #2e2820; margin:22px 0; }
    hr.red { border-top-color:#e8355a; opacity:0.5; }
    /* ── section title ── */
    .section-title {
      font-size:9px; letter-spacing:0.45em;
      color:#5a4e3e; text-transform:uppercase; margin-bottom:18px;
    }
    /* ── inventory ── */
    .inventory-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px 48px; }
    .stat-row {
      display:flex; justify-content:space-between; align-items:baseline;
      border-bottom:1px dotted #252015; padding-bottom:5px;
    }
    .stat-label { font-size:9px; letter-spacing:0.14em; color:#8a7e6e; text-transform:uppercase; }
    .stat-value { font-size:15px; font-weight:700; color:#ede8df; }
    .stat-value.red { color:#e8355a; }
    /* ── identity ── */
    .identity-row {
      display:flex; align-items:baseline; gap:10px; margin-bottom:14px;
    }
    .id-label {
      font-size:9px; letter-spacing:0.2em; color:#5a4e3e;
      text-transform:uppercase; white-space:nowrap; min-width:210px;
    }
    .id-dots { flex:1; border-bottom:1px dotted #252015; margin-bottom:4px; }
    .id-value {
      font-family:'Oswald','Arial Narrow',sans-serif;
      font-size:20px; font-weight:600; letter-spacing:0.08em;
      color:#e8355a; white-space:nowrap;
    }
    .id-sub { font-size:8px; color:#5a4e3e; letter-spacing:0.12em; margin-top:1px; }
    /* ── genre bars ── */
    .genre-row { display:flex; align-items:center; gap:14px; margin-bottom:10px; }
    .genre-name { font-size:9px; letter-spacing:0.2em; color:#8a7e6e; text-transform:uppercase; min-width:110px; }
    .genre-bar-track { flex:1; height:7px; background:#252015; overflow:hidden; }
    .genre-bar-fill { height:100%; background:#e8355a; }
    .genre-count { font-size:9px; color:#5a4e3e; min-width:20px; text-align:right; }
    /* ── films list ── */
    .film-row {
      display:flex; align-items:baseline; gap:12px;
      border-bottom:1px dotted #252015; padding-bottom:8px; margin-bottom:8px;
    }
    .film-num { font-size:9px; color:#e8355a; min-width:18px; }
    .film-title {
      font-family:'Oswald','Arial Narrow',sans-serif;
      font-size:15px; font-weight:400; letter-spacing:0.06em; color:#ede8df;
    }
    .film-year { font-size:10px; color:#d4a843; }
    /* ── footer ── */
    .footer {
      margin-top:36px; text-align:center;
      font-size:9px; letter-spacing:0.28em; color:#332a1e; text-transform:uppercase;
    }
    .footer span { color:#e8355a; }
  </style>
</head>
<body>
  <div class="corner corner-tl"></div>
  <div class="corner corner-tr"></div>
  <div class="corner corner-bl"></div>
  <div class="corner corner-br"></div>

  <div class="header">
    <div class="logo">KULESHOV LAB</div>
    <div class="subtitle">Dossier Cinematográfico · Uso Confidencial</div>
    <div class="badge">Expediente Personal · Clasificado</div>
  </div>

  <hr class="red">

  <div class="section-title">Inventario de Expedientes</div>
  <div class="inventory-grid">
    <div class="stat-row">
      <span class="stat-label">Adquisiciones Totales</span>
      <span class="stat-value">${movies.length}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Sancionadas</span>
      <span class="stat-value red">${liked.length}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Archivadas</span>
      <span class="stat-value">${watched.length}</span>
    </div>
    <div class="stat-row">
      <span class="stat-label">Rechazadas</span>
      <span class="stat-value">${disliked.length}</span>
    </div>
  </div>

  <hr>

  <div class="section-title">Análisis de Identidad</div>

  <div class="identity-row">
    <span class="id-label">Tu género alma es</span>
    <div class="id-dots"></div>
    <div><div class="id-value">${topGenre}</div></div>
  </div>

  ${favDecade ? `
  <div class="identity-row">
    <span class="id-label">Tu época favorita es</span>
    <div class="id-dots"></div>
    <div><div class="id-value">LOS ${favDecade}s</div></div>
  </div>` : ''}

  ${cinematicAge && avgYear ? `
  <div class="identity-row">
    <span class="id-label">Tu edad cinematográfica es</span>
    <div class="id-dots"></div>
    <div>
      <div class="id-value">${cinematicAge} AÑOS</div>
      <div class="id-sub">el film medio de tu vault es de ${avgYear}</div>
    </div>
  </div>` : ''}

  <div class="identity-row">
    <span class="id-label">Tu temperatura fílmica es</span>
    <div class="id-dots"></div>
    <div>
      <div class="id-value">${syncIndex}°</div>
      <div class="id-sub">${syncTemp}</div>
    </div>
  </div>

  <div class="identity-row">
    <span class="id-label">Tu ratio de adquisición es</span>
    <div class="id-dots"></div>
    <div>
      <div class="id-value">${acquisitionRatio}%</div>
      <div class="id-sub">${liked.length} de ${movies.length} films sancionados</div>
    </div>
  </div>

  ${sortedGenres.length > 0 ? `
  <hr>
  <div class="section-title">Distribución de Géneros</div>
  ${genreBarsHtml}` : ''}

  ${liked.length > 0 ? `
  <hr>
  <div class="section-title">Adquisiciones Destacadas</div>
  ${filmsHtml}` : ''}

  <hr class="red">
  <div class="footer">Generado por <span>KULESHOV LAB</span> · ${today}</div>

  <script>window.onload = function() { setTimeout(function() { window.print(); }, 700); };</script>
</body>
</html>`;
}

export function VaultView() {
  const [stats, setStats] = useState<UserStats | null>(null);
  const [movies, setMovies] = useState<WatchedMovieItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<WatchedMovieItem | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<FilmStatus>('none');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [search, setSearch] = useState('');

  useEffect(() => {
    Promise.all([api.getUserStats(), api.getWatchedMovieDetails()])
      .then(([s, m]) => { setStats(s); setMovies(m.movies); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (selected) setSelectedStatus(toFilmStatus(selected.status));
  }, [selected]);

  const PALETTE_COLORS = ['bg-primary', 'bg-amber', 'bg-sky-400', 'bg-emerald-500', 'bg-violet-400'];

  const palette = useMemo(() => {
    const counts = new Map<string, number>();
    movies
      .filter(m => m.status === 'liked')
      .forEach(m => (m.genres ?? []).forEach(g => counts.set(g, (counts.get(g) ?? 0) + 1)));
    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([genre, count], i) => ({ genre, count, color: PALETTE_COLORS[i] }));
  }, [movies]);

  const filtered = useMemo(() =>
    movies.filter(m =>
      (statusFilter === 'all' || m.status === statusFilter) &&
      m.title.toLowerCase().includes(search.toLowerCase())
    ), [movies, statusFilter, search]);

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

  const handleExportDossier = () => {
    const blob = new Blob([buildDossierHtml(movies)], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    window.open(url, '_blank');
    setTimeout(() => URL.revokeObjectURL(url), 15000);
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
        <button
          onClick={handleExportDossier}
          disabled={movies.length === 0}
          className="inline-flex items-center gap-2 bg-primary px-6 py-3 font-mono text-xs uppercase tracking-[0.2em] text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-40 disabled:cursor-not-allowed"
        >
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
              <div className="flex h-12 gap-1">
                {palette.map(p => (
                  <div
                    key={p.genre}
                    className={`min-w-0 ${p.color}`}
                    style={{ flex: p.count }}
                    title={p.genre}
                  />
                ))}
              </div>
              <div className="flex flex-wrap gap-x-3 gap-y-1">
                {palette.map(p => (
                  <span key={p.genre} className="flex items-center gap-1 font-mono text-[9px] uppercase tracking-[0.12em] text-muted-foreground">
                    <span className={`inline-block size-1.5 shrink-0 ${p.color}`} />
                    {p.genre}
                  </span>
                ))}
              </div>
            </>
          ) : (
            <div className="flex h-12 gap-1 opacity-20">
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

      {/* Filters */}
      {!loading && movies.length > 0 && (
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex gap-1">
            {(['all', 'liked', 'watched', 'disliked'] as const).map(s => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.12em] border transition-colors ${
                  statusFilter === s
                    ? 'border-primary bg-primary/10 text-primary'
                    : 'border-border/60 text-muted-foreground hover:border-primary/50 hover:text-foreground'
                }`}
              >
                {FILTER_LABELS[s]}
              </button>
            ))}
          </div>
          <div className="flex items-center gap-2 border border-border/60 px-3 py-1.5 focus-within:border-primary/60 transition-colors">
            <Search className="size-3 shrink-0 text-muted-foreground" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search titles…"
              className="w-36 bg-transparent font-mono text-xs text-foreground placeholder:text-muted-foreground/60 focus:outline-none"
            />
            {search && (
              <button onClick={() => setSearch('')} className="text-muted-foreground hover:text-foreground transition-colors">
                <X className="size-3" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <Loader2 className="size-8 text-primary animate-spin" />
        </div>
      ) : movies.length === 0 ? (
        <div className="mt-10 border border-dashed border-border/60 py-20 text-center font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          Your vault is empty — start by recommending films in the Engine
        </div>
      ) : filtered.length === 0 ? (
        <div className="mt-10 border border-dashed border-border/60 py-20 text-center font-mono text-xs uppercase tracking-[0.2em] text-muted-foreground">
          No films match your filters
        </div>
      ) : (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          {filtered.map((movie) => (
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
