import { useCallback, useLayoutEffect, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent, ReactNode } from 'react';
import { Maximize2 } from 'lucide-react';
import { Card } from '../../../components/ui/Card';

interface ResizableVisualizationCardProps {
  children: ReactNode;
}

const MIN_HEIGHT = 260;
const DEFAULT_HEIGHT = 420;
const VIEWPORT_MARGIN = 180;

export function ResizableVisualizationCard({ children }: ResizableVisualizationCardProps) {
  const frameRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(DEFAULT_HEIGHT);
  const [maxHeight, setMaxHeight] = useState(DEFAULT_HEIGHT);

  const measureMaxHeight = useCallback(() => {
    const viewportHeight = Math.max(window.innerHeight - VIEWPORT_MARGIN, MIN_HEIGHT);
    setMaxHeight(viewportHeight);
    setHeight((current) => Math.min(Math.max(current, MIN_HEIGHT), viewportHeight));
  }, []);

  useLayoutEffect(() => {
    measureMaxHeight();
    window.addEventListener('resize', measureMaxHeight);
    return () => window.removeEventListener('resize', measureMaxHeight);
  }, [measureMaxHeight, children]);

  const startResize = useCallback(
    (event: ReactPointerEvent<HTMLButtonElement>) => {
      event.preventDefault();
      event.currentTarget.setPointerCapture(event.pointerId);
      const startY = event.clientY;
      const startHeight = frameRef.current?.getBoundingClientRect().height ?? height;

      const handlePointerMove = (moveEvent: PointerEvent) => {
        const nextHeight = startHeight + moveEvent.clientY - startY;
        setHeight(Math.min(Math.max(nextHeight, MIN_HEIGHT), maxHeight));
      };
      const stopResize = () => {
        window.removeEventListener('pointermove', handlePointerMove);
        window.removeEventListener('pointerup', stopResize);
      };

      window.addEventListener('pointermove', handlePointerMove);
      window.addEventListener('pointerup', stopResize, { once: true });
    },
    [height, maxHeight],
  );

  return (
    <Card className="relative p-3">
      <div
        ref={frameRef}
        className="overflow-hidden pr-1"
        style={{ height, maxHeight, minHeight: MIN_HEIGHT }}
      >
        <div className="h-full min-h-0 p-2">
          {children}
        </div>
      </div>

      <button
        type="button"
        aria-label="시각화 영역 높이 조절"
        className="absolute bottom-2 right-2 flex h-7 w-7 cursor-ns-resize items-center justify-center rounded-lg border border-surface-border bg-white text-ink-faint shadow-sm transition-colors hover:border-accent/30 hover:text-accent"
        style={{ touchAction: 'none' }}
        onPointerDown={startResize}
      >
        <Maximize2 size={14} />
      </button>
    </Card>
  );
}
