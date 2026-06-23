import type {
  ExecutionLanguage,
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
import { FlowchartRenderer } from './renderers/FlowchartRenderer';
import { HybridRenderer } from './renderers/HybridRenderer';
import { AlgorithmShowcaseRenderer } from './renderers/AlgorithmShowcaseRenderer';

type VisualizationProps = {
  viz?: VisualizationData | null;
  stepIndex: number;
  mode?: VisualizationRequestMode | VisualizationMode;
  language?: ExecutionLanguage;
  hasExecution?: boolean;
  hasTraceSteps?: boolean;
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
  flowchart: FlowchartRenderer,
  hybrid: HybridRenderer,
  'algorithm-showcase': AlgorithmShowcaseRenderer,
};

export function ExecutionVisualization({
  viz,
  stepIndex,
  mode,
  language,
  hasExecution = false,
  hasTraceSteps = false,
}: VisualizationProps) {
  if (!viz?.stepStates?.length) {
    if (hasExecution && language === 'java' && !hasTraceSteps) {
      return (
        <div className="flex h-48 flex-col items-center justify-center gap-2 text-center text-sm text-ink-muted">
          <p>Java는 현재 실행 결과 확인을 우선 지원합니다.</p>
          <p className="text-xs text-ink-faint">단계별 trace 시각화는 Java runner 보강 후 연결됩니다.</p>
        </div>
      );
    }

    if (hasExecution && !hasTraceSteps) {
      return (
        <div className="flex h-48 flex-col items-center justify-center gap-2 text-center text-sm text-ink-muted">
          <p>실행은 완료됐지만 표시할 trace 단계가 없습니다.</p>
          <p className="text-xs text-ink-faint">컴파일 실패, 실행 제한, runner 제약 여부를 확인해 주세요.</p>
        </div>
      );
    }

    if (mode === 'none') {
      return (
        <div className="flex h-48 flex-col items-center justify-center gap-2 text-center text-sm text-ink-muted">
          <p>이 수업은 차트형 시각화보다 코드 추적 중심으로 진행됩니다.</p>
          <p className="text-xs text-ink-faint">오른쪽 실행 상태에서 현재 실행 중 값을 확인하세요.</p>
        </div>
      );
    }

    return (
      <div className="flex h-48 flex-col items-center justify-center gap-2 text-center text-sm text-ink-muted">
        <p>실행 후 시각화가 표시됩니다.</p>
        {mode === 'auto' && (
          <p className="text-xs text-ink-faint">AI 분석 결과에 따라 알맞은 템플릿이 자동 선택됩니다.</p>
        )}
      </div>
    );
  }

  const state = getCurrentState(viz, stepIndex);
  const Renderer = KIND_RENDERERS[viz.kind];

  if (!Renderer) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-ink-muted">
        지원하지 않는 시각화입니다. [{viz.kind}]
      </div>
    );
  }

  return (
    <div className="h-full min-h-0">
      <Renderer state={state} />
    </div>
  );
}
