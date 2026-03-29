import { useEffect, useMemo, useRef, useState } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { FileText, Loader2, Play, RotateCcw } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { createExamSession, fetchExamCategories, submitExamAnswer } from '../../lib/api';
import type {
  ExamCategory,
  ExamQuestion,
  ExamSession,
  ExamSubmissionResult,
} from '../../types/exam';
import type { StudioLessonSeed } from '../../types/learning';
import { ExecutionVisualization } from '../studio/ExecutionVisualization';
import { CodeEditorPanel } from '../studio/components/CodeEditorPanel';
import { ExecutionErrorPanel } from '../studio/components/ExecutionErrorPanel';
import { PlaybackControls } from '../studio/components/PlaybackControls';
import { StdoutPanel } from '../studio/components/StdoutPanel';
import { VariablesPanel } from '../studio/components/VariablesPanel';
import { useLineHighlight } from '../studio/hooks/useLineHighlight';
import { useExecutionStudio } from '../studio/useExecutionStudio';


function createEmptyExamSeed(): StudioLessonSeed {
  return {
    id: 'exam-empty',
    title: '시험을 준비하는 중',
    categoryName: '시험',
    description: '카테고리를 선택하고 시험을 시작하세요.',
    language: 'python',
    visualizationMode: 'none',
    sourceCode: '',
    difficulty: '시험',
    estimatedMinutes: 0,
    learningPoints: [],
    tags: [],
  };
}

function buildQuestionSeed(question: ExamQuestion, code: string): StudioLessonSeed {
  return {
    id: question.id,
    title: question.title,
    categoryName: question.categoryName,
    description: question.prompt,
    language: 'python',
    visualizationMode: question.visualizationMode,
    sourceCode: code,
    difficulty: question.difficulty,
    estimatedMinutes: question.estimatedMinutes,
    learningPoints: [],
    tags: question.tags,
  };
}

const QUESTION_COUNT_OPTIONS = [2, 3, 5];

function formatValue(value: unknown) {
  if (typeof value === 'string') {
    return value;
  }

  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

export function ExamCenter() {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);
  const studio = useExecutionStudio(useMemo(() => createEmptyExamSeed(), []));

  const [categories, setCategories] = useState<ExamCategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [questionCount, setQuestionCount] = useState(3);
  const [session, setSession] = useState<ExamSession | null>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answerMap, setAnswerMap] = useState<Record<string, string>>({});
  const [submissionMap, setSubmissionMap] = useState<Record<string, ExamSubmissionResult>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submissionError, setSubmissionError] = useState<string | null>(null);

  const currentQuestion = session?.questions[currentQuestionIndex] ?? null;
  const currentSubmission = currentQuestion ? submissionMap[currentQuestion.id] ?? null : null;

  useLineHighlight({
    monaco,
    editorRef,
    decorationsRef,
    lineNumber: studio.currentStepInfo?.line_number ?? null,
  });

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const categoryData = await fetchExamCategories();
        setCategories(categoryData);
        setSelectedCategoryId(categoryData[0]?.id ?? null);
      } catch (loadError) {
        console.error(loadError);
        setError('시험 카테고리를 불러오지 못했습니다.');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  useEffect(() => {
    if (!currentQuestion) {
      return;
    }

    setSubmissionError(null);
    const code = answerMap[currentQuestion.id] ?? currentQuestion.starterCode;
    studio.applyLesson(buildQuestionSeed(currentQuestion, code));
    // 현재 문제 전환에만 에디터를 맞춘다.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentQuestion?.id]);

  useEffect(() => {
    if (!currentQuestion) {
      return;
    }

    setAnswerMap((prev) => {
      if (prev[currentQuestion.id] === studio.code) {
        return prev;
      }
      return {
        ...prev,
        [currentQuestion.id]: studio.code,
      };
    });
  }, [currentQuestion, studio.code]);

  const selectedCategory = useMemo(
    () => categories.find((category) => category.id === selectedCategoryId) ?? null,
    [categories, selectedCategoryId],
  );

  const gradedQuestionCount = useMemo(() => Object.keys(submissionMap).length, [submissionMap]);
  const totalScore = useMemo(() => {
    if (!session) {
      return 0;
    }

    const total = session.questions.reduce(
      (sum, question) => sum + (submissionMap[question.id]?.score ?? 0),
      0,
    );
    return Math.round(total / session.questionCount);
  }, [session, submissionMap]);

  const passedQuestionCount = useMemo(() => {
    if (!session) {
      return 0;
    }

    return session.questions.filter((question) => submissionMap[question.id]?.status === 'passed').length;
  }, [session, submissionMap]);

  const startExam = async () => {
    if (!selectedCategoryId) {
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const nextSession = await createExamSession({
        categoryId: selectedCategoryId,
        questionCount,
      });
      setSession(nextSession);
      setCurrentQuestionIndex(0);
      setAnswerMap({});
      setSubmissionMap({});
      setSubmissionError(null);
      studio.resetStudio();
    } catch (startError) {
      console.error(startError);
      setError(startError instanceof Error ? startError.message : '시험을 시작하지 못했습니다.');
    } finally {
      setIsStarting(false);
    }
  };

  const handleCodeChange = (value: string) => {
    studio.setCode(value);
    if (currentQuestion) {
      setAnswerMap((prev) => ({ ...prev, [currentQuestion.id]: value }));
      setSubmissionMap((prev) => {
        if (!(currentQuestion.id in prev)) {
          return prev;
        }

        const next = { ...prev };
        delete next[currentQuestion.id];
        return next;
      });
      setSubmissionError(null);
    }
  };

  const handleSubmit = async () => {
    if (!currentQuestion || !studio.code.trim()) {
      return;
    }

    setIsSubmitting(true);
    setSubmissionError(null);

    try {
      const submission = await submitExamAnswer({
        lessonId: currentQuestion.lessonId,
        sourceCode: studio.code,
      });
      setSubmissionMap((prev) => ({
        ...prev,
        [currentQuestion.id]: submission,
      }));
    } catch (submitError) {
      console.error(submitError);
      setSubmissionError(
        submitError instanceof Error ? submitError.message : '채점 중 오류가 발생했습니다.',
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const resetExam = () => {
    setSession(null);
    setCurrentQuestionIndex(0);
    setAnswerMap({});
    setSubmissionMap({});
    setSubmissionError(null);
    studio.applyLesson(createEmptyExamSeed());
    studio.resetStudio();
  };

  return (
    <div className="mx-auto w-full max-w-[1440px] px-6 py-6">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-ink">시험</h2>
        <p className="mt-1 text-sm text-ink-secondary">카테고리를 고르고 랜덤 문제로 실력을 점검합니다.</p>
      </div>

      {!session ? (
        <div className="mx-auto max-w-[960px] space-y-4">
          {isLoading ? (
            <Card className="flex items-center gap-3 text-sm text-ink-muted">
              <Loader2 className="h-4 w-4 animate-spin text-accent" />
              시험 카테고리를 불러오는 중입니다.
            </Card>
          ) : (
            <>
              <div className="grid gap-3 md:grid-cols-3">
                {categories.map((category) => {
                  const isActive = category.id === selectedCategoryId;
                  return (
                    <button
                      key={category.id}
                      type="button"
                      onClick={() => setSelectedCategoryId(category.id)}
                      className={`rounded-2xl border bg-white p-5 text-left transition-colors ${
                        isActive
                          ? 'border-accent/40 bg-accent-light/30'
                          : 'border-surface-border hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-sm font-semibold text-ink">{category.name}</span>
                        <span className="rounded-lg bg-surface-soft px-2 py-1 text-xs text-ink-muted">
                          {category.questionCount}문항
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{category.description}</p>
                    </button>
                  );
                })}
              </div>

              <Card>
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">문항 수</p>
                    <div className="mt-2 flex gap-2">
                      {QUESTION_COUNT_OPTIONS.map((count) => {
                        const isActive = count === questionCount;
                        return (
                          <button
                            key={count}
                            type="button"
                            onClick={() => setQuestionCount(count)}
                            className={`rounded-xl border px-3 py-1.5 text-sm font-medium transition-colors ${
                              isActive
                                ? 'border-accent/40 bg-accent-light/40 text-accent'
                                : 'border-surface-border bg-white text-ink-secondary hover:bg-surface-soft'
                            }`}
                          >
                            {count}문항
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    onClick={() => void startExam()}
                    disabled={!selectedCategory || isStarting}
                  >
                    {isStarting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        생성 중...
                      </>
                    ) : (
                      <>
                        <FileText size={14} />
                        시험 시작
                      </>
                    )}
                  </Button>
                </div>
                {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
              </Card>
            </>
          )}
        </div>
      ) : (
        <div className="space-y-5">
          <Card>
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">{session.categoryName}</p>
                <h3 className="mt-1 text-lg font-semibold text-ink">
                  문제 {currentQuestionIndex + 1} / {session.questionCount}
                </h3>
                <p className="mt-2 text-xs text-ink-muted">
                  채점 완료 {gradedQuestionCount}/{session.questionCount} · 총점 {totalScore}점 · 통과 {passedQuestionCount}문항
                </p>
                {currentQuestion && (
                  <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{currentQuestion.prompt}</p>
                )}
              </div>
              <div className="flex gap-1.5">
                <Button variant="outline" onClick={resetExam}>
                  <RotateCcw size={14} />
                  다른 시험
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))}
                  disabled={currentQuestionIndex === 0}
                >
                  이전 문제
                </Button>
                <Button
                  variant="primary"
                  onClick={() =>
                    setCurrentQuestionIndex((prev) => Math.min(session.questions.length - 1, prev + 1))
                  }
                  disabled={currentQuestionIndex >= session.questions.length - 1}
                >
                  다음 문제
                </Button>
              </div>
            </div>
          </Card>

          <div className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="rounded-lg border border-surface-border bg-white px-3 py-1.5 text-sm text-ink-secondary">
                  시험 시각화: {studio.visualizationMode}
                </div>
                <div className="flex gap-1.5">
                  <Button variant="outline" onClick={studio.resetStudio}>
                    <RotateCcw size={14} />
                    초기화
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => void studio.handleRun()}
                    disabled={studio.isRunning || !studio.code.trim()}
                  >
                    {studio.isRunning ? (
                      '분석 중...'
                    ) : (
                      <>
                        <Play size={14} />
                        실행
                      </>
                    )}
                  </Button>
                  <Button
                    variant="primary"
                    onClick={() => void handleSubmit()}
                    disabled={isSubmitting || !studio.code.trim()}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        채점 중...
                      </>
                    ) : (
                      <>
                        <FileText size={14} />
                        채점
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <CodeEditorPanel
                fileName="exam.py"
                language="python"
                code={studio.code}
                onChange={handleCodeChange}
                editorRef={editorRef}
              />
            </div>

            <div className="space-y-3">
              <PlaybackControls
                canControl={Boolean(studio.execution)}
                isPlaying={studio.isPlaying}
                stepIndex={studio.stepIndex}
                totalSteps={studio.totalSteps}
                playbackSpeed={studio.playbackSpeed}
                onTogglePlay={studio.togglePlay}
            onPrev={studio.stepPrev}
            onNext={studio.stepNext}
            onReset={studio.stepReset}
            onJumpToEnd={studio.stepEnd}
            onSeek={studio.seekStep}
            onPlaybackSpeedChange={studio.setPlaybackSpeed}
          />

              <ExecutionErrorPanel requestError={studio.requestError} execution={studio.execution} />

              <Card>
                <ExecutionVisualization viz={studio.execution?.visualization} stepIndex={studio.stepIndex} />
              </Card>

              <VariablesPanel
                localsSnapshot={studio.currentStepInfo?.locals_snapshot}
                globalsSnapshot={studio.currentStepInfo?.globals_snapshot}
                callStack={studio.currentStepInfo?.call_stack}
                metadata={studio.currentStepInfo?.metadata}
              />

              <Card>
                <h4 className="mb-3 text-xs font-semibold uppercase tracking-wider text-ink-muted">문제 태그</h4>
                <div className="flex flex-wrap gap-2">
                  {currentQuestion?.tags.map((tag) => (
                    <span key={tag} className="rounded-full bg-surface-muted px-2.5 py-1 text-xs text-ink-muted">
                      {tag}
                    </span>
                  ))}
                </div>
              </Card>

              <Card>
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">채점 결과</h4>
                    {currentSubmission ? (
                      <p className="mt-2 text-sm text-ink-secondary">
                        {currentSubmission.passedCount}/{currentSubmission.totalCount} 테스트 통과 · 점수 {currentSubmission.score}점
                      </p>
                    ) : (
                      <p className="mt-2 text-sm text-ink-secondary">아직 채점 전입니다.</p>
                    )}
                  </div>
                  {currentSubmission && (
                    <span
                      className={`rounded-full px-2.5 py-1 text-xs font-medium ${
                        currentSubmission.status === 'passed'
                          ? 'bg-emerald-50 text-emerald-600'
                          : currentSubmission.status === 'failed'
                            ? 'bg-amber-50 text-amber-600'
                            : 'bg-rose-50 text-rose-600'
                      }`}
                    >
                      {currentSubmission.status === 'passed'
                        ? '통과'
                        : currentSubmission.status === 'failed'
                          ? '미통과'
                          : currentSubmission.status === 'timeout'
                            ? '시간 초과'
                            : '오류'}
                    </span>
                  )}
                </div>

                {submissionError && (
                  <p className="mt-3 text-sm text-rose-600">{submissionError}</p>
                )}

                {currentSubmission?.errorMessage && (
                  <p className="mt-3 text-sm text-rose-600">{currentSubmission.errorMessage}</p>
                )}

                {currentSubmission && currentSubmission.results.length > 0 && (
                  <div className="mt-4 space-y-2">
                    {currentSubmission.results.map((result) => (
                      <div
                        key={result.caseId}
                        className="rounded-2xl border border-surface-border bg-surface-soft px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-sm font-medium text-ink">{result.caseId}</span>
                          <span
                            className={`text-xs font-medium ${
                              result.passed ? 'text-emerald-600' : 'text-rose-600'
                            }`}
                          >
                            {result.passed ? '통과' : '실패'}
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-ink-muted">{result.inputSummary}</p>
                        <p className="mt-2 text-sm text-ink-secondary">{result.message}</p>
                        {!result.passed && (
                          <div className="mt-3 grid gap-2 md:grid-cols-2">
                            <div className="rounded-xl bg-white px-3 py-2">
                              <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
                                예상값
                              </p>
                              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-xs text-ink-secondary">
                                {formatValue(result.expected)}
                              </pre>
                            </div>
                            <div className="rounded-xl bg-white px-3 py-2">
                              <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
                                실제값
                              </p>
                              <pre className="mt-1 overflow-x-auto whitespace-pre-wrap text-xs text-ink-secondary">
                                {formatValue(result.actual)}
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              <StdoutPanel stdoutSnapshot={studio.currentStepInfo?.stdout_snapshot} execution={studio.execution} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
