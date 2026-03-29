import { useEffect, useMemo, useState } from 'react';
import { executeCode } from '../../lib/api';
import type {
  ExecutionResult,
  VisualizationRequestMode,
} from '../../types/execution';
import type { StudioLessonSeed } from '../../types/learning';

export interface ExecutionStudioController {
  code: string;
  visualizationMode: VisualizationRequestMode;
  isRunning: boolean;
  execution: ExecutionResult | null;
  currentStepInfo: ExecutionResult['steps'][number] | null;
  stepIndex: number;
  isPlaying: boolean;
  requestError: string | null;
  totalSteps: number;
  setCode: (value: string) => void;
  setVisualizationMode: (value: VisualizationRequestMode) => void;
  handleRun: () => Promise<void>;
  togglePlay: () => void;
  stepPrev: () => void;
  stepNext: () => void;
  stepReset: () => void;
  resetStudio: () => void;
  applyLesson: (lesson: StudioLessonSeed) => void;
}

export function useExecutionStudio(initialLesson: StudioLessonSeed): ExecutionStudioController {
  const [code, setCode] = useState(initialLesson.sourceCode);
  const [visualizationMode, setVisualizationMode] = useState<VisualizationRequestMode>(
    initialLesson.visualizationMode,
  );
  const [isRunning, setIsRunning] = useState(false);
  const [execution, setExecution] = useState<ExecutionResult | null>(null);
  const [stepIndex, setStepIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [requestError, setRequestError] = useState<string | null>(null);

  const currentStepInfo = useMemo(() => {
    if (!execution || stepIndex < 0 || stepIndex >= execution.steps.length) {
      return null;
    }

    return execution.steps[stepIndex];
  }, [execution, stepIndex]);

  const totalSteps = execution?.step_count || execution?.steps.length || 0;

  useEffect(() => {
    let intervalId: number | undefined;

    if (isPlaying && execution && stepIndex < execution.steps.length - 1) {
      intervalId = window.setInterval(() => {
        setStepIndex((prev) => prev + 1);
      }, 600);
    } else if (execution && stepIndex >= execution.steps.length - 1) {
      setIsPlaying(false);
    }

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [execution, isPlaying, stepIndex]);

  const resetStudio = () => {
    setExecution(null);
    setStepIndex(-1);
    setIsPlaying(false);
    setRequestError(null);
  };

  const applyLesson = (lesson: StudioLessonSeed) => {
    setCode(lesson.sourceCode);
    setVisualizationMode(lesson.visualizationMode);
    resetStudio();
  };

  const handleRun = async () => {
    setIsRunning(true);
    resetStudio();

    try {
      const result = await executeCode({
        sourceCode: code,
        visualizationMode,
      });

      setExecution(result);
      if (result.steps.length > 0) {
        setStepIndex(0);
      }
    } catch (error) {
      console.error(error);
      setRequestError(
        error instanceof Error
          ? error.message
          : '네트워크 에러가 발생했습니다. 백엔드 서버가 켜져 있는지 확인해 주세요.',
      );
    } finally {
      setIsRunning(false);
    }
  };

  return {
    code,
    visualizationMode,
    isRunning,
    execution,
    currentStepInfo,
    stepIndex,
    isPlaying,
    requestError,
    totalSteps,
    setCode,
    setVisualizationMode,
    handleRun,
    togglePlay: () => setIsPlaying((prev) => !prev),
    stepPrev: () => setStepIndex((prev) => Math.max(0, prev - 1)),
    stepNext: () => setStepIndex((prev) => Math.min(totalSteps - 1, prev + 1)),
    stepReset: () => setStepIndex(0),
    resetStudio,
    applyLesson,
  };
}
