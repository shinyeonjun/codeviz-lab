import { useEffect, useMemo, useRef, useState } from 'react';
import { useMonaco } from '@monaco-editor/react';
import { FileCheck2, FileText, Loader2, Play, RotateCcw } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import {
  createExamSession,
  fetchExamCategories,
  getErrorMessage,
  shouldReportError,
  submitExamAnswer,
} from '../../lib/api';
import type { ExamCategory, ExamSession, ExamSubmissionResult } from '../../types/exam';
import { GradingResultCard } from './components/GradingResultCard';
import { WrongReviewCard } from './components/WrongReviewCard';
import {
  buildQuestionSeed,
  createEmptyExamSeed,
  getWrongReviewItems,
  QUESTION_COUNT_OPTIONS,
} from './examCenterUtils';
import { CodeEditorPanel } from '../studio/components/CodeEditorPanel';
import { ExecutionResultPanel } from '../studio/components/ExecutionResultPanel';
import { StdoutPanel } from '../studio/components/StdoutPanel';
import { useLineHighlight } from '../studio/hooks/useLineHighlight';
import { useExecutionStudio } from '../studio/useExecutionStudio';
import { getEditorFileName } from '../studio/utils/languageUtils';
import type { ExecutionLanguage } from '../../types/execution';

const EXAM_LANGUAGE_OPTIONS: { id: ExecutionLanguage; label: string }[] = [
  { id: 'python', label: 'Python' },
  { id: 'c', label: 'C' },
  { id: 'java', label: 'Java' },
];

export function ExamCenter() {
  const monaco = useMonaco();
  const editorRef = useRef<any>(null);
  const decorationsRef = useRef<string[]>([]);
  const studio = useExecutionStudio(useMemo(() => createEmptyExamSeed(), []));

  const [categories, setCategories] = useState<ExamCategory[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [selectedLanguage, setSelectedLanguage] = useState<ExecutionLanguage>('python');
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
        const categoryData = await fetchExamCategories({ language: selectedLanguage });
        setCategories(categoryData);
        setSelectedCategoryId(categoryData[0]?.id ?? null);
      } catch (loadError) {
        if (shouldReportError(loadError)) {
          console.error(loadError);
        }
        setError(getErrorMessage(loadError, '시험 카테고리를 불러오지 못했습니다.'));
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [selectedLanguage]);

  useEffect(() => {
    if (!currentQuestion) {
      return;
    }

    setSubmissionError(null);
    const code = answerMap[currentQuestion.id] ?? currentQuestion.starterCode;
    studio.applyLesson(buildQuestionSeed(currentQuestion, code));
    // 현재 문제 전환 시에만 에디터 seed를 맞춘다.
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
  const effectiveQuestionCount = selectedCategory
    ? Math.min(questionCount, selectedCategory.questionCount)
    : questionCount;

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

  const wrongQuestionCount = session ? gradedQuestionCount - passedQuestionCount : 0;
  const wrongReviewItems = useMemo(
    () => getWrongReviewItems(session, submissionMap),
    [session, submissionMap],
  );

  const startExam = async () => {
    if (!selectedCategoryId) {
      return;
    }

    setIsStarting(true);
    setError(null);

    try {
      const nextSession = await createExamSession({
        categoryId: selectedCategoryId,
        questionCount: effectiveQuestionCount,
        language: selectedLanguage,
      });
      setSession(nextSession);
      setCurrentQuestionIndex(0);
      setAnswerMap({});
      setSubmissionMap({});
      setSubmissionError(null);
      studio.resetStudio();
    } catch (startError) {
      if (shouldReportError(startError)) {
        console.error(startError);
      }
      setError(getErrorMessage(startError, '시험을 시작하지 못했습니다.'));
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
        language: currentQuestion.language,
      });
      setSubmissionMap((prev) => ({
        ...prev,
        [currentQuestion.id]: submission,
      }));
    } catch (submitError) {
      if (shouldReportError(submitError)) {
        console.error(submitError);
      }
      setSubmissionError(getErrorMessage(submitError, '채점 중 오류가 발생했습니다.'));
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
        <p className="mt-1 text-sm text-ink-secondary">
          지금까지 학습한 템플릿 안에서만 랜덤 문제를 뽑아 실력을 점검합니다.
        </p>
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
              {categories.length === 0 ? (
                <Card className="text-sm text-ink-muted">
                  아직 학습한 템플릿이 없습니다. 메인 화면에서 템플릿을 먼저 열어 학습하면 시험 범위에 추가됩니다.
                </Card>
              ) : (
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
              )}

              <Card>
                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">언어</p>
                      <div className="mt-2 flex gap-2">
                        {EXAM_LANGUAGE_OPTIONS.map((language) => {
                          const isActive = language.id === selectedLanguage;
                          return (
                            <button
                              key={language.id}
                              type="button"
                              onClick={() => setSelectedLanguage(language.id)}
                              className={`rounded-xl border px-3 py-1.5 text-sm font-medium transition-colors ${
                                isActive
                                  ? 'border-accent/40 bg-accent-light/40 text-accent'
                                  : 'border-surface-border bg-white text-ink-secondary hover:bg-surface-soft'
                              }`}
                            >
                              {language.label}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                    <div>
                    <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">문항 수</p>
                    <div className="mt-2 flex gap-2">
                      {QUESTION_COUNT_OPTIONS.map((count) => {
                        const isActive = count === questionCount;
                        const exceedsAvailableCount = selectedCategory
                          ? count > selectedCategory.questionCount
                          : false;
                        return (
                          <button
                            key={count}
                            type="button"
                            onClick={() => setQuestionCount(count)}
                            disabled={exceedsAvailableCount}
                            className={`rounded-xl border px-3 py-1.5 text-sm font-medium transition-colors ${
                              isActive
                                ? 'border-accent/40 bg-accent-light/40 text-accent'
                                : exceedsAvailableCount
                                  ? 'border-surface-border bg-surface-soft text-ink-faint'
                                  : 'border-surface-border bg-white text-ink-secondary hover:bg-surface-soft'
                            }`}
                          >
                            {count}문항
                          </button>
                        );
                      })}
                    </div>
                    </div>
                  </div>

                  <Button
                    variant="primary"
                    onClick={() => void startExam()}
                    disabled={!selectedCategory || selectedCategory.questionCount === 0 || isStarting}
                  >
                    {isStarting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        생성 중...
                      </>
                    ) : (
                      <>
                        <FileText size={14} />
                        {effectiveQuestionCount}문항 시험 시작
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
                  채점 완료 {gradedQuestionCount}/{session.questionCount} · 총점 {totalScore}점 · 통과 {passedQuestionCount}문항 · 오답 {wrongQuestionCount}문항
                </p>
                {currentQuestion && (
                  <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{currentQuestion.prompt}</p>
                )}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" className="min-w-[104px]" onClick={resetExam}>
                  <RotateCcw size={14} />
                  다른 시험
                </Button>
                <Button
                  variant="outline"
                  className="min-w-[104px]"
                  onClick={() => setCurrentQuestionIndex((prev) => Math.max(0, prev - 1))}
                  disabled={currentQuestionIndex === 0}
                >
                  이전 문제
                </Button>
                <Button
                  variant="primary"
                  className="min-w-[104px]"
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

          <WrongReviewCard
            items={wrongReviewItems}
            onSelectQuestion={setCurrentQuestionIndex}
          />

          <div className="grid gap-5 lg:grid-cols-[1.05fr_0.95fr]">
            <div className="space-y-3">
              <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
                <div className="rounded-lg border border-surface-border bg-white px-3 py-1.5 text-sm text-ink-secondary">
                  AI가 trace를 분석해 시각화 템플릿을 선택합니다.
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button variant="outline" className="min-w-[96px]" onClick={studio.resetStudio}>
                    <RotateCcw size={14} />
                    초기화
                  </Button>
                  <Button
                    variant="outline"
                    className="min-w-[112px]"
                    onClick={() => void studio.handleRun()}
                    disabled={studio.isRunning || !studio.code.trim()}
                    title="현재 코드를 실행해 trace와 stdout을 확인합니다."
                  >
                    {studio.isRunning ? (
                      '분석 중...'
                    ) : (
                      <>
                        <Play size={14} />
                        실행 추적
                      </>
                    )}
                  </Button>
                  <Button
                    variant="primary"
                    className="min-w-[112px]"
                    onClick={() => void handleSubmit()}
                    disabled={isSubmitting || !studio.code.trim()}
                    title="현재 답안을 채점 서버에 제출합니다."
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        채점 중...
                      </>
                    ) : (
                      <>
                        <FileCheck2 size={14} />
                        채점 제출
                      </>
                    )}
                  </Button>
                </div>
              </div>

              <CodeEditorPanel
                fileName={getEditorFileName(studio.language, 'exam')}
                language={studio.language}
                code={studio.code}
                onChange={handleCodeChange}
                editorRef={editorRef}
              />

              <StdoutPanel
                title="?ㅽ뻾 stdout"
                emptyText="?ㅽ뻾 ?꾩엯?덈떎."
                stdoutSnapshot={studio.currentStepInfo?.stdout_snapshot}
                execution={studio.execution}
              />
            </div>

            <ExecutionResultPanel
              execution={studio.execution}
              requestError={studio.requestError}
              currentStepInfo={studio.currentStepInfo}
              stepIndex={studio.stepIndex}
              totalSteps={studio.totalSteps}
              isPlaying={studio.isPlaying}
              playbackSpeed={studio.playbackSpeed}
              visualizationMode={studio.visualizationMode}
              language={studio.language}
              onTogglePlay={studio.togglePlay}
              onPrev={studio.stepPrev}
              onNext={studio.stepNext}
              onReset={studio.stepReset}
              onJumpToEnd={studio.stepEnd}
              onSeek={studio.seekStep}
              onPlaybackSpeedChange={studio.setPlaybackSpeed}
              showStdout={false}
              stdoutTitle="실행 stdout"
              stdoutEmptyText="실행 전입니다."
            >
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

              <GradingResultCard
                submission={currentSubmission}
                submissionError={submissionError}
              />
            </ExecutionResultPanel>
          </div>
        </div>
      )}
    </div>
  );
}
