import React from 'react';

export const GrainOverlay = () => <div className="grain-overlay" />;

export const MetadataStrip = ({ items, animate = false }: { items: string[], animate?: boolean }) => (
  <div className={`w-full overflow-hidden whitespace-nowrap border-y border-outline-variant/10 py-2 bg-background/50 backdrop-blur-sm`}>
    <div className={`flex gap-12 font-mono text-[10px] uppercase tracking-[0.2em] text-secondary/60 ${animate ? 'animate-marquee' : 'px-6'}`}>
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-2">
          {animate && i % 2 === 0 && <span className="w-1.5 h-1.5 bg-primary rounded-full" />}
          {item}
        </span>
      ))}
      {animate && items.map((item, i) => (
        <span key={`dup-${i}`} className="flex items-center gap-2">
          {i % 2 === 0 && <span className="w-1.5 h-1.5 bg-primary rounded-full" />}
          {item}
        </span>
      ))}
    </div>
  </div>
);
