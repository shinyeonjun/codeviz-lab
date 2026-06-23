import { useEffect, useMemo, useState } from 'react';
import { ArrowRight, PlayCircle, Loader2, AlertCircle, BookX, CheckCircle2 } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { LearningGroup, LearningInsight, LearningLesson, LearningRecommendation } from '../../types/learning';

interface LearningHomeProps {
  groups: LearningGroup[];
  insights: LearningInsight | null;
  currentLesson: LearningLesson | null;
  onOpenLesson: (lessonId: string) => void;
  isLoading: boolean;
  isSelectingLesson: boolean;
  error: string | null;
}

const CATEGORY_COLORS: Record<string, string> = {
  basics: 'bg-blue-100 text-blue-700',
  'data-structures': 'bg-amber-100 text-amber-700',
  algorithms: 'bg-violet-100 text-violet-700',
};
const DEFAULT_VISIBLE_LESSON_COUNT = 6;

function formatMinutes(minutes: number) {
  return `${minutes}분`;
}

function formatStudiedAt(value: string) {
  return new Intl.DateTimeFormat('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function RecommendationButton({
  recommendation,
  onOpenLesson,
}: {
  recommendation: LearningRecommendation;
  onOpenLesson: (lessonId: string) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => void onOpenLesson(recommendation.lesson.id)}
      className="flex w-full items-center justify-between gap-3 rounded-xl border border-surface-border bg-white px-3 py-2.5 text-left transition-colors hover:border-accent/30 hover:bg-accent-light/20"
    >
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-ink">{recommendation.lesson.title}</p>
        <p className="mt-0.5 truncate text-xs text-ink-muted">{recommendation.reason}</p>
      </div>
      <ArrowRight size={14} className="shrink-0 text-ink-faint" />
    </button>
  );
}

export function LearningHome({
  groups,
  insights,
  currentLesson,
  onOpenLesson,
  isLoading,
  isSelectingLesson,
  error,
}: LearningHomeProps) {
  const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [isLessonListExpanded, setIsLessonListExpanded] = useState(false);

  useEffect(() => {
    if (selectedCategoryId && groups.some((group) => group.category.id === selectedCategoryId)) {
      return;
    }

    setSelectedCategoryId(currentLesson?.categoryId ?? groups[0]?.category.id ?? null);
  }, [currentLesson?.categoryId, groups, selectedCategoryId]);

  const selectedGroup = useMemo(
    () => groups.find((group) => group.category.id === selectedCategoryId) ?? groups[0] ?? null,
    [groups, selectedCategoryId],
  );

  const visibleLessons = useMemo(() => {
    if (!selectedGroup) {
      return [];
    }
    return isLessonListExpanded
      ? selectedGroup.lessons
      : selectedGroup.lessons.slice(0, DEFAULT_VISIBLE_LESSON_COUNT);
  }, [isLessonListExpanded, selectedGroup]);

  const hiddenLessonCount = selectedGroup
    ? Math.max(0, selectedGroup.lessons.length - visibleLessons.length)
    : 0;

  if (isLoading && groups.length === 0) {
    return (
      <div className="mx-auto flex h-full min-h-[50vh] max-w-[960px] flex-col items-center justify-center gap-4 px-8 py-12 text-ink-muted">
        <Loader2 className="h-8 w-8 animate-spin text-accent" />
        <p className="text-sm font-medium">학습 목록을 불러오는 중입니다...</p>
      </div>
    );
  }

  if (error && groups.length === 0) {
    return (
      <div className="mx-auto flex h-full min-h-[50vh] max-w-[960px] flex-col items-center justify-center gap-4 px-8 py-12 text-red-600">
        <AlertCircle className="h-10 w-10 text-red-400" />
        <div className="text-center">
          <p className="font-semibold">학습 데이터를 불러오지 못했습니다.</p>
          <p className="mt-1 text-sm text-red-500/80">{error}</p>
        </div>
      </div>
    );
  }

  if (!isLoading && groups.length === 0) {
    return (
      <div className="mx-auto flex h-full min-h-[50vh] max-w-[960px] flex-col items-center justify-center gap-4 px-8 py-12 text-ink-muted">
        <BookX className="h-10 w-10 text-ink-faint" />
        <p className="text-sm font-medium">현재 등록된 학습 콘텐츠가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[960px] px-8 py-12">
      <h2 className="text-3xl font-bold tracking-tight text-ink">오늘 이어갈 수업</h2>
      <p className="mt-2 text-sm text-ink-secondary">
        기초 개념, 자료구조, 알고리즘 순서로 정리된 실습 템플릿을 골라 실행해보세요.
      </p>

      {currentLesson && (
        <Card className="mt-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
            <div className="flex-1">
              <span className="text-xs font-medium text-ink-muted">{currentLesson.categoryName}</span>
              <h3 className="mt-2 text-xl font-bold text-ink">{currentLesson.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-secondary">{currentLesson.description}</p>
              <div className="mt-4 flex items-center gap-4 text-xs text-ink-muted">
                <span>{formatMinutes(currentLesson.estimatedMinutes)}</span>
                <span>{currentLesson.difficulty}</span>
                {currentLesson.progress && (
                  <span className="inline-flex items-center gap-1 text-blue-600">
                    <CheckCircle2 size={13} />
                    {formatStudiedAt(currentLesson.progress.lastStudiedAt)} 학습
                  </span>
                )}
              </div>
            </div>
            <Button
              variant="primary"
              className="whitespace-nowrap"
              onClick={() => void onOpenLesson(currentLesson.id)}
              disabled={isSelectingLesson}
            >
              <PlayCircle size={16} />
              수업 열기
            </Button>
          </div>
        </Card>
      )}

      {insights && (
        <section className="mt-6 grid gap-3 lg:grid-cols-[1fr_1.4fr]">
          <Card>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase text-ink-muted">학습 현황</p>
                <p className="mt-2 text-2xl font-bold text-ink">
                  {formatPercent(insights.completionRate)}
                </p>
                <p className="mt-1 text-xs text-ink-muted">
                  {insights.studiedLessons} / {insights.totalLessons}개 학습
                </p>
              </div>
              {insights.dailyRecommendation && (
                <Button
                  variant="outline"
                  className="min-h-8 px-3 py-1.5 text-xs"
                  onClick={() => void onOpenLesson(insights.dailyRecommendation!.lesson.id)}
                >
                  오늘의 추천
                </Button>
              )}
            </div>
            <div className="mt-4 space-y-2">
              {insights.categoryProgress.map((item) => (
                <div key={item.categoryId}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="font-medium text-ink-secondary">{item.categoryName}</span>
                    <span className="text-ink-muted">
                      {item.studiedCount}/{item.totalCount}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-muted">
                    <div
                      className="h-2 rounded-full bg-accent"
                      style={{ width: `${Math.min(100, Math.round(item.completionRate * 100))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>

          <Card>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-xs font-semibold uppercase text-ink-muted">다음 학습</p>
                <div className="mt-3 space-y-2">
                  {insights.nextRecommendations.length > 0 ? (
                    insights.nextRecommendations.slice(0, 2).map((recommendation) => (
                      <RecommendationButton
                        key={recommendation.lesson.id}
                        recommendation={recommendation}
                        onOpenLesson={onOpenLesson}
                      />
                    ))
                  ) : (
                    <p className="rounded-xl bg-surface-soft px-3 py-2 text-xs text-ink-muted">
                      모든 제공 템플릿을 학습했습니다.
                    </p>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold uppercase text-ink-muted">복습 추천</p>
                <div className="mt-3 space-y-2">
                  {insights.reviewRecommendations.length > 0 ? (
                    insights.reviewRecommendations.slice(0, 2).map((recommendation) => (
                      <RecommendationButton
                        key={recommendation.lesson.id}
                        recommendation={recommendation}
                        onOpenLesson={onOpenLesson}
                      />
                    ))
                  ) : (
                    <p className="rounded-xl bg-surface-soft px-3 py-2 text-xs text-ink-muted">
                      첫 수업을 열면 복습 후보가 생깁니다.
                    </p>
                  )}
                </div>
              </div>
            </div>
            {insights.weakCategories.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {insights.weakCategories.map((category) => (
                  <span
                    key={category.categoryId}
                    className="rounded-full bg-surface-soft px-2.5 py-1 text-xs text-ink-muted"
                  >
                    {category.categoryName} {formatPercent(category.completionRate)}
                  </span>
                ))}
              </div>
            )}
          </Card>
        </section>
      )}

      <section className="mt-10">
        <div className="flex flex-wrap gap-2">
          {groups.map((group) => {
            const isActive = group.category.id === selectedGroup?.category.id;
            return (
              <button
                key={group.category.id}
                type="button"
                onClick={() => {
                  setSelectedCategoryId(group.category.id);
                  setIsLessonListExpanded(false);
                }}
                className={`rounded-xl px-3.5 py-2 text-sm font-semibold transition-colors ${
                  isActive
                    ? CATEGORY_COLORS[group.category.id] || 'bg-gray-100 text-gray-700'
                    : 'text-ink-muted hover:bg-surface-soft hover:text-ink'
                }`}
              >
                {group.category.name}
                <span className="ml-2 text-xs font-medium opacity-70">{group.lessons.length}개</span>
              </button>
            );
          })}
        </div>

        {selectedGroup && (
          <div className="mt-5">
            <div className="mb-4 flex flex-col gap-1">
              <h3 className="text-lg font-bold text-ink">{selectedGroup.category.name}</h3>
              <p className="text-sm text-ink-secondary">{selectedGroup.category.description}</p>
            </div>

            <div className="space-y-2">
              {visibleLessons.map((lesson) => {
                const isCurrent = lesson.id === currentLesson?.id;
                const isStudied = Boolean(lesson.progress);
                return (
                  <button
                    key={lesson.id}
                    type="button"
                    onClick={() => void onOpenLesson(lesson.id)}
                    className={`group flex w-full items-center gap-4 rounded-xl border px-4 py-3.5 text-left transition-colors ${
                      isCurrent
                        ? 'border-accent/30 bg-accent-light/40'
                        : isStudied
                          ? 'border-blue-200 bg-blue-50/70 hover:border-blue-300 hover:bg-blue-50'
                        : 'border-surface-border bg-white hover:border-gray-300'
                    }`}
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-ink">{lesson.title}</span>
                        {isStudied && (
                          <span className="inline-flex items-center gap-1 rounded bg-blue-100 px-1.5 py-0.5 text-[11px] font-medium text-blue-700">
                            <CheckCircle2 size={11} />
                            학습함
                          </span>
                        )}
                        {isCurrent && (
                          <span className="rounded bg-accent/10 px-1.5 py-0.5 text-[11px] font-medium text-accent">
                            현재
                          </span>
                        )}
                      </div>
                      <p className="mt-0.5 truncate text-xs text-ink-muted">{lesson.description}</p>
                    </div>
                    <div className="flex shrink-0 flex-wrap items-center justify-end gap-3 text-xs text-ink-muted">
                      {lesson.progress && (
                        <span className="text-blue-600">
                          {formatStudiedAt(lesson.progress.lastStudiedAt)}
                        </span>
                      )}
                      <span>{formatMinutes(lesson.estimatedMinutes)}</span>
                      <span>{lesson.difficulty}</span>
                      <ArrowRight size={14} className={isCurrent ? 'text-accent' : 'text-ink-faint'} />
                    </div>
                  </button>
                );
              })}
            </div>

            {hiddenLessonCount > 0 || isLessonListExpanded ? (
              <div className="mt-4 flex justify-center">
                <button
                  type="button"
                  onClick={() => setIsLessonListExpanded((prev) => !prev)}
                  className="rounded-xl border border-surface-border bg-white px-4 py-2 text-sm font-medium text-ink-secondary transition-colors hover:bg-surface-soft"
                >
                  {isLessonListExpanded ? '접기' : `나머지 ${hiddenLessonCount}개 더 보기`}
                </button>
              </div>
            ) : null}
          </div>
        )}
      </section>
    </div>
  );
}
