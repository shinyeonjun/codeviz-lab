import { useEffect, useRef } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { Play, RotateCcw } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ExecutionVisualization } from './ExecutionVisualization';
import { useExecutionStudio } from './useExecutionStudio';
import type { StudioLessonSeed } from '../../types/learning';
import { CodeEditorPanel } from './components/CodeEditorPanel';
import { ExecutionErrorPanel } from './components/ExecutionErrorPanel';
import { PlaybackControls } from './components/PlaybackControls';
import { StdoutPanel } from './components/StdoutPanel';
import { VariablesPanel } from './components/VariablesPanel';
import { useLineHighlight } from './hooks/useLineHighlight';

const PRACTICE_PRESET: StudioLessonSeed = {
  id: 'studio-free',
  title: '스튜디오',
  categoryName: '자유 작성',
  description: '수업을 선택하지 않아도 자유롭게 코드를 작성하고 실행할 수 있습니다.',
  visualizationMode: 'none',
  sourceCode: '# 자유롭게 코드를 작성하세요\nprint("Hello, World!")\n',
  difficulty: '자유',
  estimatedMinutes: 0,
  learningPoints: [],
  tags: [],
};

export function PracticeStudio() {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);
  const studio = useExecutionStudio(PRACTICE_PRESET);

  const {
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
    togglePlay,
    stepPrev,
    stepNext,
    stepReset,
    resetStudio,
  } = studio;

  useLineHighlight({
    monaco,
    editorRef,
    decorationsRef,
    lineNumber: currentStepInfo?.line_number ?? null,
  });

  useEffect(() => {
    setVisualizationMode('auto');
  }, [setVisualizationMode]);

  return (
    <div className="mx-auto w-full max-w-[1440px] px-6 py-6">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-ink">스튜디오</h2>
        <p className="mt-1 text-sm text-ink-secondary">{PRACTICE_PRESET.description}</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="rounded-lg border border-surface-border bg-white px-3 py-1.5 text-sm text-ink-secondary">
              실행 시 AI가 코드 구조를 보고 시각화 템플릿을 선택합니다.
            </div>
            <div className="flex gap-1.5">
              <Button variant="outline" onClick={resetStudio}>
                <RotateCcw size={14} />
                초기화
              </Button>
              <Button variant="primary" onClick={() => void handleRun()} disabled={isRunning || !code.trim()}>
                {isRunning ? (
                  '분석 중...'
                ) : (
                  <>
                    <Play size={14} />
                    실행
                  </>
                )}
              </Button>
            </div>
          </div>

          <CodeEditorPanel fileName="scratch.py" code={code} onChange={setCode} editorRef={editorRef} />
        </div>

        <div className="space-y-3">
          <PlaybackControls
            canControl={Boolean(execution)}
            isPlaying={isPlaying}
            stepIndex={stepIndex}
            totalSteps={totalSteps}
            onTogglePlay={togglePlay}
            onPrev={stepPrev}
            onNext={stepNext}
            onReset={stepReset}
          />

          <ExecutionErrorPanel requestError={requestError} execution={execution} />

          <Card>
            <ExecutionVisualization
              viz={execution?.visualization}
              stepIndex={stepIndex}
              mode={execution?.visualizationMode ?? visualizationMode}
            />
          </Card>

          <VariablesPanel localsSnapshot={currentStepInfo?.locals_snapshot} />
          <StdoutPanel stdoutSnapshot={currentStepInfo?.stdout_snapshot} execution={execution} />
        </div>
      </div>
    </div>
  );
}
