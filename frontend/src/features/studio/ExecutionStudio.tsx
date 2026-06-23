import { useEffect, useMemo, useRef, useState } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { ArrowLeft, Play, RotateCcw } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import type { LearningLesson, StudioLessonSeed } from '../../types/learning';
import type { ExecutionStudioController } from './useExecutionStudio';
import { CodeEditorPanel } from './components/CodeEditorPanel';
import { ExecutionResultPanel } from './components/ExecutionResultPanel';
import { ResizableStudioLayout } from './components/ResizableStudioLayout';
import { StdoutPanel } from './components/StdoutPanel';
import { useLineHighlight } from './hooks/useLineHighlight';
import { getEditorFileName } from './utils/languageUtils';
import { resolveLessonCode } from './utils/lessonLanguageVariants';
import type { ExecutionLanguage } from '../../types/execution';

type LearningStage = 'learn' | 'implement';

interface ExecutionStudioProps {
  lesson: LearningLesson;
  studio: ExecutionStudioController;
  onBackHome: () => void;
  isSelectingLesson: boolean;
}

const STAGE_OPTIONS: { id: LearningStage; label: string }[] = [
  { id: 'learn', label: '학습' },
  { id: 'implement', label: '직접 구현' },
];

const LANGUAGE_OPTIONS: { id: ExecutionLanguage; label: string }[] = [
  { id: 'python', label: 'Python' },
  { id: 'java', label: 'Java' },
  { id: 'c', label: 'C' },
];

function resolveStageVisualizationMode(lesson: LearningLesson): string {
  return lesson.visualizationMode.startsWith('showcase-') ? lesson.visualizationMode : 'auto';
}

function resolveStageCode(
  lesson: LearningLesson,
  stage: LearningStage,
  language: ExecutionLanguage,
): string {
  return resolveLessonCode(lesson, stage, language);
}

function buildStageSeed(
  lesson: LearningLesson,
  stage: LearningStage,
  language: ExecutionLanguage,
): StudioLessonSeed {
  if (stage === 'implement') {
    return {
      id: `${lesson.id}:implement`,
      title: lesson.implementationChallenge.title,
      categoryName: lesson.categoryName,
      description: lesson.implementationChallenge.prompt,
      language,
      visualizationMode: resolveStageVisualizationMode(lesson),
      sourceCode: resolveStageCode(lesson, stage, language),
      difficulty: lesson.difficulty,
      estimatedMinutes: lesson.estimatedMinutes,
      learningPoints: lesson.implementationChallenge.checkpoints,
      tags: lesson.tags,
    };
  }

  return {
    id: `${lesson.id}:learn`,
    title: lesson.learningContent.title,
    categoryName: lesson.categoryName,
    description: lesson.learningContent.summary,
    language,
    visualizationMode: resolveStageVisualizationMode(lesson),
    sourceCode: resolveStageCode(lesson, stage, language),
    difficulty: lesson.difficulty,
    estimatedMinutes: lesson.estimatedMinutes,
    learningPoints: lesson.learningContent.conceptPoints,
    tags: lesson.tags,
  };
}

export function ExecutionStudio({
  lesson,
  studio,
  onBackHome,
  isSelectingLesson,
}: ExecutionStudioProps) {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);
  const [activeStage, setActiveStage] = useState<LearningStage>('learn');
  const [activeLanguage, setActiveLanguage] = useState<ExecutionLanguage>(lesson.language);
  const supportedLanguages = useMemo(
    () => lesson.supportedLanguages?.length ? lesson.supportedLanguages : LANGUAGE_OPTIONS.map((option) => option.id),
    [lesson.supportedLanguages],
  );
  const availableLanguageOptions = useMemo(
    () => LANGUAGE_OPTIONS.filter((option) => supportedLanguages.includes(option.id)),
    [supportedLanguages],
  );

  const {
    code,
    language,
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
  } = studio;

  useLineHighlight({
    monaco,
    editorRef,
    decorationsRef,
    lineNumber: currentStepInfo?.line_number ?? null,
  });

  useEffect(() => {
    setActiveStage('learn');
    setActiveLanguage(supportedLanguages.includes(lesson.language) ? lesson.language : supportedLanguages[0] ?? 'python');
  }, [lesson.id, lesson.language, supportedLanguages]);

  useEffect(() => {
    studio.applyLesson(buildStageSeed(lesson, activeStage, activeLanguage));
    // stage 또는 lesson 변경 시에만 에디터 seed를 맞춘다.
    // studio 객체는 렌더마다 새 참조가 될 수 있어 의존성에서 제외한다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeLanguage, activeStage, lesson.id]);

  return (
    <div className="mx-auto w-full max-w-[1440px] px-6 py-6">
      <div className="mb-5">
        <button
          type="button"
          onClick={onBackHome}
          className="mb-2 inline-flex items-center gap-1 text-sm text-ink-muted transition-colors hover:text-accent"
        >
          <ArrowLeft size={14} />
          돌아가기
        </button>
        <h2 className="text-2xl font-bold text-ink">{lesson.title}</h2>
        <p className="mt-1 text-sm text-ink-secondary">{lesson.description}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {lesson.tags.map((tag) => (
            <span key={tag} className="rounded-full bg-surface-muted px-2.5 py-1 text-xs text-ink-muted">
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {STAGE_OPTIONS.map((stage) => {
            const isActive = stage.id === activeStage;
            return (
              <button
                key={stage.id}
                type="button"
                onClick={() => setActiveStage(stage.id)}
                className={`rounded-xl border px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'border-accent/40 bg-accent-light/40 text-accent'
                    : 'border-surface-border bg-white text-ink-secondary hover:bg-surface-soft'
                }`}
              >
                {stage.label}
              </button>
            );
          })}
        </div>
        <div className="mt-2 flex flex-wrap gap-2">
          {availableLanguageOptions.map((option) => {
            const isActive = option.id === activeLanguage;
            return (
              <button
                key={option.id}
                type="button"
                onClick={() => setActiveLanguage(option.id)}
                className={`rounded-xl border px-3 py-1.5 text-sm font-medium transition-colors ${
                  isActive
                    ? 'border-accent/40 bg-accent-light/40 text-accent'
                    : 'border-surface-border bg-white text-ink-secondary hover:bg-surface-soft'
                }`}
              >
                {option.label}
              </button>
            );
          })}
        </div>
      </div>

      <ResizableStudioLayout
        left={(
          <div className="space-y-3">
            <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
              <div className="flex min-w-0 flex-wrap items-center gap-2 text-xs text-ink-muted">
                <span className="rounded-lg border border-surface-border bg-white px-3 py-1.5">
                  AI가 trace를 분석해 시각화 템플릿을 선택합니다.
                </span>
                {isSelectingLesson && <span>학습을 전환하는 중입니다.</span>}
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
              fileName={getEditorFileName(language, 'main')}
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
