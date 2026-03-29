import type { ExecutionResult } from '../../../types/execution';

interface ExecutionErrorPanelProps {
  requestError: string | null;
  execution: ExecutionResult | null;
}

export function ExecutionErrorPanel({ requestError, execution }: ExecutionErrorPanelProps) {
  if (requestError) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
        {requestError}
      </div>
    );
  }

  if (execution && (execution.status === 'failed' || execution.status === 'timeout')) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-3">
        <div className="text-sm font-medium text-red-800">{execution.status.toUpperCase()}</div>
        <div className="mt-1 font-mono text-xs text-red-700">
          {execution.error_message || execution.stderr}
        </div>
      </div>
    );
  }

  return null;
}
