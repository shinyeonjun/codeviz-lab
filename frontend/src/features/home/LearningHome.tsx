import { ArrowRight, PlayCircle, Loader2, AlertCircle, BookX } from 'lucide-react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import type { LearningGroup, LearningLesson } from '../../types/learning';

interface LearningHomeProps {
  groups: LearningGroup[];
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

function formatMinutes(minutes: number) {
  return `${minutes}분`;
}

export function LearningHome({
  groups,
  currentLesson,
  onOpenLesson,
  isLoading,
  isSelectingLesson,
  error,
}: LearningHomeProps) {
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
          <p className="font-semibold">학습 데이터를 불러오지 못했습니다</p>
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
      <p className="mt-2 text-sm text-ink-secondary">백엔드 학습 카탈로그를 기준으로 수업을 이어서 봅니다.</p>

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
                <span>{currentLesson.visualizationMode}</span>
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

      {groups.map((group) => (
        <section key={group.category.id} className="mt-10">
          <div className="mb-4 flex items-center gap-2.5">
            <span
              className={`rounded-lg px-2.5 py-1 text-xs font-semibold ${
                CATEGORY_COLORS[group.category.id] || 'bg-gray-100 text-gray-600'
              }`}
            >
              {group.category.name}
            </span>
            <span className="text-xs text-ink-muted">{group.lessons.length}개 수업</span>
          </div>

          <div className="space-y-2">
            {group.lessons.map((lesson) => {
              const isCurrent = lesson.id === currentLesson?.id;
              return (
                <button
                  key={lesson.id}
                  type="button"
                  onClick={() => void onOpenLesson(lesson.id)}
                  className={`group flex w-full items-center gap-4 rounded-xl border px-4 py-3.5 text-left transition-colors ${
                    isCurrent
                      ? 'border-accent/30 bg-accent-light/40'
                      : 'border-surface-border bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-ink">{lesson.title}</span>
                      {isCurrent && (
                        <span className="rounded bg-accent/10 px-1.5 py-0.5 text-[11px] font-medium text-accent">
                          현재
                        </span>
                      )}
                    </div>
                    <p className="mt-0.5 truncate text-xs text-ink-muted">{lesson.description}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3 text-xs text-ink-muted">
                    <span>{formatMinutes(lesson.estimatedMinutes)}</span>
                    <span>{lesson.visualizationMode}</span>
                    <ArrowRight size={14} className={isCurrent ? 'text-accent' : 'text-ink-faint'} />
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
