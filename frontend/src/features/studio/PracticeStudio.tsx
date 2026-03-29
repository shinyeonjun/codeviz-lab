import { useRef } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { Play, RotateCcw } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ExecutionVisualization } from './ExecutionVisualization';
import { useExecutionStudio } from './useExecutionStudio';
import type { StudioLessonSeed } from '../../types/learning';
import type { ExecutionLanguage } from '../../types/execution';
import { CodeEditorPanel } from './components/CodeEditorPanel';
import { ExecutionErrorPanel } from './components/ExecutionErrorPanel';
import { PlaybackControls } from './components/PlaybackControls';
import { StdoutPanel } from './components/StdoutPanel';
import { VariablesPanel } from './components/VariablesPanel';
import { useLineHighlight } from './hooks/useLineHighlight';

const PRACTICE_PRESETS: Record<ExecutionLanguage, StudioLessonSeed> = {
  python: {
    id: 'studio-free-python',
    title: '스튜디오',
    categoryName: '자유 작성',
    description: '수업을 선택하지 않아도 자유롭게 코드를 작성하고 실행할 수 있습니다.',
    language: 'python',
    visualizationMode: 'auto',
    sourceCode: '# 자유롭게 코드를 작성하세요\nprint("Hello, World!")\n',
    difficulty: '자유',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  },
  c: {
    id: 'studio-free-c',
    title: '스튜디오',
    categoryName: '자유 작성',
    description: '수업을 선택하지 않아도 자유롭게 코드를 작성하고 실행할 수 있습니다.',
    language: 'c',
    visualizationMode: 'auto',
    sourceCode:
      '#include <stdio.h>\n\nint main(void) {\n    printf("Hello, C!\\n");\n    return 0;\n}\n',
    difficulty: '자유',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  },
};

const LANGUAGE_OPTIONS: { id: ExecutionLanguage; label: string }[] = [
  { id: 'python', label: 'Python' },
  { id: 'c', label: 'C' },
];

export function PracticeStudio() {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);
  const studio = useExecutionStudio(PRACTICE_PRESETS.python);

  const {
    language,
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
    handleRun,
    togglePlay,
    stepPrev,
    stepNext,
    stepReset,
    resetStudio,
    applyLesson,
  } = studio;

  useLineHighlight({
    monaco,
    editorRef,
    decorationsRef,
    lineNumber: currentStepInfo?.line_number ?? null,
  });

  const handleChangeLanguage = (nextLanguage: ExecutionLanguage) => {
    if (nextLanguage === language) {
      return;
    }
    applyLesson(PRACTICE_PRESETS[nextLanguage]);
  };

  return (
    <div className="mx-auto w-full max-w-[1440px] px-6 py-6">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-ink">스튜디오</h2>
        <p className="mt-1 text-sm text-ink-secondary">{PRACTICE_PRESETS[language].description}</p>
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="rounded-lg border border-surface-border bg-white px-3 py-1.5 text-sm text-ink-secondary">
                실행 시 AI가 코드 구조를 보고 시각화 템플릿을 선택합니다.
              </div>
              <div className="flex rounded-xl border border-surface-border bg-white p-1">
                {LANGUAGE_OPTIONS.map((option) => {
                  const isActive = option.id === language;
                  return (
                    <button
                      key={option.id}
                      type="button"
                      onClick={() => handleChangeLanguage(option.id)}
                      className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-accent-light/50 text-accent'
                          : 'text-ink-secondary hover:bg-surface-soft'
                      }`}
                    >
                      {option.label}
                    </button>
                  );
                })}
              </div>
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

          <CodeEditorPanel
            fileName={language === 'c' ? 'main.c' : 'scratch.py'}
            language={language}
            code={code}
            onChange={setCode}
            editorRef={editorRef}
          />
        </div>

        <div className="space-y-3">
          <PlaybackControls
            canControl={Boolean(execution)}
            isPlaying={isPlaying}
            stepIndex={stepIndex}
            totalSteps={totalSteps}
            playbackSpeed={studio.playbackSpeed}
            onTogglePlay={togglePlay}
            onPrev={stepPrev}
            onNext={stepNext}
            onReset={stepReset}
            onSeek={studio.seekStep}
            onPlaybackSpeedChange={studio.setPlaybackSpeed}
          />

          <ExecutionErrorPanel requestError={requestError} execution={execution} />

          <Card>
            <ExecutionVisualization
              viz={execution?.visualization}
              stepIndex={stepIndex}
              mode={execution?.visualizationMode ?? visualizationMode}
            />
          </Card>

          <VariablesPanel
            localsSnapshot={currentStepInfo?.locals_snapshot}
            globalsSnapshot={currentStepInfo?.globals_snapshot}
            callStack={currentStepInfo?.call_stack}
            metadata={currentStepInfo?.metadata}
          />
          <StdoutPanel stdoutSnapshot={currentStepInfo?.stdout_snapshot} execution={execution} />
        </div>
      </div>
    </div>
  );
}
