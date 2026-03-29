import { Card } from '../../../components/ui/Card';
import type { ExecutionFrame } from '../../../types/execution';

interface VariablesPanelProps {
  localsSnapshot?: Record<string, unknown> | null;
  globalsSnapshot?: Record<string, unknown> | null;
  callStack?: ExecutionFrame[] | null;
  metadata?: Record<string, unknown> | null;
}

function renderSnapshotEntries(snapshot: Record<string, unknown>) {
  return Object.entries(snapshot).map(([key, value]) => (
    <div key={key} className="flex items-baseline gap-3 rounded-lg bg-surface-soft px-3 py-2">
      <span className="font-mono text-xs font-semibold text-accent">{key}</span>
      <span className="font-mono text-sm text-ink">{JSON.stringify(value)}</span>
    </div>
  ));
}

function renderEmpty(message: string) {
  return <p className="py-3 text-center text-sm text-ink-faint">{message}</p>;
}

export function VariablesPanel({
  localsSnapshot,
  globalsSnapshot,
  callStack,
  metadata,
}: VariablesPanelProps) {
  const locals = localsSnapshot ?? null;
  const globals = globalsSnapshot ?? null;
  const frames = callStack ?? [];
  const hasMetadata = metadata && Object.keys(metadata).length > 0;

  return (
    <Card>
      <div className="mb-3 flex items-center justify-between gap-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">Trace Context</h4>
        {hasMetadata && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(metadata ?? {}).map(([key, value]) => (
              <span
                key={key}
                className="rounded-full border border-surface-border bg-white px-2 py-1 font-mono text-[11px] text-ink-muted"
              >
                {key}: {String(value)}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="max-h-[260px] space-y-3 overflow-y-auto scrollbar-thin">
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">Locals</p>
          <div className="space-y-1.5">
            {locals ? (
              Object.keys(locals).length > 0 ? (
                renderSnapshotEntries(locals)
              ) : (
                renderEmpty('지역 변수가 없습니다')
              )
            ) : (
              renderEmpty('대기 중')
            )}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">Globals</p>
          <div className="space-y-1.5">
            {globals ? (
              Object.keys(globals).length > 0 ? (
                renderSnapshotEntries(globals)
              ) : (
                renderEmpty('전역 변수가 없습니다')
              )
            ) : (
              renderEmpty('대기 중')
            )}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">Call Stack</p>
          <div className="space-y-1.5">
            {frames.length > 0 ? (
              frames.map((frame, index) => (
                <div
                  key={`${frame.function_name}-${index}`}
                  className={`rounded-lg border px-3 py-2 ${
                    index === frames.length - 1
                      ? 'border-accent/30 bg-accent-light/20'
                      : 'border-surface-border bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-mono text-sm font-semibold text-ink">{frame.function_name}</span>
                    <span className="text-[11px] text-ink-muted">
                      {frame.line_number ? `line ${frame.line_number}` : 'line -'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              renderEmpty('호출 스택 정보가 없습니다')
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
