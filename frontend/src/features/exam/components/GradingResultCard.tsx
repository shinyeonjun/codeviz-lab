import { Card } from '../../../components/ui/Card';
import type { ExamSubmissionResult } from '../../../types/exam';
import { formatValue, getStatusClass, getStatusLabel } from '../examCenterUtils';

interface GradingResultCardProps {
  submission: ExamSubmissionResult | null;
  submissionError: string | null;
}

export function GradingResultCard({ submission, submissionError }: GradingResultCardProps) {
  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-ink-muted">채점 결과</h4>
          {submission ? (
            <p className="mt-2 text-sm text-ink-secondary">
              {submission.passedCount}/{submission.totalCount} 테스트 통과 · 점수 {submission.score}점
            </p>
          ) : (
            <p className="mt-2 text-sm text-ink-secondary">아직 채점 전입니다.</p>
          )}
        </div>
        {submission && (
          <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${getStatusClass(submission.status)}`}>
            {getStatusLabel(submission.status)}
          </span>
        )}
      </div>

      {submissionError && <p className="mt-3 text-sm text-rose-600">{submissionError}</p>}
      {submission?.errorMessage && (
        <p className="mt-3 text-sm text-rose-600">{submission.errorMessage}</p>
      )}

      {submission && submission.results.length > 0 && (
        <div className="mt-4 space-y-2">
          {submission.results.map((result) => (
            <div
              key={result.caseId}
              className={`rounded-2xl border px-4 py-3 ${
                result.passed ? 'border-emerald-100 bg-emerald-50/40' : 'border-rose-100 bg-rose-50/50'
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-ink">{result.caseId}</span>
                <span className={`text-xs font-medium ${result.passed ? 'text-emerald-600' : 'text-rose-600'}`}>
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
  );
}
