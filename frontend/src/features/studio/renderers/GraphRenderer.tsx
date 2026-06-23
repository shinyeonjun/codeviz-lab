import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import type { VisualizationStepState } from '../../../types/execution';
import { asEdgeList, asNodeList, asStringSet } from '../utils/visualizationUtils';
import { DetailChip } from '../components/VisualizationCommon';

type GraphLine = {
  id: string;
  d: string;
  labelX: number;
  labelY: number;
  label: string;
  isActive: boolean;
};

type GraphNodeCenter = {
  id: string;
  centerX: number;
  centerY: number;
};

export function GraphRenderer({ state }: { state: VisualizationStepState }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [lines, setLines] = useState<GraphLine[]>([]);

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
      const containerHeight = containerRect.height;
      const nodeElements = Array.from(container.querySelectorAll('[data-node-id]'));
      const nodeRects = nodeElements.map((element) => {
        const rect = element.getBoundingClientRect();
        return {
          id: String((element as HTMLElement).dataset.nodeId ?? ''),
          centerX: rect.left + rect.width / 2 - containerRect.left,
          centerY: rect.top + rect.height / 2 - containerRect.top,
        };
      });
      const newLines = edges
        .map((edge, index) => {
          const fromEl = container.querySelector(`[data-node-id="${edge.from}"]`);
          const toEl = container.querySelector(`[data-node-id="${edge.to}"]`);
          if (!fromEl || !toEl) return null;

          const fromRect = fromEl.getBoundingClientRect();
          const toRect = toEl.getBoundingClientRect();

          const x1 = fromRect.left + fromRect.width / 2 - containerRect.left;
          const y1 = fromRect.top + fromRect.height / 2 - containerRect.top;
          const x2 = toRect.left + toRect.width / 2 - containerRect.left;
          const y2 = toRect.top + toRect.height / 2 - containerRect.top;
          const arc = calculateGraphArc({
            from: String(edge.from),
            to: String(edge.to),
            x1,
            y1,
            x2,
            y2,
            nodeRects,
            containerHeight,
          });

          return {
            id: `${edge.from}-${edge.to}-${index}`,
            d: arc.d,
            labelX: arc.labelX,
            labelY: arc.labelY,
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

      <div className="relative mt-4 min-h-[220px] rounded-xl border border-surface-border bg-white p-6 pb-16" ref={containerRef}>
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
                <path
                  d={line.d}
                  stroke={line.isActive ? '#10b981' : '#cbd5e1'}
                  strokeWidth={line.isActive ? '2' : '1.5'}
                  markerEnd={line.isActive ? 'url(#arrow-graph-active)' : 'url(#arrow-graph)'}
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
                {line.label && (
                  <text
                    x={line.labelX}
                    y={line.labelY}
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

function calculateGraphArc({
  from,
  to,
  x1,
  y1,
  x2,
  y2,
  nodeRects,
  containerHeight,
}: {
  from: string;
  to: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  nodeRects: GraphNodeCenter[];
  containerHeight: number;
}) {
  const crossedNodes = nodeRects.filter((node) => {
    if (node.id === from || node.id === to) {
      return false;
    }
    const withinX = node.centerX > Math.min(x1, x2) + 8 && node.centerX < Math.max(x1, x2) - 8;
    const nearLine = Math.abs(node.centerY - (y1 + y2) / 2) < 36;
    return withinX && nearLine;
  }).length;

  if (crossedNodes === 0) {
    return {
      d: `M ${x1} ${y1} L ${x2} ${y2}`,
      labelX: (x1 + x2) / 2,
      labelY: (y1 + y2) / 2,
    };
  }

  const labelX = (x1 + x2) / 2;
  const labelY = Math.min(containerHeight - 24, Math.max(y1, y2) + 48 + crossedNodes * 10);
  const shoulderOffset = 18;
  const startShoulderX = x1 < x2 ? x1 + shoulderOffset : x1 - shoulderOffset;
  const endShoulderX = x1 < x2 ? x2 - shoulderOffset : x2 + shoulderOffset;
  return {
    d: `M ${x1} ${y1} L ${startShoulderX} ${labelY} L ${endShoulderX} ${labelY} L ${x2} ${y2}`,
    labelX,
    labelY,
  };
}
