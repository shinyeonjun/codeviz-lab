import { useEffect, useMemo, useState } from 'react';
import { executeCode, getErrorMessage, shouldReportError } from '../../lib/api';
import type {
  ExecutionLanguage,
  ExecutionResult,
  VisualizationRequestMode,
} from '../../types/execution';
import type { StudioLessonSeed } from '../../types/learning';

export interface ExecutionStudioController {
  language: ExecutionLanguage;
  code: string;
  visualizationMode: VisualizationRequestMode;
  showFlowchart: boolean;
  isRunning: boolean;
  execution: ExecutionResult | null;
  currentStepInfo: ExecutionResult['steps'][number] | null;
  stepIndex: number;
  isPlaying: boolean;
  playbackSpeed: number;
  requestError: string | null;
  totalSteps: number;
  setLanguage: (value: ExecutionLanguage) => void;
  setCode: (value: string) => void;
  setShowFlowchart: (value: boolean) => void;
  setPlaybackSpeed: (value: number) => void;
  handleRun: () => Promise<void>;
  togglePlay: () => void;
  stepPrev: () => void;
  stepNext: () => void;
  stepReset: () => void;
  stepEnd: () => void;
  seekStep: (value: number) => void;
  resetStudio: () => void;
  applyLesson: (lesson: StudioLessonSeed) => void;
}

const BASE_PLAYBACK_INTERVAL_MS = 600;
const SHOWCASE_MODE_PREFIX = 'showcase-';

export function useExecutionStudio(initialLesson: StudioLessonSeed): ExecutionStudioController {
  const [language, setLanguage] = useState<ExecutionLanguage>(initialLesson.language);
  const [code, setCode] = useState(initialLesson.sourceCode);
  const [visualizationMode, setVisualizationMode] = useState<VisualizationRequestMode>(
    initialLesson.visualizationMode,
  );
  const [showFlowchart, setShowFlowchart] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [execution, setExecution] = useState<ExecutionResult | null>(null);
  const [stepIndex, setStepIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);
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
      }, Math.max(75, Math.round(BASE_PLAYBACK_INTERVAL_MS / playbackSpeed)));
    } else if (execution && stepIndex >= execution.steps.length - 1) {
      setIsPlaying(false);
    }

    return () => {
      if (intervalId) {
        window.clearInterval(intervalId);
      }
    };
  }, [execution, isPlaying, playbackSpeed, stepIndex]);

  const resetStudio = () => {
    setExecution(null);
    setStepIndex(-1);
    setIsPlaying(false);
    setRequestError(null);
  };

  const updateCode = (value: string) => {
    setCode(value);
    resetStudio();
  };

  const updateLanguage = (value: ExecutionLanguage) => {
    setLanguage(value);
    resetStudio();
  };

  const applyLesson = (lesson: StudioLessonSeed) => {
    setLanguage(lesson.language);
    setCode(lesson.sourceCode);
    setVisualizationMode(lesson.visualizationMode);
    resetStudio();
  };

  const handleRun = async () => {
    setIsRunning(true);
    resetStudio();

    try {
      const requestedVisualizationMode = visualizationMode.startsWith(SHOWCASE_MODE_PREFIX)
        ? visualizationMode
        : showFlowchart ? 'hybrid' : visualizationMode;

      const result = await executeCode({
        language,
        sourceCode: code,
        visualizationMode: requestedVisualizationMode,
      });

      setExecution(result);
      if (result.steps.length > 0) {
        setStepIndex(0);
      }
    } catch (error) {
      if (shouldReportError(error)) {
        console.error(error);
      }
      setRequestError(
        getErrorMessage(error, '실행 중 오류가 발생했습니다. 백엔드 서버가 켜져 있는지 확인해 주세요.'),
      );
    } finally {
      setIsRunning(false);
    }
  };

  return {
    language,
    code,
    visualizationMode,
    showFlowchart,
    isRunning,
    execution,
    currentStepInfo,
    stepIndex,
    isPlaying,
    playbackSpeed,
    requestError,
    totalSteps,
    setLanguage: updateLanguage,
    setCode: updateCode,
    setShowFlowchart,
    setPlaybackSpeed,
    handleRun,
    togglePlay: () => {
      if (!execution || totalSteps === 0) {
        return;
      }

      if (!isPlaying && stepIndex >= totalSteps - 1) {
        setStepIndex(0);
      }

      setIsPlaying((prev) => !prev);
    },
    stepPrev: () => {
      setIsPlaying(false);
      setStepIndex((prev) => Math.max(0, prev - 1));
    },
    stepNext: () => {
      setIsPlaying(false);
      setStepIndex((prev) => Math.min(totalSteps - 1, prev + 1));
    },
    stepReset: () => {
      setIsPlaying(false);
      setStepIndex(0);
    },
    stepEnd: () => {
      if (totalSteps === 0) {
        return;
      }

      setIsPlaying(false);
      setStepIndex(totalSteps - 1);
    },
    seekStep: (value: number) => {
      if (totalSteps === 0) {
        return;
      }

      setIsPlaying(false);
      setStepIndex(Math.min(totalSteps - 1, Math.max(0, value)));
    },
    resetStudio,
    applyLesson,
  };
}
