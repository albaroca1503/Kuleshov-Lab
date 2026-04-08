import React from 'react';
import { Settings, User, Menu } from 'lucide-react';

interface NavigationProps {
  currentView: string;
  onViewChange: (view: string) => void;
}

export const Navigation = ({ currentView, onViewChange }: NavigationProps) => {
  const navItems = [
    { id: 'vault', label: 'Vault', color: 'text-secondary' },
    { id: 'engine', label: 'Engine', color: 'text-primary' },
    { id: 'feed', label: 'Feed', color: 'text-secondary' },
  ];

  return (
    <header className="fixed top-0 left-0 w-full z-50 flex justify-between items-center px-6 py-4 bg-background/90 backdrop-blur-xl border-b border-outline-variant/10">
      <div 
        className="flex items-center gap-2 cursor-pointer"
        onClick={() => onViewChange('engine')}
      >
        <span className="text-2xl font-headline italic tracking-tight text-on-surface">Kuleshov Lab</span>
      </div>
      
      <nav className="hidden md:flex gap-10 items-center">
        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            className={`font-mono text-[11px] uppercase tracking-[0.15em] transition-colors duration-200 ${
              currentView === item.id 
                ? 'text-primary font-bold' 
                : 'text-secondary hover:text-primary'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <div className="flex items-center gap-6">
        <div className="relative hidden sm:block">
          <input 
            type="text" 
            placeholder="SEARCH ARCHIVES..."
            className="bg-transparent border-0 border-b border-outline-variant/30 text-[10px] font-mono tracking-widest focus:ring-0 focus:border-primary w-48 py-1 placeholder:text-secondary/30"
          />
        </div>
        <div className="flex gap-4 text-on-surface/60">
          <Settings className="w-5 h-5 cursor-pointer hover:text-primary transition-colors" />
          <User className="w-5 h-5 cursor-pointer hover:text-primary transition-colors" />
          <Menu className="w-5 h-5 md:hidden cursor-pointer hover:text-primary transition-colors" />
        </div>
      </div>
    </header>
  );
};
