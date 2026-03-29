import { AnimatePresence, motion } from 'framer-motion';
import type { VisualizationStepState } from '../../../types/execution';
import {
  asPointerDetails,
  asScalarBadges,
  buildPointerMap,
} from '../utils/visualizationUtils';
import { ArrowBadge, DetailChip, ScalarBadgeList } from '../components/VisualizationCommon';

export function ArrayBarsRenderer({ state }: { state: VisualizationStepState }) {
  const values = state.values ?? [];
  const activeIndices = state.activeIndices ?? [];
  const matchedIndices = state.matchedIndices ?? [];
  const pointers = asPointerDetails(state.payload.indexPointers);
  const pointerMap = buildPointerMap(pointers);
  const scalarBadges = asScalarBadges(state.payload.scalarBadges);
  const max = Math.max(...values, 10);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {activeIndices.length > 0 && <DetailChip label="active" value={activeIndices.join(', ')} />}
      </div>
      <ScalarBadgeList badges={scalarBadges} />
      <div className="flex items-end justify-center gap-2 overflow-x-auto px-2 pb-1" style={{ minHeight: '220px' }}>
        <AnimatePresence>
          {values.map((value, index) => {
            const isActive = activeIndices.includes(index);
            const isMatched = matchedIndices.includes(index);
            const color = isActive ? 'bg-ink' : isMatched ? 'bg-emerald-500' : 'bg-surface-border';
            const indexPointers = pointerMap.get(index) ?? [];

            return (
              <motion.div key={`${index}-${value}`} layout className="flex min-w-[52px] flex-col items-center">
                <div className="mb-1 flex min-h-[44px] flex-col items-center justify-end gap-0.5">
                  {indexPointers.map((pointer) => (
                    <ArrowBadge key={pointer.name} label={pointer.name} />
                  ))}
                </div>
                <span className={`mb-1 font-mono text-[11px] ${isActive ? 'text-ink font-semibold' : 'text-ink-muted'}`}>{value}</span>
                <motion.div
                  layout
                  className={`w-11 rounded-t-lg ${color} transition-colors`}
                  style={{ height: `${Math.max((value / max) * 132, 8)}px` }}
                />
                <span className="mt-2 font-mono text-[10px] text-ink-faint">[{index}]</span>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </div>
  );
}
