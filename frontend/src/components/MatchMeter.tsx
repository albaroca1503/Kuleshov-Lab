export interface MatchFacet {
  label: string;
  score: number;
}

export function MatchBar({
  value,
  className = '',
}: {
  value: number;
  className?: string;
}) {
  return (
    <div
      className={`h-1 w-full overflow-hidden bg-border/60 ${className}`}
      role="progressbar"
      aria-valuenow={value}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full bg-primary transition-[width] duration-700 ease-out"
        style={{ width: `${value}%` }}
      />
    </div>
  );
}

export function MatchBreakdown({ facets }: { facets: MatchFacet[] }) {
  return (
    <div className="flex flex-col gap-2.5">
      {facets.map((f) => (
        <div key={f.label} className="flex items-center gap-3">
          <span className="w-28 shrink-0 font-mono text-[10px] uppercase tracking-[0.18em] text-muted-foreground">
            {f.label}
          </span>
          <MatchBar value={f.score} className="flex-1" />
          <span className="w-9 shrink-0 text-right font-mono text-[11px] tabular-nums text-amber">
            {f.score}
          </span>
        </div>
      ))}
    </div>
  );
}
