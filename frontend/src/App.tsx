import React, { useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Navigation, View } from './components/Navigation';
import { EngineView } from './components/EngineView';
import { VaultView } from './components/VaultView';
import { SignalView } from './components/SignalView';
import { SettingsModal } from './components/SettingsModal';
import { GrainOverlay } from './components/Common';
import { useRecommendations } from './hooks/useRecommendations';
import { FilmStatus } from './components/FilmCard';
import { Filters } from './services/api';

export default function App() {
  const [view, setView] = useState<View>('engine');
  const [showSettings, setShowSettings] = useState(false);
  const [statuses, setStatuses] = useState<Record<number, FilmStatus>>({});

  const { movies, loading, error, getRecommendations, getVaultRecommendations, markWatched, clearError } =
    useRecommendations();

  const setStatus = useCallback(
    (id: number, s: FilmStatus) => {
      setStatuses((prev) => ({ ...prev, [id]: s }));
      if (s !== 'none') {
        markWatched(id, s);
      }
    },
    [markWatched],
  );

  const handleSearch = useCallback(
    async (vibe: string, filters?: Filters) => {
      await getRecommendations(vibe, 20, filters);
    },
    [getRecommendations],
  );

  const handleVaultSearch = useCallback(
    async (_filters?: Filters) => {
      await getVaultRecommendations();
    },
    [getVaultRecommendations],
  );

  return (
    <div className="min-h-svh bg-background">
      <GrainOverlay />
      <Navigation
        view={view}
        onViewChange={setView}
        onSettingsClick={() => setShowSettings(true)}
      />

      <main>
        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
          >
            {view === 'engine' && (
              <EngineView
                onSearch={handleSearch}
                onVaultSearch={handleVaultSearch}
                loading={loading}
                error={error}
                onClearError={clearError}
                movies={movies}
                statuses={statuses}
                onSetStatus={setStatus}
              />
            )}
            {view === 'vault' && <VaultView />}
            {view === 'signal' && <SignalView onSetStatus={setStatus} />}
          </motion.div>
        </AnimatePresence>
      </main>

      <AnimatePresence>
        {showSettings && <SettingsModal onClose={() => setShowSettings(false)} />}
      </AnimatePresence>
    </div>
  );
}
