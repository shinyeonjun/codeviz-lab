import { useEffect, useMemo, useRef, useState } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { ArrowLeft, Play, RotateCcw } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ExecutionVisualization } from './ExecutionVisualization';
import type { LearningLesson, StudioLessonSeed } from '../../types/learning';
import type { ExecutionStudioController } from './useExecutionStudio';
import { CodeEditorPanel } from './components/CodeEditorPanel';
import { ExecutionErrorPanel } from './components/ExecutionErrorPanel';
import { PlaybackControls } from './components/PlaybackControls';
import { StdoutPanel } from './components/StdoutPanel';
import { VariablesPanel } from './components/VariablesPanel';
import { useLineHighlight } from './hooks/useLineHighlight';

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

function buildStageSeed(lesson: LearningLesson, stage: LearningStage): StudioLessonSeed {
  if (stage === 'implement') {
    return {
      id: `${lesson.id}:implement`,
      title: lesson.implementationChallenge.title,
      categoryName: lesson.categoryName,
      description: lesson.implementationChallenge.prompt,
      language: lesson.language,
      visualizationMode: lesson.visualizationMode,
      sourceCode: lesson.implementationChallenge.starterCode,
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
    language: lesson.language,
    visualizationMode: lesson.visualizationMode,
    sourceCode: lesson.learningContent.walkthroughCode,
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

  const {
    code,
    language,
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
  } = studio;

  useLineHighlight({
    monaco,
    editorRef,
    decorationsRef,
    lineNumber: currentStepInfo?.line_number ?? null,
  });

  useEffect(() => {
    setActiveStage('learn');
  }, [lesson.id]);

  useEffect(() => {
    studio.applyLesson(buildStageSeed(lesson, activeStage));
    // stage 전환과 lesson 변경에만 에디터 시드를 맞춘다.
    // studio 객체 자체는 매 렌더마다 새로 만들어질 수 있어 의존성에서 제외한다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeStage, lesson.id]);

  const stageContent = useMemo(() => {
    return activeStage === 'implement' ? lesson.implementationChallenge : lesson.learningContent;
  }, [activeStage, lesson]);

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
      </div>

      <div className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-ink-muted">
              <span className="rounded-lg border border-surface-border bg-white px-3 py-1.5">
                수업 시각화: {visualizationMode}
              </span>
              {isSelectingLesson && <span>학습을 전환하는 중입니다.</span>}
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
            fileName={language === 'c' ? 'main.c' : 'main.py'}
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

          <VariablesPanel localsSnapshot={currentStepInfo?.locals_snapshot} />

          <Card>
            <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">
              {stageContent.title}
            </h4>
            {'summary' in stageContent ? (
              <p className="mb-3 text-sm leading-relaxed text-ink-secondary">{stageContent.summary}</p>
            ) : (
              <p className="mb-3 text-sm leading-relaxed text-ink-secondary">{stageContent.prompt}</p>
            )}
            <div className="space-y-2">
              {('conceptPoints' in stageContent ? stageContent.conceptPoints : stageContent.checkpoints).map((point) => (
                <div key={point} className="rounded-lg bg-surface-soft px-3 py-2 text-sm text-ink-secondary">
                  {point}
                </div>
              ))}
            </div>
          </Card>

          <StdoutPanel stdoutSnapshot={currentStepInfo?.stdout_snapshot} execution={execution} />
        </div>
      </div>
    </div>
  );
}
