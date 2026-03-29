export type VisualizationKind =
  | 'array-bars'
  | 'array-cells'
  | 'stack-vertical'
  | 'queue-horizontal'
  | 'call-stack'
  | 'dp-table'
  | 'tree-binary'
  | 'graph-node-edge';

export type VisualizationMode = string;
export type VisualizationRequestMode = string;

export interface ExecutionStep {
  step_index: number;
  line_number: number;
  event_type: string;
  function_name: string;
  locals_snapshot: Record<string, unknown>;
  stdout_snapshot: string;
  error_message: string | null;
}

export interface VisualizationStepState {
  step_index: number;
  line_number: number;
  values?: number[];
  activeIndices?: number[];
  matchedIndices?: number[];
  payload: Record<string, unknown>;
  message?: string | null;
}

export interface VisualizationData {
  kind: VisualizationKind;
  sourceVariable?: string | null;
  stepStates: VisualizationStepState[];
  metadata?: Record<string, unknown>;
}

export interface ExecutionResult {
  run_id: string;
  language: string;
  visualizationMode: VisualizationMode;
  status: string;
  source_code: string;
  stdin: string;
  stdout: string;
  stderr: string;
  error_message?: string | null;
  step_count: number;
  created_at: string;
  completed_at?: string | null;
  steps: ExecutionStep[];
  visualization?: VisualizationData | null;
}
