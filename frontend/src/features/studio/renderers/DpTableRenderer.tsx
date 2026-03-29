import { motion } from 'framer-motion';
import type { VisualizationStepState } from '../../../types/execution';
import { asCellKeys, asMatrix, asScalarBadges } from '../utils/visualizationUtils';
import { DetailChip, ScalarBadgeList } from '../components/VisualizationCommon';

export function DpTableRenderer({ state }: { state: VisualizationStepState }) {
  const matrix = asMatrix(state.payload.matrix);
  const activeCells = asCellKeys(state.payload.activeCells);
  const matchedCells = asCellKeys(state.payload.matchedCells);
  const scalarBadges = asScalarBadges(state.payload.scalarBadges);
  const activeCellLabels = Array.from(activeCells).slice(0, 4);

  return (
    <div className="space-y-4 overflow-x-auto">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="rows" value={String(state.payload.rows ?? matrix.length)} />
        <DetailChip
          label="cols"
          value={String(state.payload.cols ?? Math.max(...matrix.map((row) => row.length), 0))}
        />
        <DetailChip label="active" value={String(state.payload.activeCellCount ?? activeCells.size)} />
        {activeCellLabels.length > 0 && <DetailChip label="cells" value={activeCellLabels.join(', ')} />}
      </div>
      <ScalarBadgeList badges={scalarBadges} />
      <motion.div layout className="space-y-2">
        {matrix.length > 0 && (
          <div className="flex gap-2 pl-9">
            {matrix[0].map((_, colIndex) => (
              <div key={`col-${colIndex}`} className="flex h-6 w-12 items-center justify-center text-[11px] text-ink-faint">
                {colIndex}
              </div>
            ))}
          </div>
        )}
        {matrix.map((row, rowIndex) => (
          <motion.div layout key={`row-${rowIndex}`} className="flex items-center gap-2">
            <div className="flex h-12 w-7 items-center justify-center text-[11px] text-ink-faint">{rowIndex}</div>
            {row.map((value, colIndex) => {
              const key = `${rowIndex}:${colIndex}`;
              const isActive = activeCells.has(key);
              const isMatched = matchedCells.has(key);
              const classes = isActive
                ? 'border-ink bg-surface-soft text-ink ring-1 ring-ink'
                : isMatched
                  ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
                  : 'border-surface-border bg-white text-ink';

              return (
                <motion.div 
                  key={key} 
                  layout
                  transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                  className={`flex h-12 w-12 items-center justify-center rounded-lg border transition-colors ${classes}`}
                >
                  <span className={`font-mono text-sm ${isActive ? 'font-bold text-ink' : 'font-semibold text-ink-secondary'}`}>{String(value)}</span>
                </motion.div>
              );
            })}
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
