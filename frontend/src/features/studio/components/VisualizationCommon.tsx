import { formatValue, type ScalarBadge } from '../utils/visualizationUtils';

export function DetailChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full bg-surface-soft px-2.5 py-1 text-[11px] text-ink-secondary">
      <span className="font-medium text-ink-muted">{label}</span>
      <span className="font-mono text-ink">{value}</span>
    </div>
  );
}

export function ScalarBadgeList({ badges }: { badges: ScalarBadge[] }) {
  if (badges.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {badges.map((badge) => (
        <div
          key={badge.name}
          className="inline-flex items-center gap-1.5 rounded-lg bg-surface-soft px-2.5 py-1.5"
        >
          <span className="font-mono text-[11px] font-semibold text-accent">{badge.name}</span>
          <span className="text-[11px] text-ink-muted">=</span>
          <span className="font-mono text-[11px] text-ink">{formatValue(badge.value)}</span>
        </div>
      ))}
    </div>
  );
}

export function ArrowBadge({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center">
      <span className="rounded bg-surface-soft px-1.5 py-0.5 font-mono text-[10px] font-semibold text-accent">
        {label}
      </span>
      <span className="text-sm leading-none text-accent">▼</span>
    </div>
  );
}
