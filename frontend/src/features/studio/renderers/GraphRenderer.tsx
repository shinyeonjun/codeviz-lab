import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import type { VisualizationStepState } from '../../../types/execution';
import { asEdgeList, asNodeList, asStringSet } from '../utils/visualizationUtils';
import { DetailChip } from '../components/VisualizationCommon';

export function GraphRenderer({ state }: { state: VisualizationStepState }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [lines, setLines] = useState<{ id: string; x1: number; y1: number; x2: number; y2: number; label: string; isActive: boolean }[]>([]);

  const nodes = asNodeList(state.payload.nodes);
  const edges = asEdgeList(state.payload.edges);
  const activeNodeIds = asStringSet(state.payload.activeNodeIds);
  const focusNodeIds = asStringSet(state.payload.focusNodeIds);
  const activeEdgeIds = asStringSet(state.payload.activeEdgeIds);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const updateLines = () => {
      const containerRect = container.getBoundingClientRect();
      const newLines = edges
        .map((edge, index) => {
          const fromEl = container.querySelector(`[data-node-id="${edge.from}"]`);
          const toEl = container.querySelector(`[data-node-id="${edge.to}"]`);
          if (!fromEl || !toEl) return null;

          const fromRect = fromEl.getBoundingClientRect();
          const toRect = toEl.getBoundingClientRect();

          return {
            id: `${edge.from}-${edge.to}-${index}`,
            x1: fromRect.left + fromRect.width / 2 - containerRect.left,
            y1: fromRect.top + fromRect.height / 2 - containerRect.top,
            x2: toRect.left + toRect.width / 2 - containerRect.left,
            y2: toRect.top + toRect.height / 2 - containerRect.top,
            label: edge.label ? String(edge.label) : '',
            isActive: activeEdgeIds.has(`${edge.from}->${edge.to}`),
          };
        })
        .filter(Boolean) as any;
      setLines(newLines);
    };

    let animationFrameId: number;
    const startTime = performance.now();

    const animateLines = (time: number) => {
      updateLines();
      if (time - startTime < 800) {
        animationFrameId = requestAnimationFrame(animateLines);
      }
    };

    animationFrameId = requestAnimationFrame(animateLines);
    window.addEventListener('resize', updateLines);
    
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener('resize', updateLines);
    };
  }, [edges, nodes, state, activeEdgeIds]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="nodes" value={String(nodes.length)} />
        <DetailChip label="edges" value={String(edges.length)} />
        {activeNodeIds.size > 0 && <DetailChip label="new nodes" value={Array.from(activeNodeIds).join(', ')} />}
      </div>

      <div className="relative mt-4 min-h-[160px] rounded-xl border border-surface-border bg-white p-6" ref={containerRef}>
        {lines.length > 0 && (
          <svg className="pointer-events-none absolute inset-0 z-0 h-full w-full">
            <defs>
              <marker id="arrow-graph" markerWidth="8" markerHeight="8" refX="30" refY="4" orient="auto">
                <polygon points="0 0, 8 4, 0 8" fill="#cbd5e1" />
              </marker>
              <marker id="arrow-graph-active" markerWidth="8" markerHeight="8" refX="30" refY="4" orient="auto">
                <polygon points="0 0, 8 4, 0 8" fill="#10b981" />
              </marker>
            </defs>
            {lines.map((line) => (
              <g key={line.id}>
                <line
                  x1={line.x1}
                  y1={line.y1}
                  x2={line.x2}
                  y2={line.y2}
                  stroke={line.isActive ? '#10b981' : '#cbd5e1'}
                  strokeWidth={line.isActive ? '2' : '1.5'}
                  markerEnd={line.isActive ? 'url(#arrow-graph-active)' : 'url(#arrow-graph)'}
                />
                {line.label && (
                  <text
                    x={(line.x1 + line.x2) / 2}
                    y={(line.y1 + line.y2) / 2}
                    dy="-6"
                    fill={line.isActive ? '#059669' : '#94a3b8'}
                    fontSize="11"
                    fontWeight={line.isActive ? 'bold' : '500'}
                    textAnchor="middle"
                    stroke="#ffffff"
                    strokeWidth="4"
                    paintOrder="stroke"
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  >
                    {line.label}
                  </text>
                )}
              </g>
            ))}
          </svg>
        )}

        <div className="relative z-10 flex flex-wrap justify-center gap-8">
          {nodes.map((node) => {
            const nodeId = String(node.id);
            const isActive = activeNodeIds.has(nodeId);
            const isFocused = focusNodeIds.has(nodeId);
            const classes = isActive
              ? 'bg-surface-soft border-ink text-ink shadow-sm ring-1 ring-ink'
              : isFocused
                ? 'bg-emerald-50 border-emerald-500 text-emerald-800 shadow-sm'
                : 'bg-white border-surface-border text-ink shadow-sm';

            return (
              <motion.div
                key={nodeId}
                layout
                transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                data-node-id={nodeId}
                className={`flex h-12 min-w-[3rem] shrink-0 items-center justify-center rounded-full border px-4 transition-colors ${classes}`}
              >
                <div className={`font-mono text-sm ${isActive ? 'font-bold' : 'font-semibold'}`}>
                  {String(node.label ?? node.id)}
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
