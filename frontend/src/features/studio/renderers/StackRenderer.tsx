import type { VisualizationStepState } from '../../../types/execution';
import {
  asScalarBadges,
  asStringArray,
  formatValue,
} from '../utils/visualizationUtils';
import { ArrowBadge, DetailChip, ScalarBadgeList } from '../components/VisualizationCommon';

export function StackRenderer({ state }: { state: VisualizationStepState }) {
  const items = asStringArray(state.payload.items);
  const topIndex = typeof state.payload.topIndex === 'number' ? state.payload.topIndex : null;
  const operation = typeof state.payload.operation === 'string' ? state.payload.operation : 'peek';
  const scalarBadges = asScalarBadges(state.payload.scalarBadges);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="operation" value={operation} />
        <DetailChip label="size" value={String(state.payload.size ?? items.length)} />
        {state.payload.topValue !== undefined && state.payload.topValue !== null && (
          <DetailChip label="top" value={formatValue(state.payload.topValue)} />
        )}
        {state.payload.pushedValue !== undefined && state.payload.pushedValue !== null && (
          <DetailChip label="push" value={formatValue(state.payload.pushedValue)} />
        )}
        {state.payload.poppedValue !== undefined && state.payload.poppedValue !== null && (
          <DetailChip label="pop" value={formatValue(state.payload.poppedValue)} />
        )}
      </div>
      <ScalarBadgeList badges={scalarBadges} />
      <div className="flex min-h-56 items-end justify-center">
        <div className="flex w-48 flex-col-reverse gap-2">
          {items.map((item, index) => {
            const actualIndex = items.length - 1 - index;
            const isTop = topIndex === actualIndex;
            const classes = isTop ? 'border-ink bg-surface-soft ring-1 ring-ink' : 'border-surface-border bg-white';

            return (
              <div
                key={`${item}-${actualIndex}`}
                className={`rounded-xl border px-4 py-3 text-center transition-all ${classes}`}
              >
                <div className="mb-1 flex min-h-[26px] items-center justify-center">
                  {isTop ? <ArrowBadge label="top" /> : null}
                </div>
                <div className="text-[11px] text-ink-muted">{isTop ? 'top' : 'stack'}</div>
                <div className={`mt-1 font-mono text-sm ${isTop ? 'font-bold text-ink' : 'font-semibold text-ink-secondary'}`}>{item}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
