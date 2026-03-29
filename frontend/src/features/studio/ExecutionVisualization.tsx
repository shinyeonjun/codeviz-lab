import type {
  VisualizationData,
  VisualizationKind,
  VisualizationMode,
  VisualizationRequestMode,
  VisualizationStepState,
} from '../../types/execution';
import { ArrayBarsRenderer } from './renderers/ArrayBarsRenderer';
import { ArrayCellsRenderer } from './renderers/ArrayCellsRenderer';
import { PalindromePointersRenderer } from './renderers/PalindromePointersRenderer';
import { StackRenderer } from './renderers/StackRenderer';
import { QueueRenderer } from './renderers/QueueRenderer';
import { CallStackRenderer } from './renderers/CallStackRenderer';
import { DpTableRenderer } from './renderers/DpTableRenderer';
import { TreeRenderer } from './renderers/TreeRenderer';
import { GraphRenderer } from './renderers/GraphRenderer';

export const VISUALIZATION_MODE_OPTIONS: { id: VisualizationRequestMode; name: string }[] = [
  { id: 'auto', name: 'AI 추천' },
  { id: 'none', name: '코드 추적' },
  { id: 'array-bars', name: '배열 막대' },
  { id: 'array-cells', name: '배열 셀' },
  { id: 'palindrome-pointers', name: '팰린드롬 포인터' },
  { id: 'stack-vertical', name: '스택' },
  { id: 'queue-horizontal', name: '큐' },
  { id: 'call-stack', name: '호출 스택' },
  { id: 'dp-table', name: 'DP 테이블' },
  { id: 'tree-binary', name: '이진 트리' },
  { id: 'graph-node-edge', name: '그래프' },
];

type VisualizationProps = {
  viz?: VisualizationData | null;
  stepIndex: number;
  mode?: VisualizationRequestMode | VisualizationMode;
};

function getCurrentState(viz: VisualizationData, stepIndex: number): VisualizationStepState {
  return viz.stepStates.find((state) => state.step_index === stepIndex + 1) ?? viz.stepStates[0];
}

const KIND_RENDERERS: Record<VisualizationKind, (props: { state: VisualizationStepState }) => JSX.Element> = {
  'array-bars': ArrayBarsRenderer,
  'array-cells': ArrayCellsRenderer,
  'palindrome-pointers': PalindromePointersRenderer,
  'stack-vertical': StackRenderer,
  'queue-horizontal': QueueRenderer,
  'call-stack': CallStackRenderer,
  'dp-table': DpTableRenderer,
  'tree-binary': TreeRenderer,
  'graph-node-edge': GraphRenderer,
};

export function ExecutionVisualization({ viz, stepIndex, mode }: VisualizationProps) {
  if (!viz?.stepStates?.length) {
    if (mode === 'none') {
      return (
        <div className="flex h-48 flex-col items-center justify-center gap-2 text-center text-sm text-ink-muted">
          <p>이 수업은 차트형 시각화 대신 코드 추적 중심으로 진행됩니다.</p>
          <p className="text-xs text-ink-faint">오른쪽 변수 패널과 현재 실행 줄 강조를 같이 보세요.</p>
        </div>
      );
    }

    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 text-center text-sm text-ink-muted">
        <p>실행 후 시각화가 표시됩니다.</p>
        {mode === 'auto' && <p className="text-xs text-ink-faint">AI 추천 결과에 따라 차트가 선택됩니다.</p>}
      </div>
    );
  }

  const state = getCurrentState(viz, stepIndex);
  const Renderer = KIND_RENDERERS[viz.kind];

  if (!Renderer) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-ink-muted">
        미지원 시각화 [{viz.kind}]
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Renderer state={state} />
    </div>
  );
}
