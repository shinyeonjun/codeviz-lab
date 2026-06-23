import type { ReactNode } from 'react';
import type {
  ExecutionLanguage,
  ExecutionResult,
  ExecutionStep,
  VisualizationMode,
  VisualizationRequestMode,
} from '../../../types/execution';
import { ExecutionVisualization } from '../ExecutionVisualization';
import { ExecutionErrorPanel } from './ExecutionErrorPanel';
import { PlaybackControls } from './PlaybackControls';
import { ResizableVisualizationCard } from './ResizableVisualizationCard';
import { StdoutPanel } from './StdoutPanel';
import { VariablesPanel } from './VariablesPanel';

interface ExecutionResultPanelProps {
  execution: ExecutionResult | null;
  requestError: string | null;
  currentStepInfo: ExecutionStep | null;
  stepIndex: number;
  totalSteps: number;
  isPlaying: boolean;
  playbackSpeed: number;
  visualizationMode: VisualizationMode | VisualizationRequestMode;
  language: ExecutionLanguage;
  onTogglePlay: () => void;
  onPrev: () => void;
  onNext: () => void;
  onReset: () => void;
  onJumpToEnd: () => void;
  onSeek: (value: number) => void;
  onPlaybackSpeedChange: (value: number) => void;
  stdoutTitle?: string;
  stdoutEmptyText?: string;
  showStdout?: boolean;
  children?: ReactNode;
}

export function ExecutionResultPanel({
  execution,
  requestError,
  currentStepInfo,
  stepIndex,
  totalSteps,
  isPlaying,
  playbackSpeed,
  visualizationMode,
  language,
  onTogglePlay,
  onPrev,
  onNext,
  onReset,
  onJumpToEnd,
  onSeek,
  onPlaybackSpeedChange,
  stdoutTitle,
  stdoutEmptyText,
  showStdout = true,
  children,
}: ExecutionResultPanelProps) {
  return (
    <div className="space-y-3">
      <PlaybackControls
        canControl={Boolean(execution && totalSteps > 0)}
        isPlaying={isPlaying}
        stepIndex={stepIndex}
        totalSteps={totalSteps}
        playbackSpeed={playbackSpeed}
        onTogglePlay={onTogglePlay}
        onPrev={onPrev}
        onNext={onNext}
        onReset={onReset}
        onJumpToEnd={onJumpToEnd}
        onSeek={onSeek}
        onPlaybackSpeedChange={onPlaybackSpeedChange}
      />

      <ExecutionErrorPanel requestError={requestError} execution={execution} />

      <ResizableVisualizationCard>
        <ExecutionVisualization
          viz={execution?.visualization}
          stepIndex={stepIndex}
          mode={execution?.visualizationMode ?? visualizationMode}
          language={execution?.language ?? language}
          hasExecution={Boolean(execution)}
          hasTraceSteps={Boolean(execution?.steps.length)}
        />
      </ResizableVisualizationCard>

      <VariablesPanel
        localsSnapshot={currentStepInfo?.locals_snapshot}
        globalsSnapshot={currentStepInfo?.globals_snapshot}
        callStack={currentStepInfo?.call_stack}
        metadata={currentStepInfo?.metadata}
      />

      {children}

      {showStdout && (
        <StdoutPanel
          title={stdoutTitle}
          emptyText={stdoutEmptyText}
          stdoutSnapshot={currentStepInfo?.stdout_snapshot}
          execution={execution}
        />
      )}
    </div>
  );
}
