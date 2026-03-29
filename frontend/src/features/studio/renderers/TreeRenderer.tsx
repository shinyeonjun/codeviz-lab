import { useEffect, useRef, useState } from 'react';
import type { VisualizationStepState } from '../../../types/execution';
import { asEdgeList, asNodeList, asStringSet } from '../utils/visualizationUtils';
import { DetailChip } from '../components/VisualizationCommon';

export function TreeRenderer({ state }: { state: VisualizationStepState }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [lines, setLines] = useState<{ id: string; x1: number; y1: number; x2: number; y2: number; label: string }[]>(
    [],
  );

  const nodes = asNodeList(state.payload.nodes);
  const edges = asEdgeList(state.payload.edges);
  const activeNodeIds = asStringSet(state.payload.activeNodeIds);
  const focusNodeIds = asStringSet(state.payload.focusNodeIds);
  const rows = nodes.reduce<Record<number, Array<Record<string, unknown>>>>((acc, node) => {
    const depth = typeof node.depth === 'number' ? node.depth : String(node.id ?? '').split('.').length - 1;
    acc[depth] = [...(acc[depth] ?? []), node];
    return acc;
  }, {});

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const updateLines = () => {
      const containerRect = container.getBoundingClientRect();
      const newLines = edges
        .map((edge) => {
          const fromEl = container.querySelector(`[data-node-id="${edge.from}"]`);
          const toEl = container.querySelector(`[data-node-id="${edge.to}"]`);
          if (!fromEl || !toEl) return null;

          const fromRect = fromEl.getBoundingClientRect();
          const toRect = toEl.getBoundingClientRect();

          return {
            id: `${edge.from}-${edge.to}`,
            x1: fromRect.left + fromRect.width / 2 - containerRect.left,
            y1: fromRect.top + fromRect.height / 2 - containerRect.top,
            x2: toRect.left + toRect.width / 2 - containerRect.left,
            y2: toRect.top + toRect.height / 2 - containerRect.top,
            label: edge.label ? String(edge.label) : '',
          };
        })
        .filter(Boolean) as any;
      setLines(newLines);
    };

    updateLines();
    const timer = setTimeout(updateLines, 50);
    window.addEventListener('resize', updateLines);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', updateLines);
    };
  }, [edges, nodes, state]);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        <DetailChip label="nodes" value={String(nodes.length)} />
        <DetailChip label="edges" value={String(edges.length)} />
        {state.payload.depthCount !== undefined && <DetailChip label="depth" value={String(state.payload.depthCount)} />}
        {Boolean(state.payload.rootNodeId) && <DetailChip label="root" value={String(state.payload.rootNodeId)} />}
      </div>

      <div className="relative mt-8 min-h-[120px] py-4" ref={containerRef}>
        {lines.length > 0 && (
          <svg className="pointer-events-none absolute inset-0 z-0 h-full w-full">
            <defs>
              <marker id="arrow-tree" markerWidth="8" markerHeight="8" refX="30" refY="4" orient="auto">
                <polygon points="0 0, 8 4, 0 8" fill="#cbd5e1" />
              </marker>
            </defs>
            {lines.map((line) => (
              <g key={line.id}>
                <line
                  x1={line.x1}
                  y1={line.y1}
                  x2={line.x2}
                  y2={line.y2}
                  stroke="#cbd5e1"
                  strokeWidth="1.5"
                  markerEnd="url(#arrow-tree)"
                />
                {line.label && (
                  <text
                    x={(line.x1 + line.x2) / 2}
                    y={(line.y1 + line.y2) / 2}
                    dy="-6"
                    fill="#94a3b8"
                    fontSize="11"
                    fontWeight="500"
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

        <div className="relative z-10 space-y-10">
          {Object.entries(rows)
            .sort((a, b) => Number(a[0]) - Number(b[0]))
            .map(([depth, rowNodes]) => (
              <div key={depth} className="flex flex-wrap justify-center gap-10">
                {rowNodes.map((node) => {
                  const nodeId = String(node.id ?? '');
                  const isActive = activeNodeIds.has(nodeId);
                  const isFocused = focusNodeIds.has(nodeId);
                  const classes = isActive
                    ? 'border-ink bg-surface-soft text-ink ring-1 ring-ink shadow-sm'
                    : isFocused
                      ? 'border-emerald-500 bg-emerald-50 text-emerald-800 shadow-sm'
                      : 'border-surface-border bg-white text-ink shadow-sm';

                  return (
                    <div
                      key={nodeId}
                      data-node-id={nodeId}
                      className={`flex h-12 min-w-[3rem] shrink-0 items-center justify-center rounded-full border px-4 transition-all ${classes}`}
                    >
                      <div className={`font-mono text-sm ${isActive ? 'font-bold' : 'font-semibold'}`}>
                        {String(node.label ?? node.value ?? nodeId)}
                      </div>
                    </div>
                  );
                })}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
}
