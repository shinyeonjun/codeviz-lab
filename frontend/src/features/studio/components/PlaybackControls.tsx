import { ChevronLeft, ChevronRight, Pause, Play, SkipBack, SkipForward } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

const SPEED_OPTIONS = [
  { value: 1, label: '1x' },
  { value: 2, label: '2x' },
  { value: 4, label: '4x' },
  { value: 8, label: '8x' },
];

interface PlaybackControlsProps {
  canControl: boolean;
  isPlaying: boolean;
  stepIndex: number;
  totalSteps: number;
  playbackSpeed: number;
  onTogglePlay: () => void;
  onPrev: () => void;
  onNext: () => void;
  onReset: () => void;
  onJumpToEnd: () => void;
  onSeek: (value: number) => void;
  onPlaybackSpeedChange: (value: number) => void;
}

export function PlaybackControls({
  canControl,
  isPlaying,
  stepIndex,
  totalSteps,
  playbackSpeed,
  onTogglePlay,
  onPrev,
  onNext,
  onReset,
  onJumpToEnd,
  onSeek,
  onPlaybackSpeedChange,
}: PlaybackControlsProps) {
  const currentValue = canControl && totalSteps > 0 ? stepIndex : 0;

  return (
    <div className="rounded-2xl border border-surface-border bg-white px-4 py-3">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-1.5">
          <Button variant={isPlaying ? 'outline' : 'primary'} onClick={onTogglePlay} disabled={!canControl}>
            {isPlaying ? (
              <>
                <Pause size={14} />
                정지
              </>
            ) : (
              <>
                <Play size={14} />
                재생
              </>
            )}
          </Button>
          <Button variant="outline" onClick={onPrev} disabled={!canControl || stepIndex <= 0}>
            <ChevronLeft size={14} />
          </Button>
          <Button variant="outline" onClick={onNext} disabled={!canControl || stepIndex >= totalSteps - 1}>
            <ChevronRight size={14} />
          </Button>
          <Button variant="outline" onClick={onReset} disabled={!canControl || stepIndex <= 0}>
            <SkipBack size={14} />
          </Button>
          <Button
            variant="outline"
            onClick={onJumpToEnd}
            disabled={!canControl || totalSteps === 0 || stepIndex >= totalSteps - 1}
          >
            <SkipForward size={14} />
          </Button>
          <div className="inline-flex items-center gap-1 rounded-xl bg-surface-soft px-2.5 py-1.5 text-xs text-ink-muted">
            <span>단계 제한</span>
            <span className="font-mono text-base leading-none text-accent">∞</span>
          </div>
          <div className="ml-auto flex items-center gap-1 rounded-xl bg-surface-soft p-1">
            {SPEED_OPTIONS.map((option) => {
              const isActive = playbackSpeed === option.value;
              return (
                <button
                  key={option.label}
                  type="button"
                  onClick={() => onPlaybackSpeedChange(option.value)}
                  disabled={!canControl}
                  className={`rounded-lg px-2.5 py-1 text-xs font-medium transition-colors disabled:opacity-50 ${
                    isActive ? 'bg-white text-accent shadow-sm' : 'text-ink-muted hover:text-ink'
                  }`}
                >
                  {option.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="min-w-10 text-right font-mono text-xs text-ink-muted">
            {canControl ? stepIndex + 1 : 0}
          </span>
          <input
            type="range"
            min={0}
            max={Math.max(totalSteps - 1, 0)}
            step={1}
            value={currentValue}
            disabled={!canControl || totalSteps <= 1}
            onChange={(event) => onSeek(Number(event.target.value))}
            className="h-1.5 w-full cursor-pointer appearance-none rounded-full bg-surface-muted accent-accent disabled:cursor-not-allowed disabled:opacity-50"
          />
          <span className="min-w-10 font-mono text-xs text-ink-muted">{totalSteps}</span>
        </div>
      </div>
    </div>
  );
}
