import type { VisualizationRequestMode } from '../../../types/execution';

interface VisualizationModeOption {
  id: VisualizationRequestMode;
  name: string;
}

interface VisualizationModeSelectProps {
  value: VisualizationRequestMode;
  options: VisualizationModeOption[];
  onChange: (value: VisualizationRequestMode) => void;
}

export function VisualizationModeSelect({
  value,
  options,
  onChange,
}: VisualizationModeSelectProps) {
  return (
    <select
      value={value}
      onChange={(event) => onChange(event.target.value as VisualizationRequestMode)}
      className="rounded-lg border border-surface-border bg-white px-3 py-1.5 text-sm text-ink outline-none focus:border-accent"
    >
      {options.map((mode) => (
        <option key={mode.id} value={mode.id}>
          {mode.name}
        </option>
      ))}
    </select>
  );
}
