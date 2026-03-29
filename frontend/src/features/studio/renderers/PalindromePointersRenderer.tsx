import type { VisualizationStepState } from '../../../types/execution';
import {
  asNumberArray,
  asPointerDetails,
  asScalarBadges,
  asStringArray,
  buildPointerMap,
} from '../utils/visualizationUtils';
import { ArrowBadge, DetailChip, ScalarBadgeList } from '../components/VisualizationCommon';

function getComparisonLabel(result: unknown, hasPointers: boolean) {
  if (!hasPointers) {
    return '대기';
  }
  if (result === true) {
    return '일치';
  }
  if (result === false) {
    return '불일치';
  }
  return '완료';
}

export function PalindromePointersRenderer({ state }: { state: VisualizationStepState }) {
  const items = asStringArray(state.payload.items);
  const activeIndices = asNumberArray(state.payload.activeIndices ?? state.activeIndices ?? []);
  const matchedIndices = asNumberArray(state.payload.matchedIndices ?? state.matchedIndices ?? []);
  const pointers = asPointerDetails(state.payload.indexPointers);
  const pointerMap = buildPointerMap(pointers);
  const scalarBadges = asScalarBadges(state.payload.scalarBadges);
  const leftIndex = typeof state.payload.leftIndex === 'number' ? state.payload.leftIndex : null;
  const rightIndex = typeof state.payload.rightIndex === 'number' ? state.payload.rightIndex : null;
  const comparisonResult = state.payload.comparisonResult;
  const hasPointers = leftIndex !== null && rightIndex !== null;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="left" value={leftIndex === null ? '-' : String(leftIndex)} />
        <DetailChip label="right" value={rightIndex === null ? '-' : String(rightIndex)} />
        <DetailChip label="비교" value={getComparisonLabel(comparisonResult, hasPointers)} />
      </div>
      <ScalarBadgeList badges={scalarBadges} />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-5 lg:grid-cols-7">
        {items.map((item, index) => {
          const isActive = activeIndices.includes(index);
          const isMatched = matchedIndices.includes(index);
          const isMismatch = isActive && comparisonResult === false;
          const classes = isMismatch
            ? 'border-rose-400 bg-rose-50 text-rose-700 ring-1 ring-rose-300'
            : isActive
              ? 'border-accent/40 bg-accent-light/30 text-accent ring-1 ring-accent/30'
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
