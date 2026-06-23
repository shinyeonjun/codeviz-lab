import type { VisualizationKind, VisualizationStepState } from '../../../types/execution';
import { ArrayBarsRenderer } from './ArrayBarsRenderer';
import { ArrayCellsRenderer } from './ArrayCellsRenderer';
import { CallStackRenderer } from './CallStackRenderer';
import { DpTableRenderer } from './DpTableRenderer';
import { FlowchartRenderer } from './FlowchartRenderer';
import { GraphRenderer } from './GraphRenderer';
import { PalindromePointersRenderer } from './PalindromePointersRenderer';
import { QueueRenderer } from './QueueRenderer';
import { StackRenderer } from './StackRenderer';
import { TreeRenderer } from './TreeRenderer';

type NestedVisualization = {
  kind: VisualizationKind;
  sourceVariable?: string | null;
  state: VisualizationStepState;
  metadata?: Record<string, unknown>;
};

const STRUCTURE_RENDERERS: Partial<
  Record<VisualizationKind, (props: { state: VisualizationStepState }) => JSX.Element>
> = {
  'array-bars': ArrayBarsRenderer,
  'array-cells': ArrayCellsRenderer,
  'palindrome-pointers': PalindromePointersRenderer,
  'stack-vertical': StackRenderer,
  'queue-horizontal': QueueRenderer,
  'call-stack': CallStackRenderer,
  'dp-table': DpTableRenderer,
  'tree-binary': TreeRenderer,
  'graph-node-edge': GraphRenderer,
  flowchart: FlowchartRenderer,
};

export function HybridRenderer({ state }: { state: VisualizationStepState }) {
  const flowchart = asNestedVisualization(state.payload.flowchart);
  const structure = asNestedVisualization(state.payload.structure);
  const StructureRenderer = structure ? STRUCTURE_RENDERERS[structure.kind] : null;

  if (!flowchart || !structure || !StructureRenderer) {
    return (
      <div className="rounded-xl border border-surface-border bg-white p-6 text-center text-sm text-ink-muted">
        hybrid 시각화 데이터를 표시할 수 없습니다.
      </div>
    );
  }

  return (
    <div className="grid h-full min-h-0 gap-3 2xl:grid-cols-[0.95fr_1.05fr]">
      <section className="flex min-h-0 min-w-0 flex-col rounded-lg border border-surface-border bg-white/70 p-2.5">
        <div className="mb-2.5 flex items-center justify-between gap-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">흐름</h4>
          <span className="rounded-md bg-surface-soft px-2 py-0.5 text-[11px] text-ink-muted">흐름도</span>
        </div>
        <div className="min-h-0 flex-1">
          <FlowchartRenderer state={flowchart.state} density="compact" />
        </div>
      </section>

      <section className="flex min-h-0 min-w-0 flex-col rounded-lg border border-surface-border bg-white/70 p-2.5">
        <div className="mb-2.5 flex items-center justify-between gap-3">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">상태</h4>
          <span className="rounded-md bg-surface-soft px-2 py-0.5 text-[11px] text-ink-muted">
            {getVisualizationKindLabel(structure.kind)}
          </span>
        </div>
        <div className="min-h-0 flex-1">
          <StructureRenderer state={structure.state} />
        </div>
      </section>
    </div>
  );
}

function asNestedVisualization(value: unknown): NestedVisualization | null {
  if (!value || typeof value !== 'object') {
    return null;
  }
  const record = value as Record<string, unknown>;
  const kind = record.kind;
  const state = record.state;
  if (!isVisualizationKind(kind) || !state || typeof state !== 'object') {
    return null;
  }

  return {
    kind,
    sourceVariable: typeof record.sourceVariable === 'string' ? record.sourceVariable : null,
    state: asStepState(state as Record<string, unknown>),
    metadata: isRecord(record.metadata) ? record.metadata : {},
  };
}

function asStepState(record: Record<string, unknown>): VisualizationStepState {
  return {
    step_index: asNumber(record.step_index ?? record.stepIndex),
    line_number: asNumber(record.line_number ?? record.lineNumber),
    values: Array.isArray(record.values) ? record.values.filter((item): item is number => typeof item === 'number') : [],
    activeIndices: asNumberArray(record.activeIndices ?? record.active_indices),
    matchedIndices: asNumberArray(record.matchedIndices ?? record.matched_indices),
    payload: isRecord(record.payload) ? record.payload : {},
    message: typeof record.message === 'string' ? record.message : null,
  };
}

function isVisualizationKind(value: unknown): value is VisualizationKind {
  return (
    value === 'array-bars'
    || value === 'array-cells'
    || value === 'palindrome-pointers'
    || value === 'stack-vertical'
    || value === 'queue-horizontal'
    || value === 'call-stack'
    || value === 'dp-table'
    || value === 'tree-binary'
    || value === 'graph-node-edge'
    || value === 'flowchart'
    || value === 'hybrid'
    || value === 'algorithm-showcase'
  );
}

function getVisualizationKindLabel(kind: VisualizationKind) {
  const labels: Partial<Record<VisualizationKind, string>> = {
    'array-bars': '배열 막대',
    'array-cells': '배열 셀',
    'palindrome-pointers': '팰린드롬 포인터',
    'stack-vertical': '스택',
    'queue-horizontal': '큐',
    'call-stack': '호출 스택',
    'dp-table': 'DP 테이블',
    'tree-binary': '이진 트리',
    'graph-node-edge': '그래프',
    flowchart: '흐름도',
    hybrid: '복합 시각화',
  };
  return labels[kind] ?? '알고리즘';
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}

function asNumber(value: unknown): number {
  return typeof value === 'number' ? value : 0;
}

function asNumberArray(value: unknown): number[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter((item): item is number => typeof item === 'number');
}
