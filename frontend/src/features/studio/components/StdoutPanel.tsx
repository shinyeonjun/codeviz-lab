import { Terminal } from 'lucide-react';
import type { ExecutionResult } from '../../../types/execution';

interface StdoutPanelProps {
  stdoutSnapshot?: string;
  execution: ExecutionResult | null;
}

export function StdoutPanel({ stdoutSnapshot, execution }: StdoutPanelProps) {
  return (
    <div className="overflow-hidden rounded-xl border border-sidebar-light bg-sidebar">
      <div className="flex items-center gap-1.5 border-b border-white/5 px-3 py-2">
        <Terminal size={12} className="text-gray-500" />
        <span className="text-[11px] font-medium text-gray-500">stdout</span>
      </div>
      <div className="min-h-[120px] whitespace-pre-wrap p-3 font-mono text-[13px] leading-relaxed text-green-400/90">
        {stdoutSnapshot || execution?.stdout || 'Ready.'}
      </div>
    </div>
  );
}
