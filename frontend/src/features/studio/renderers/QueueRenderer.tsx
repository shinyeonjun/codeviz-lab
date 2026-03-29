import { AnimatePresence, motion } from 'framer-motion';
import type { VisualizationStepState } from '../../../types/execution';
import {
  asScalarBadges,
  asStringArray,
  formatValue,
} from '../utils/visualizationUtils';
import { ArrowBadge, DetailChip, ScalarBadgeList } from '../components/VisualizationCommon';

export function QueueRenderer({ state }: { state: VisualizationStepState }) {
  const items = asStringArray(state.payload.items);
  const frontIndex = typeof state.payload.frontIndex === 'number' ? state.payload.frontIndex : null;
  const rearIndex = typeof state.payload.rearIndex === 'number' ? state.payload.rearIndex : null;
  const operation = typeof state.payload.operation === 'string' ? state.payload.operation : 'peek';
  const scalarBadges = asScalarBadges(state.payload.scalarBadges);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="operation" value={operation} />
        <DetailChip label="size" value={String(state.payload.size ?? items.length)} />
        {state.payload.frontValue !== undefined && state.payload.frontValue !== null && (
          <DetailChip label="front" value={formatValue(state.payload.frontValue)} />
        )}
        {state.payload.rearValue !== undefined && state.payload.rearValue !== null && (
          <DetailChip label="rear" value={formatValue(state.payload.rearValue)} />
        )}
        {state.payload.enqueuedValue !== undefined && state.payload.enqueuedValue !== null && (
          <DetailChip label="enqueue" value={formatValue(state.payload.enqueuedValue)} />
        )}
        {state.payload.dequeuedValue !== undefined && state.payload.dequeuedValue !== null && (
          <DetailChip label="dequeue" value={formatValue(state.payload.dequeuedValue)} />
        )}
      </div>
      <ScalarBadgeList badges={scalarBadges} />
      <div className="flex flex-wrap justify-center gap-2">
        <AnimatePresence mode="popLayout">
          {items.map((item, index) => {
            const isFront = frontIndex === index;
            const isRear = rearIndex === index;
            const classes = isFront || isRear ? 'border-accent/30 bg-accent-light/40' : 'border-surface-border bg-white';

            return (
              <motion.div 
                key={`${item}-${index}`} 
                layout
                initial={{ opacity: 0, x: 20, scale: 0.9 }}
                animate={{ opacity: 1, x: 0, scale: 1 }}
                exit={{ opacity: 0, x: -20, scale: 0.9 }}
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                className={`min-w-[84px] rounded-xl border px-4 py-3 text-center transition-colors ${classes}`}
              >
                <div className="mb-1 flex min-h-[26px] items-center justify-center gap-1">
                  {isFront ? <ArrowBadge label="front" /> : null}
                  {isRear ? <ArrowBadge label="rear" /> : null}
                </div>
                <div className="text-[11px] text-ink-muted">
                  {isFront && isRear ? 'front · rear' : isFront ? 'front' : isRear ? 'rear' : 'queue'}
                </div>
                <div className="mt-1 font-mono text-sm font-semibold text-ink">{item}</div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
