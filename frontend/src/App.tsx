import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Clapperboard, 
  X, 
  Plus, 
  Info, 
  Share2, 
  Play, 
  Archive,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { Navigation } from './components/Navigation';
import { GrainOverlay, MetadataStrip } from './components/Common';
import { useRecommendations } from './hooks/useRecommendations';
import { api, Movie } from './services/api';

// --- Views ---

interface EngineViewProps {
  onSearch: (vibe: string) => void;
  loading: boolean;
  error: string | null;
  onClearError: () => void;
  movies: Movie[];
}

const EngineView = ({ onSearch, loading, error, onClearError, movies }: EngineViewProps) => {
  const [vibeInput, setVibeInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (vibeInput.trim()) {
      onSearch(vibeInput);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setVibeInput(suggestion);
    onSearch(suggestion);
  };

  return (
    <div className="relative min-h-screen pt-24 pb-32 cinematic-bg flex flex-col items-center justify-center px-6">
      <div className="absolute top-24 left-0 w-full">
        <MetadataStrip 
          items={[
            loading ? "SYSTEM_STATUS: PROCESSING" : "SYSTEM_STATUS: OPERATIONAL", 
            "ENGINE_VERSION: 2.0.4_NOIR", 
            "STREAMING_FILTERS: ACTIVE", 
            "CURATION_MODE: CINEMATIC_ARCHIVE", 
            "LATENCY: 12ms"
          ]} 
        />
      </div>

      <div className="w-full max-w-4xl space-y-12 z-10">
        {error && (
          <div className="bg-red-500/10 border border-red-500/20 p-4 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="font-mono text-sm text-red-500">{error}</p>
            <button onClick={onClearError} className="ml-auto">
              <X className="w-4 h-4 text-red-500" />
            </button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="relative group">
            <input
              type="text"
              value={vibeInput}
              onChange={(e) => setVibeInput(e.target.value)}
              placeholder="Describe the vibe..."
              disabled={loading}
              className="w-full bg-transparent border-b border-outline-variant py-8 text-4xl md:text-6xl font-headline italic text-on-surface focus:outline-none focus:border-primary transition-colors placeholder:text-secondary/30 disabled:opacity-50 leading-tight"
              style={{ lineHeight: '1.1' }}
            />
            <div className="absolute right-0 bottom-8">
              {loading ? (
                <Loader2 className="text-primary w-10 h-10 animate-spin" />
              ) : (
                <Clapperboard className="text-primary w-10 h-10" />
              )}
            </div>
          </div>
          
          <div className="flex flex-wrap gap-4 pt-4">
            {[
              "A neon-drenched 80s thriller",
              "A melancholic rainy afternoon in Tokyo",
              "Gothic horror in a sun-bleached desert"
            ].map((suggestion, i) => (
              <button 
                key={i}
                type="button"
                onClick={() => handleSuggestionClick(suggestion)}
                disabled={loading}
                className="px-4 py-2 bg-surface-low hover:bg-surface-high transition-colors text-xs font-mono uppercase tracking-widest text-secondary border border-outline-variant/20 disabled:opacity-50"
              >
                "{suggestion}"
              </button>
            ))}
          </div>
        </form>

        {movies.length > 0 && (
          <div className="pt-12 border-t border-outline-variant/10">
            <h3 className="font-mono text-sm uppercase tracking-widest text-primary mb-6">
              Found {movies.length} matches
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {movies.map((movie) => (
                <div key={movie.id} className="bg-surface-low aspect-[2/3] relative overflow-hidden group cursor-pointer">
                  <img
                    src={movie.poster_url || 'https://via.placeholder.com/500x750?text=No+Poster'}
                    className="w-full h-full object-cover grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-700"
                    alt={movie.title}
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-background/20 to-transparent"></div>
                  <div className="absolute bottom-0 left-0 p-4 w-full">
                    <h4 className="text-sm font-headline italic text-on-surface line-clamp-2">{movie.title}</h4>
                    <p className="font-mono text-[9px] uppercase tracking-widest text-secondary mt-1">
                      {movie.release_date ? new Date(movie.release_date).getFullYear() : 'N/A'}
                    </p>
                    {movie.score && (
                      <p className="font-mono text-[9px] text-primary mt-1">
                        Match: {(movie.score * 100).toFixed(0)}%
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const VaultView = ({ onSelectMovie }: { onSelectMovie: () => void }) => (
  <div className="max-w-7xl mx-auto px-6 pt-32 pb-20">
    <header className="mb-20 flex flex-col md:flex-row md:items-end justify-between gap-8">
      <div className="max-w-2xl">
        <h1 className="text-6xl md:text-8xl font-headline italic leading-[0.9] text-on-surface mb-6">The Vault</h1>
        <p className="font-sans text-secondary text-lg leading-relaxed opacity-80">A curated repository of cinematic experiences. Your personal chronology of sight and sound, indexed for the discerning eye.</p>
      </div>
      <button className="bg-gradient-to-b from-primary to-primary-container text-on-primary font-mono font-bold text-[11px] px-8 py-4 tracking-[0.1em] uppercase">
        Export Dossier
      </button>
    </header>

    <section className="grid grid-cols-1 md:grid-cols-4 gap-px bg-outline-variant/10 mb-20">
      {[
        { label: 'Total Hours', value: '1,428.5', sub: '+12.4% vs last period', color: 'text-primary' },
        { label: 'Mood Palette', value: 'Neo-Noir', sub: 'Dominant Palette', isPalette: true },
        { label: 'Sync Index', value: '99.2%', sub: 'Optimal Integrity' },
        { label: 'Catalog Count', value: '842', sub: 'Active Acquisitions' }
      ].map((stat, i) => (
        <div key={i} className="bg-surface p-8">
          <p className="font-mono text-[10px] uppercase tracking-[0.2em] text-secondary/50 mb-4">{stat.label}</p>
          {stat.isPalette ? (
            <div className="flex h-10 w-full gap-1 mb-2">
              <div className="h-full w-1/4 bg-primary-container"></div>
              <div className="h-full w-1/6 bg-secondary"></div>
              <div className="h-full w-1/3 bg-surface-highest"></div>
              <div className="h-full flex-grow bg-outline"></div>
            </div>
          ) : (
            <h3 className={`text-4xl font-headline italic ${stat.color || 'text-on-surface'}`}>{stat.value}</h3>
          )}
          <p className="font-mono text-[9px] uppercase tracking-[0.1em] text-outline mt-2">{stat.sub}</p>
        </div>
      ))}
    </section>

    <div className="text-center py-20">
      <p className="font-mono text-sm text-secondary/60">Your watched movies will appear here</p>
    </div>
  </div>
);

const FeedView = () => (
  <div className="pt-32 pb-32 flex flex-col items-center min-h-screen w-full px-4 overflow-hidden">
    <div className="w-full max-w-lg mb-8 flex justify-between items-center font-mono text-[10px] tracking-[0.2em] text-secondary opacity-60 border-b border-outline-variant/10 pb-2">
      <span className="uppercase">SIGNAL: ACTIVE</span>
      <span className="uppercase">STOCK: 35MM NOIR</span>
      <span className="uppercase">LAT: 34.0522 N</span>
    </div>

    <div className="text-center py-20">
      <p className="font-mono text-sm text-secondary/60">Swipeable feed coming soon</p>
    </div>
  </div>
);

// --- Main App ---

export default function App() {
  const [currentView, setCurrentView] = useState('engine');
  const { movies, loading, error, getRecommendations, clearError } = useRecommendations();

  const handleSearch = async (vibe: string) => {
    await getRecommendations(vibe, 20);
  };

  const renderView = () => {
    switch (currentView) {
      case 'engine':
        return (
          <EngineView 
            onSearch={handleSearch}
            loading={loading}
            error={error}
            onClearError={clearError}
            movies={movies}
          />
        );
      case 'vault':
        return <VaultView onSelectMovie={() => {}} />;
      case 'feed':
        return <FeedView />;
      default:
        return (
          <EngineView 
            onSearch={handleSearch}
            loading={loading}
            error={error}
            onClearError={clearError}
            movies={movies}
          />
        );
    }
  };

  return (
    <div className="min-h-screen bg-background selection:bg-primary selection:text-on-primary">
      <GrainOverlay />
      <Navigation currentView={currentView} onViewChange={setCurrentView} />
      
      <main className="relative">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            {renderView()}
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Desktop Metadata Sidebar */}
      <aside className="fixed right-0 top-0 h-screen w-16 border-l border-outline-variant/10 flex flex-col items-center py-12 gap-12 hidden md:flex z-40">
        <div className="rotate-90 origin-center whitespace-nowrap">
          <span className="font-mono text-[10px] uppercase tracking-[0.5em] text-secondary/30">THE_CINEMATIC_CURATOR_V2</span>
        </div>
        <div className="mt-auto space-y-8 pb-8">
          <Info className="w-5 h-5 text-secondary/40 hover:text-primary cursor-pointer transition-colors" />
          <Share2 className="w-5 h-5 text-secondary/40 hover:text-primary cursor-pointer transition-colors" />
        </div>
      </aside>

      {/* Bottom Nav (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center h-20 bg-background border-t border-outline-variant/10">
        {[
          { id: 'vault', label: 'Vault', icon: Archive },
          { id: 'engine', label: 'Engine', icon: Clapperboard },
          { id: 'feed', label: 'Feed', icon: Play }
        ].map(item => (
          <button
            key={item.id}
            onClick={() => setCurrentView(item.id)}
            className={`flex flex-col items-center justify-center transition-all duration-200 ${
              currentView === item.id ? 'text-primary scale-110' : 'text-secondary opacity-60'
            }`}
          >
            <item.icon className={`w-6 h-6 ${currentView === item.id ? 'fill-primary/20' : ''}`} />
            <span className="font-mono uppercase tracking-[0.1em] text-[10px] mt-1">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}

// Made with Bob
