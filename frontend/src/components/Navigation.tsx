import React from 'react';
import { Settings, User } from 'lucide-react';

export type View = 'vault' | 'engine' | 'signal';

const NAV: { id: View; label: string }[] = [
  { id: 'vault', label: 'Vault' },
  { id: 'engine', label: 'Engine' },
  { id: 'signal', label: 'Signal' },
];

export function Navigation({
  view,
  onViewChange,
  onSettingsClick,
}: {
  view: View;
  onViewChange: (v: View) => void;
  onSettingsClick?: () => void;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1600px] items-center gap-4 px-4 sm:px-6 lg:px-10">
        <button
          onClick={() => onViewChange('vault')}
          className="font-display text-lg font-bold italic tracking-tight text-foreground transition-colors hover:text-primary sm:text-xl"
        >
          KULESHOV LAB
        </button>

        <nav className="ml-auto flex items-center gap-1 sm:gap-2 md:absolute md:left-1/2 md:ml-0 md:-translate-x-1/2">
          {NAV.map((item) => {
            const active = view === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`relative px-2.5 py-1.5 font-mono text-[11px] uppercase tracking-[0.22em] transition-colors sm:text-xs ${
                  active
                    ? 'text-primary text-glow-signal'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {item.label}
                {active && (
                  <span className="absolute -bottom-px left-2.5 right-2.5 h-px bg-primary" />
                )}
              </button>
            );
          })}
        </nav>

        <div className="ml-auto flex items-center gap-3 md:ml-0">
          <button
            onClick={onSettingsClick}
            aria-label="Settings"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            <Settings className="size-4" />
          </button>
          <button
            aria-label="Account"
            className="text-muted-foreground transition-colors hover:text-foreground"
          >
            <User className="size-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
