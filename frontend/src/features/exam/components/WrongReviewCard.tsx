import { ChevronRight } from 'lucide-react';
import { Card } from '../../../components/ui/Card';
import { getStatusLabel, type WrongReviewItem } from '../examCenterUtils';

interface WrongReviewCardProps {
  items: WrongReviewItem[];
  onSelectQuestion: (index: number) => void;
}

export function WrongReviewCard({ items, onSelectQuestion }: WrongReviewCardProps) {
  if (items.length === 0) {
    return null;
  }

  return (
    <Card>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">오답 노트</h4>
          <p className="mt-1 text-sm text-ink-secondary">
            실패한 문제를 다시 열어 예상값과 실제값을 비교하세요.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {items.map(({ question, index, submission }) => {
            const firstFailedCase = submission.results.find((result) => !result.passed);
            return (
              <button
                key={question.id}
                type="button"
                onClick={() => onSelectQuestion(index)}
                className="rounded-xl border border-rose-100 bg-rose-50/50 px-3 py-2 text-left transition-colors hover:border-rose-200 hover:bg-rose-50"
              >
                <span className="block text-xs font-semibold text-rose-700">
                  {index + 1}. {question.title}
                </span>
                <span className="mt-0.5 block text-[11px] text-rose-500">
                  {submission.score}점 · {firstFailedCase?.caseId ?? getStatusLabel(submission.status)}
                </span>
                <span className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-rose-600">
                  문제로 이동
                  <ChevronRight size={12} />
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </Card>
  );
}
