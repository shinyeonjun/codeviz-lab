import { Card } from '../../../components/ui/Card';

interface VariablesPanelProps {
  localsSnapshot?: Record<string, unknown> | null;
}

export function VariablesPanel({ localsSnapshot }: VariablesPanelProps) {
  return (
    <Card>
      <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">Variables</h4>
      <div className="max-h-[180px] space-y-1.5 overflow-y-auto scrollbar-thin">
        {localsSnapshot ? (
          Object.keys(localsSnapshot).length > 0 ? (
            Object.entries(localsSnapshot).map(([key, value]) => (
              <div key={key} className="flex items-baseline gap-3 rounded-lg bg-surface-soft px-3 py-2">
                <span className="font-mono text-xs font-semibold text-accent">{key}</span>
                <span className="font-mono text-sm text-ink">{JSON.stringify(value)}</span>
              </div>
            ))
          ) : (
            <p className="py-4 text-center text-sm text-ink-faint">변수 없음</p>
          )
        ) : (
          <p className="py-4 text-center text-sm text-ink-faint">대기 중</p>
        )}
      </div>
    </Card>
  );
}
