import { useCallback, useRef, useState } from 'react';
import type { PointerEvent as ReactPointerEvent, ReactNode } from 'react';

interface ResizableStudioLayoutProps {
  left: ReactNode;
  right: ReactNode;
}

export function ResizableStudioLayout({ left, right }: ResizableStudioLayoutProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [leftPaneWidth, setLeftPaneWidth] = useState(52);

  const updatePaneWidth = useCallback((clientX: number) => {
    const bounds = containerRef.current?.getBoundingClientRect();
    if (!bounds || bounds.width <= 0) {
      return;
    }
    const nextWidth = ((clientX - bounds.left) / bounds.width) * 100;
    setLeftPaneWidth(Math.min(Math.max(nextWidth, 36), 70));
  }, []);

  const startResize = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>) => {
      event.preventDefault();
      updatePaneWidth(event.clientX);

      const handlePointerMove = (moveEvent: PointerEvent) => {
        updatePaneWidth(moveEvent.clientX);
      };
      const stopResize = () => {
        window.removeEventListener('pointermove', handlePointerMove);
        window.removeEventListener('pointerup', stopResize);
      };

      window.addEventListener('pointermove', handlePointerMove);
      window.addEventListener('pointerup', stopResize, { once: true });
    },
    [updatePaneWidth],
  );

  return (
    <div ref={containerRef} className="grid gap-5 lg:flex lg:items-stretch">
      <div
        className="min-w-0 lg:shrink-0"
        style={{ flexBasis: `calc(${leftPaneWidth}% - 12px)` }}
      >
        {left}
      </div>

      <div
        aria-label="코드와 시각화 영역 크기 조절"
        className="hidden w-3 cursor-col-resize items-center justify-center rounded-full text-ink-faint transition-colors hover:bg-surface-soft hover:text-ink-muted lg:flex"
        role="separator"
        tabIndex={0}
        onPointerDown={startResize}
      >
        <span className="h-14 w-1 rounded-full bg-surface-border" />
      </div>

      <div
        className="min-w-0 lg:flex-1"
        style={{ flexBasis: `calc(${100 - leftPaneWidth}% - 12px)` }}
      >
        {right}
      </div>
    </div>
  );
}
