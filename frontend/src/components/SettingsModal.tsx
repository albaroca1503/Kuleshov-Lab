import React, { useState, useEffect } from 'react';
import { X, Loader2, Check } from 'lucide-react';
import { motion } from 'motion/react';
import { api, UserSettings } from '../services/api';

const STREAMING_SERVICES = [
  { id: 8,   name: 'Netflix',     logo: '/t2yyOv40HZeVlLjYsCsPHnWLk4W.jpg' },
  { id: 119, name: 'Prime',       logo: '/68MNrwlkpF7WnmNPXLah69CR5cb.jpg' },
  { id: 337, name: 'Disney+',     logo: '/7rwgEs15tFwyR9NPQ5vpzxTj19Q.jpg' },
  { id: 350, name: 'Apple TV+',   logo: '/6uhKBfmtzFqOcLousHwZuzcrScK.jpg' },
  { id: 11,  name: 'MUBI',        logo: '/fq3wyOs1RHyz2yfzsb4sck7aWRG.jpg' },
  { id: 62,  name: 'Filmin',      logo: '/iqB6BSBA6oKlzVHmFcAH8BTLtCB.jpg' },
  { id: 384, name: 'Max',         logo: '/Ajqyt5iiK25FYKuNYo4dSOrMC5R.jpg' },
  { id: 531, name: 'Paramount+',  logo: '/fi83B1oztoS47xxcemFdPMhIzK.jpg' },
  { id: 149, name: 'Movistar+',   logo: '/7N2bFVaYWiFfLQy5bGPvtyJRxCt.jpg' },
  { id: 39,  name: 'Now TV',      logo: '/pvske06mnSHKqBJLGQHIEQ1EDQP.jpg' },
];

const COUNTRIES = [
  { code: 'ES', label: 'Spain' },
  { code: 'US', label: 'United States' },
  { code: 'GB', label: 'United Kingdom' },
  { code: 'FR', label: 'France' },
  { code: 'DE', label: 'Germany' },
  { code: 'IT', label: 'Italy' },
];

export function SettingsModal({ onClose }: { onClose: () => void }) {
  const [settings, setSettings] = useState<UserSettings>({ country_code: 'ES', streaming_service_ids: [] });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    globalThis.addEventListener('keydown', onKey);
    return () => globalThis.removeEventListener('keydown', onKey);
  }, [onClose]);

  useEffect(() => {
    api.getUserSettings().then(s => setSettings(s)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const toggle = (id: number) => setSettings(prev => ({
    ...prev,
    streaming_service_ids: prev.streaming_service_ids.includes(id)
      ? prev.streaming_service_ids.filter(x => x !== id)
      : [...prev.streaming_service_ids, id],
  }));

  const handleSave = async () => {
    setSaving(true);
    try { await api.updateUserSettings(settings); } catch (err) { console.error('Settings save failed:', err); }
    setSaving(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button className="absolute inset-0 bg-background/80 backdrop-blur-sm w-full cursor-default" onClick={onClose} aria-label="Close" />
      <motion.div
        initial={{ opacity: 0, scale: 0.97 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.97 }}
        transition={{ duration: 0.18 }}
        className="relative w-full max-w-lg border border-border/70 bg-card noir-grain p-6"
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className="font-display text-xl italic uppercase text-foreground">Streaming Services</h2>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <X className="size-4" />
          </button>
        </div>

        {loading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="size-6 text-primary animate-spin" />
          </div>
        ) : (
          <>
            <div className="mb-6">
              <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground mb-2">Country</p>
              <select
                value={settings.country_code}
                onChange={e => setSettings(prev => ({ ...prev, country_code: e.target.value }))}
                className="bg-card border border-border/70 text-foreground font-mono text-xs px-3 py-2 focus:outline-none focus:border-primary"
              >
                {COUNTRIES.map(c => <option key={c.code} value={c.code}>{c.label}</option>)}
              </select>
            </div>

            <p className="font-mono text-[9px] uppercase tracking-[0.2em] text-muted-foreground mb-3">Your subscriptions</p>
            <div className="grid grid-cols-5 gap-2 mb-6">
              {STREAMING_SERVICES.map(svc => {
                const active = settings.streaming_service_ids.includes(svc.id);
                return (
                  <button
                    key={svc.id}
                    onClick={() => toggle(svc.id)}
                    className={`flex flex-col items-center gap-1.5 p-2 border transition-all ${
                      active ? 'border-primary bg-primary/10' : 'border-border/70 hover:border-primary/50'
                    }`}
                  >
                    <img
                      src={`https://image.tmdb.org/t/p/w92${svc.logo}`}
                      alt={svc.name}
                      className="size-8 object-cover rounded"
                    />
                    <span className="font-mono text-[7px] uppercase tracking-[0.1em] text-muted-foreground text-center leading-tight">{svc.name}</span>
                    {active && <Check className="size-2.5 text-primary" />}
                  </button>
                );
              })}
            </div>

            <button
              onClick={handleSave}
              disabled={saving}
              className="w-full py-3 bg-primary text-primary-foreground font-mono text-[10px] uppercase tracking-[0.2em] hover:bg-primary/90 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving…' : 'Save preferences'}
            </button>
          </>
        )}
      </motion.div>
    </div>
  );
}
