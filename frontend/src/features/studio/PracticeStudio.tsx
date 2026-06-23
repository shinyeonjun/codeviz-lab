import { useRef } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { Play, RotateCcw } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { useExecutionStudio } from './useExecutionStudio';
import type { StudioLessonSeed } from '../../types/learning';
import type { ExecutionLanguage } from '../../types/execution';
import { CodeEditorPanel } from './components/CodeEditorPanel';
import { ExecutionResultPanel } from './components/ExecutionResultPanel';
import { ResizableStudioLayout } from './components/ResizableStudioLayout';
import { StdoutPanel } from './components/StdoutPanel';
import { useLineHighlight } from './hooks/useLineHighlight';
import { getEditorFileName } from './utils/languageUtils';

const PRACTICE_PRESETS: Record<ExecutionLanguage, StudioLessonSeed> = {
  python: {
    id: 'studio-free-python',
    title: '스튜디오',
    categoryName: '자유 작성',
    description: '수업과 상관없이 원하는 코드를 작성하고 실행 과정을 시각화합니다.',
    language: 'python',
    visualizationMode: 'auto',
    sourceCode: '# 자유롭게 코드를 작성하세요.\nprint("Hello, World!")\n',
    difficulty: '자유',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  },
  c: {
    id: 'studio-free-c',
    title: '스튜디오',
    categoryName: '자유 작성',
    description: '수업과 상관없이 원하는 C 코드를 작성하고 실행 과정을 시각화합니다.',
    language: 'c',
    visualizationMode: 'auto',
    sourceCode:
      '#include <stdio.h>\n\nint main(void) {\n    printf("Hello, C!\\n");\n    return 0;\n}\n',
    difficulty: '자유',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  },
  java: {
    id: 'studio-free-java',
    title: '스튜디오',
    categoryName: '자유 작성',
    description: '수업과 관계없이 원하는 Java 코드를 작성하고 실행 결과를 확인합니다.',
    language: 'java',
    visualizationMode: 'auto',
    sourceCode:
      'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, Java!");\n    }\n}\n',
    difficulty: '자유',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  },
};

const LANGUAGE_OPTIONS: { id: ExecutionLanguage; label: string }[] = [
  { id: 'python', label: 'Python' },
  { id: 'c', label: 'C' },
  { id: 'java', label: 'Java' },
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
    showFlowchart,
    isRunning,
    execution,
    currentStepInfo,
    stepIndex,
    isPlaying,
    requestError,
    totalSteps,
    setCode,
    setShowFlowchart,
    handleRun,
    togglePlay,
    stepPrev,
    stepNext,
    stepReset,
    stepEnd,
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

      <ResizableStudioLayout
        left={(
          <div className="space-y-3">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="flex min-w-0 flex-wrap items-center gap-2">
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
              <label className="inline-flex shrink-0 cursor-pointer items-center gap-2 rounded-lg border border-surface-border bg-white px-3 py-1.5 text-xs text-ink-secondary transition-colors hover:bg-surface-soft">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-surface-border text-accent focus:ring-accent"
                  checked={showFlowchart}
                  onChange={(event) => setShowFlowchart(event.target.checked)}
                />
                <span>흐름도 함께 보기</span>
              </label>
              <div className="flex shrink-0 gap-2">
                <Button variant="outline" className="min-w-[96px]" onClick={resetStudio}>
                  <RotateCcw size={14} />
                  초기화
                </Button>
                <Button
                  variant="primary"
                  className="min-w-[96px]"
                  onClick={() => void handleRun()}
                  disabled={isRunning || !code.trim()}
                >
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
              fileName={getEditorFileName(language)}
              language={language}
              code={code}
              onChange={setCode}
              editorRef={editorRef}
            />

            <StdoutPanel
              stdoutSnapshot={currentStepInfo?.stdout_snapshot}
              execution={execution}
            />
          </div>
        )}
        right={(
          <ExecutionResultPanel
            execution={execution}
            requestError={requestError}
            currentStepInfo={currentStepInfo}
            stepIndex={stepIndex}
            totalSteps={totalSteps}
            isPlaying={isPlaying}
            playbackSpeed={studio.playbackSpeed}
            visualizationMode={visualizationMode}
            language={language}
            onTogglePlay={togglePlay}
            onPrev={stepPrev}
            onNext={stepNext}
            onReset={stepReset}
            onJumpToEnd={stepEnd}
            onSeek={studio.seekStep}
            onPlaybackSpeedChange={studio.setPlaybackSpeed}
            showStdout={false}
          />
        )}
      />
    </div>
  );
}
