import { Card } from '../../../components/ui/Card';
import type { ExecutionFrame } from '../../../types/execution';
import { formatValue } from '../utils/visualizationUtils';

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
      <span className="font-mono text-sm text-ink">{formatSnapshotValue(value)}</span>
    </div>
  ));
}

function renderEmpty(message: string) {
  return <p className="py-3 text-center text-sm text-ink-faint">{message}</p>;
}

function formatSnapshotValue(value: unknown) {
  return formatValue(value);
}

function getMetadataLabel(key: string) {
  const labels: Record<string, string> = {
    localsCount: '지역 변수 수',
    globalsCount: '전역 변수 수',
    callStackDepth: '호출 스택 깊이',
  };
  return labels[key] ?? key;
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
        <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">실행 상태</h4>
        {hasMetadata && (
          <div className="flex flex-wrap gap-2">
            {Object.entries(metadata ?? {}).map(([key, value]) => (
              <span
                key={key}
                className="rounded-full border border-surface-border bg-white px-2 py-1 font-mono text-[11px] text-ink-muted"
              >
                {getMetadataLabel(key)}: {String(value)}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="max-h-[260px] space-y-3 overflow-y-auto scrollbar-thin">
        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">지역 변수</p>
          <div className="space-y-1.5">
            {locals ? (
              Object.keys(locals).length > 0 ? (
                renderSnapshotEntries(locals)
              ) : (
                renderEmpty('지역 변수가 없습니다.')
              )
            ) : (
              renderEmpty('대기 중')
            )}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">전역 변수</p>
          <div className="space-y-1.5">
            {globals ? (
              Object.keys(globals).length > 0 ? (
                renderSnapshotEntries(globals)
              ) : (
                renderEmpty('전역 변수가 없습니다.')
              )
            ) : (
              renderEmpty('대기 중')
            )}
          </div>
        </div>

        <div>
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-ink-faint">호출 스택</p>
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
                      {frame.line_number ? `${frame.line_number}번 줄` : '줄 정보 없음'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              renderEmpty('호출 스택 정보가 없습니다.')
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}
