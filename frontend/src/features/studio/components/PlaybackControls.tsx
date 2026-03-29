import { ChevronLeft, ChevronRight, Pause, Play, SkipBack } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface PlaybackControlsProps {
  canControl: boolean;
  isPlaying: boolean;
  stepIndex: number;
  totalSteps: number;
  onTogglePlay: () => void;
  onPrev: () => void;
  onNext: () => void;
  onReset: () => void;
}

export function PlaybackControls({
  canControl,
  isPlaying,
  stepIndex,
  totalSteps,
  onTogglePlay,
  onPrev,
  onNext,
  onReset,
}: PlaybackControlsProps) {
  return (
    <div className="flex items-center gap-1.5">
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
      <span className="ml-auto font-mono text-xs text-ink-muted">
        {canControl ? stepIndex + 1 : 0} / {totalSteps}
      </span>
    </div>
  );
}
