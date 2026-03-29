import type { VisualizationStepState } from '../../../types/execution';
import {
  asNumberArray,
  asPointerDetails,
  asScalarBadges,
  asStringArray,
  buildPointerMap,
} from '../utils/visualizationUtils';
import { ArrowBadge, DetailChip, ScalarBadgeList } from '../components/VisualizationCommon';

export function ArrayCellsRenderer({ state }: { state: VisualizationStepState }) {
  const items = asStringArray(state.payload.items);
  const activeIndices = asNumberArray(state.payload.activeIndices ?? state.activeIndices ?? []);
  const matchedIndices = asNumberArray(state.payload.matchedIndices ?? state.matchedIndices ?? []);
  const pointers = asPointerDetails(state.payload.indexPointers);
  const pointerMap = buildPointerMap(pointers);
  const scalarBadges = asScalarBadges(state.payload.scalarBadges);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {activeIndices.length > 0 && <DetailChip label="active" value={activeIndices.join(', ')} />}
      </div>
      <ScalarBadgeList badges={scalarBadges} />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 lg:grid-cols-6">
        {items.map((item, index) => {
          const isActive = activeIndices.includes(index);
          const isMatched = matchedIndices.includes(index);
          const classes = isActive
            ? 'border-ink bg-surface-soft text-ink ring-1 ring-ink'
            : isMatched
              ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
              : 'border-surface-border bg-white text-ink';

          return (
            <div key={`${item}-${index}`} className={`rounded-xl border p-3 text-center transition-all ${classes}`}>
              <div className="mb-2 flex min-h-[32px] items-end justify-center gap-1">
                {(pointerMap.get(index) ?? []).map((pointer) => (
                  <ArrowBadge key={pointer.name} label={pointer.name} />
                ))}
              </div>
              <div className="font-mono text-xs text-ink-faint">[{index}]</div>
              <div className="mt-2 font-mono text-lg font-semibold">{item}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
