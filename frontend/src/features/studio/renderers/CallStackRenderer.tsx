import type { VisualizationStepState } from '../../../types/execution';
import { asNodeList } from '../utils/visualizationUtils';
import { DetailChip } from '../components/VisualizationCommon';

export function CallStackRenderer({ state }: { state: VisualizationStepState }) {
  const frames = asNodeList(state.payload.frames);
  const activeFunction = typeof state.payload.activeFunction === 'string' ? state.payload.activeFunction : '';
  const eventType = typeof state.payload.eventType === 'string' ? state.payload.eventType : 'line';
  const activeDepth =
    typeof state.payload.activeDepth === 'number' ? state.payload.activeDepth : frames.length - 1;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="event" value={eventType} />
        <DetailChip label="frames" value={String(state.payload.frameCount ?? frames.length)} />
        <DetailChip label="depth" value={String(activeDepth)} />
        {activeFunction && <DetailChip label="active" value={activeFunction} />}
      </div>
      <div className="flex flex-col-reverse gap-2">
        {frames.map((frame, index) => {
          const name = String(frame.functionName ?? `frame-${index}`);
          const isActive = Boolean(frame.isActive);
          const classes = isActive ? 'border-ink bg-surface-soft ring-1 ring-ink' : 'border-surface-border bg-white';

          return (
            <div key={`${name}-${index}`} className="space-y-1">
              <div
                className={`rounded-xl border px-4 py-3 transition-all ${classes}`}
              >
                <div className="text-xs text-ink-muted">depth {String(frame.depth ?? index)}</div>
                <div className={`mt-1 font-mono text-sm ${isActive ? 'font-bold text-ink' : 'font-semibold text-ink-secondary'}`}>{name}</div>
              </div>
              {index < frames.length - 1 && (
                <div className="flex justify-center text-xs text-ink-faint">↑ return / ↓ call</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
