import { useCallback, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Maximize2, Minimize2 } from 'lucide-react';
import type { VisualizationStepState } from '../../../types/execution';
import { DetailChip } from '../components/VisualizationCommon';

type EdgeRelation = 'flow' | 'decision-yes' | 'decision-no' | 'loop-back' | 'jump' | 'back';

interface FlowchartNode {
  id: string;
  label: string;
  type: 'terminal' | 'branch' | 'loop' | 'output' | 'return' | 'statement';
  lineNumber?: number | null;
  isActive?: boolean;
  isVisited?: boolean;
  visitCount?: number;
  nestingDepth?: number;
}

interface FlowchartEdge {
  id: string;
  from: string;
  to: string;
  label?: string | null;
  relation?: EdgeRelation;
  isActive?: boolean;
  isVisited?: boolean;
  visitCount?: number;
}

interface FlowchartEdgePath {
  id: string;
  d: string;
  label?: string | null;
  labelX: number;
  labelY: number;
  isActive: boolean;
  isVisited: boolean;
  visitCount?: number;
}

type FlowchartRendererProps = {
  state: VisualizationStepState;
  density?: 'normal' | 'compact';
};

export function FlowchartRenderer({ state, density = 'normal' }: FlowchartRendererProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const chartBodyRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [edgePaths, setEdgePaths] = useState<FlowchartEdgePath[]>([]);
  const [showFullLabels, setShowFullLabels] = useState(false);
  const allNodes = useMemo(() => asFlowchartNodes(state.payload.nodes), [state.payload.nodes]);
  const allEdges = useMemo(() => asFlowchartEdges(state.payload.edges), [state.payload.edges]);
  const activeEdgeId = typeof state.payload.activeEdgeId === 'string' ? state.payload.activeEdgeId : null;
  const activeNode = allNodes.find((node) => node.isActive);
  const canToggleLabels = density === 'compact' || allNodes.length >= 7;
  const isCondensed = canToggleLabels && !showFullLabels;
  const nodes = useMemo(
    () => isCondensed ? buildFocusedNodeWindow(allNodes, activeNode?.id ?? null) : allNodes,
    [activeNode?.id, allNodes, isCondensed],
  );
  const visibleNodeIds = useMemo(() => new Set(nodes.map((node) => node.id)), [nodes]);
  const edges = useMemo(
    () => allEdges.filter((edge) => visibleNodeIds.has(edge.from) && visibleNodeIds.has(edge.to)),
    [allEdges, visibleNodeIds],
  );
  const visibleEdges = allEdges.filter((edge) => edge.isVisited || edge.isActive).slice(isCondensed ? -5 : -8);
  const setNodeRef = useCallback((nodeId: string, element: HTMLDivElement | null) => {
    if (element) {
      nodeRefs.current.set(nodeId, element);
      return;
    }
    nodeRefs.current.delete(nodeId);
  }, []);

  useLayoutEffect(() => {
    const container = scrollContainerRef.current;
    const activeNodeElement = activeNode?.id ? nodeRefs.current.get(activeNode.id) : null;
    if (!container || !activeNodeElement) {
      return;
    }

    let animationFrame = window.requestAnimationFrame(() => {
      centerNodeInViewport(container, activeNodeElement);
    });
    const resizeObserver = new ResizeObserver(() => {
      window.cancelAnimationFrame(animationFrame);
      animationFrame = window.requestAnimationFrame(() => {
        centerNodeInViewport(container, activeNodeElement);
      });
    });
    resizeObserver.observe(container);
    resizeObserver.observe(activeNodeElement);

    return () => {
      window.cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
    };
  }, [activeNode?.id, state.step_index, isCondensed]);

  useLayoutEffect(() => {
    const chartBody = chartBodyRef.current;
    if (!chartBody) {
      setEdgePaths([]);
      return;
    }

    const refreshEdgePaths = () => {
      setEdgePaths(measureSideEdgePaths(chartBody, nodeRefs.current, nodes, edges));
    };
    let animationFrame = window.requestAnimationFrame(refreshEdgePaths);
    const resizeObserver = new ResizeObserver(() => {
      window.cancelAnimationFrame(animationFrame);
      animationFrame = window.requestAnimationFrame(refreshEdgePaths);
    });
    resizeObserver.observe(chartBody);
    nodeRefs.current.forEach((element) => resizeObserver.observe(element));

    return () => {
      window.cancelAnimationFrame(animationFrame);
      resizeObserver.disconnect();
    };
  }, [edges, nodes, state.step_index, isCondensed]);

  return (
    <div className={`flex h-full min-h-0 flex-col ${isCondensed ? 'gap-2.5' : 'gap-3'}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-1.5">
          <DetailChip label="노드" value={String(nodes.length)} />
          <DetailChip label="연결" value={String(edges.length)} />
          {activeNode?.lineNumber && <DetailChip label="현재 줄" value={String(activeNode.lineNumber)} />}
        </div>
        {canToggleLabels && (
          <button
            type="button"
            title={showFullLabels ? '줄 번호만 보기' : '플로우차트 전체 문장 보기'}
            aria-label={showFullLabels ? '줄 번호만 보기' : '플로우차트 전체 문장 보기'}
            className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-surface-border bg-white px-2.5 text-xs font-medium text-ink-muted transition-colors hover:border-accent/30 hover:text-accent"
            onClick={() => setShowFullLabels((current) => !current)}
          >
            {showFullLabels ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
            <span>{showFullLabels ? '줄만' : '전체'}</span>
          </button>
        )}
      </div>

      <div className="min-h-0 flex-1 rounded-lg border border-surface-border bg-white p-3">
        <div ref={scrollContainerRef} className="h-full overflow-auto pr-1">
          <div
            ref={chartBodyRef}
            className={`relative mx-auto flex flex-col items-center ${
              isCondensed
                ? 'max-w-xl gap-1.5 px-14 pr-16'
                : 'w-max min-w-full max-w-none gap-2 px-20 pr-24'
            }`}
          >
            <FlowchartEdgeOverlay paths={edgePaths} />
            {nodes.map((node, index) => (
              <div
                key={node.id}
                ref={(element) => setNodeRef(node.id, element)}
                className="relative z-10 flex w-full flex-col items-center gap-1.5"
                style={
                  node.nestingDepth && isCondensed
                    ? { paddingLeft: `${Math.min(node.nestingDepth, 3) * 14}px` }
                    : undefined
                }
              >
                <FlowchartNodeCard node={node} compact={isCondensed} summary={isCondensed} />
                {index < nodes.length - 1 && (
                  <FlowchartVerticalConnector
                    edge={findEdgeBetween(edges, node.id, nodes[index + 1]?.id, activeEdgeId)}
                    compact={isCondensed}
                  />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {visibleEdges.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {visibleEdges.map((edge) => (
            <span
              key={edge.id}
              className={`rounded-md border px-2 py-0.5 text-[11px] ${
                edge.isActive
                  ? 'border-accent/40 bg-accent-light/40 text-accent'
                  : 'border-surface-border bg-white text-ink-muted'
              }`}
            >
              {edge.from} {'->'} {edge.to}
              {edge.label ? ` · ${edge.label}` : ''}
              {edge.visitCount && edge.visitCount > 1 ? ` x${edge.visitCount}` : ''}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function FlowchartVerticalConnector({ edge, compact }: { edge?: FlowchartEdge; compact: boolean }) {
  const isActive = Boolean(edge?.isActive);
  const colorClass = isActive ? 'bg-accent' : edge?.isVisited ? 'bg-emerald-500' : 'bg-surface-border';
  const arrowClass = isActive
    ? 'border-t-accent'
    : edge?.isVisited
      ? 'border-t-emerald-500'
      : 'border-t-surface-border';

  return (
    <div className="relative flex flex-col items-center">
      <div className={`${compact ? 'h-3' : 'h-4'} w-px ${colorClass}`} />
      {edge?.label && (
        <span
          className={`-my-0.5 rounded border bg-white px-1.5 py-0.5 text-[10px] font-bold leading-none shadow-sm ${
            isActive ? 'border-accent/30 text-accent' : 'border-surface-border text-ink-muted'
          }`}
        >
          {edge.label}
        </span>
      )}
      <div className={`h-0 w-0 border-x-[5px] border-x-transparent border-t-[7px] ${arrowClass}`} />
    </div>
  );
}

function FlowchartEdgeOverlay({ paths }: { paths: FlowchartEdgePath[] }) {
  if (paths.length === 0) {
    return null;
  }

  return (
    <svg className="pointer-events-none absolute inset-0 z-0 h-full w-full overflow-visible">
      <defs>
        <marker id="flowchart-arrow" markerHeight="7" markerWidth="7" orient="auto" refX="6" refY="3.5">
          <path d="M0,0 L7,3.5 L0,7 Z" className="fill-current text-surface-border" />
        </marker>
        <marker id="flowchart-arrow-active" markerHeight="7" markerWidth="7" orient="auto" refX="6" refY="3.5">
          <path d="M0,0 L7,3.5 L0,7 Z" className="fill-current text-accent" />
        </marker>
        <marker id="flowchart-arrow-visited" markerHeight="7" markerWidth="7" orient="auto" refX="6" refY="3.5">
          <path d="M0,0 L7,3.5 L0,7 Z" className="fill-current text-emerald-500" />
        </marker>
      </defs>
      {paths.map((path) => {
        const strokeClass = path.isActive
          ? 'stroke-accent'
          : path.isVisited
            ? 'stroke-emerald-500'
            : 'stroke-surface-border';
        const markerId = path.isActive
          ? 'url(#flowchart-arrow-active)'
          : path.isVisited
            ? 'url(#flowchart-arrow-visited)'
            : 'url(#flowchart-arrow)';
        return (
          <g key={path.id}>
            <path
              d={path.d}
              className={`fill-none ${strokeClass}`}
              markerEnd={markerId}
              strokeWidth={path.isActive ? 2.5 : 1.5}
              strokeLinecap="round"
              strokeLinejoin="round"
              vectorEffect="non-scaling-stroke"
            />
            {path.label && (
              <foreignObject x={path.labelX - 18} y={path.labelY - 10} width="36" height="20">
                <div
                  className={`rounded border bg-white px-1 text-center text-[10px] font-bold leading-[18px] shadow-sm ${
                    path.isActive ? 'border-accent/30 text-accent' : 'border-surface-border text-ink-muted'
                  }`}
                >
                  {path.label}
                </div>
              </foreignObject>
            )}
          </g>
        );
      })}
    </svg>
  );
}

function buildFocusedNodeWindow(nodes: FlowchartNode[], activeNodeId: string | null) {
  if (nodes.length <= 8 || !activeNodeId) {
    return nodes;
  }

  const activeIndex = nodes.findIndex((node) => node.id === activeNodeId);
  if (activeIndex < 0) {
    return nodes.slice(0, 8);
  }

  const maxVisibleNodes = 7;
  let start = Math.max(0, activeIndex - 3);
  const end = Math.min(nodes.length, start + maxVisibleNodes);
  start = Math.max(0, end - maxVisibleNodes);

  return nodes.slice(start, end);
}

function centerNodeInViewport(container: HTMLDivElement, node: HTMLDivElement) {
  const containerRect = container.getBoundingClientRect();
  const nodeRect = node.getBoundingClientRect();
  const nodeCenterTop = nodeRect.top - containerRect.top + container.scrollTop + nodeRect.height / 2;
  const nodeCenterLeft = nodeRect.left - containerRect.left + container.scrollLeft + nodeRect.width / 2;
  const targetTop = nodeCenterTop - container.clientHeight / 2;
  const targetLeft = nodeCenterLeft - container.clientWidth / 2;

  container.scrollTo({
    top: clampScrollOffset(targetTop, container.scrollHeight - container.clientHeight),
    left: clampScrollOffset(targetLeft, container.scrollWidth - container.clientWidth),
    behavior: 'smooth',
  });
}

function clampScrollOffset(value: number, max: number) {
  return Math.max(0, Math.min(value, Math.max(0, max)));
}

function measureSideEdgePaths(
  chartBody: HTMLDivElement,
  nodeRefs: Map<string, HTMLDivElement>,
  nodes: FlowchartNode[],
  edges: FlowchartEdge[],
): FlowchartEdgePath[] {
  const chartRect = chartBody.getBoundingClientRect();
  const nodeIndexMap = new Map(nodes.map((node, index) => [node.id, index]));
  const paths: FlowchartEdgePath[] = [];
  const measuredEdges = edges
    .filter((edge) => shouldDrawSideEdge(edge, nodeIndexMap))
    .map((edge) => {
      const sourceElement = nodeRefs.get(edge.from);
      const targetElement = nodeRefs.get(edge.to);
      const sourceIndex = nodeIndexMap.get(edge.from);
      const targetIndex = nodeIndexMap.get(edge.to);
      if (!sourceElement || !targetElement) {
        return null;
      }
      if (sourceIndex === undefined || targetIndex === undefined) {
        return null;
      }

      const sourceRect = getNodeVisualRect(sourceElement);
      const targetRect = getNodeVisualRect(targetElement);
      const isBackEdge = targetRect.top <= sourceRect.top;
      const side: 'left' | 'right' = isBackEdge ? 'left' : 'right';
      const endpointOffset = 6;
      const sourceX = side === 'right'
        ? sourceRect.right - chartRect.left + endpointOffset
        : sourceRect.left - chartRect.left - endpointOffset;
      const targetX = side === 'right'
        ? targetRect.right - chartRect.left + endpointOffset
        : targetRect.left - chartRect.left - endpointOffset;
      const sourceY = sourceRect.top - chartRect.top + sourceRect.height / 2;
      const targetY = targetRect.top - chartRect.top + targetRect.height / 2;

      return {
        edge,
        side,
        sourceX,
        targetX,
        sourceY,
        targetY,
        distance: Math.abs(sourceIndex - targetIndex),
      };
    })
    .filter((edge): edge is NonNullable<typeof edge> => edge !== null);

  const sideTotals = measuredEdges.reduce(
    (totals, item) => ({ ...totals, [item.side]: totals[item.side] + 1 }),
    { left: 0, right: 0 },
  );
  const sideLaneCounts = { left: 0, right: 0 };

  measuredEdges.forEach(({ edge, side, sourceX, targetX, sourceY, targetY, distance }) => {
    const lane = sideLaneCounts[side];
    sideLaneCounts[side] += 1;
    const railX = calculateSideRailX({
      side,
      lane,
      totalLanes: sideTotals[side],
      chartWidth: chartRect.width,
      sourceX,
      targetX,
      distance,
      isLoopBack: edge.relation === 'loop-back',
    });
    const labelY = sourceY + (targetY - sourceY) / 2 + getLaneLabelOffset(lane);

    paths.push({
      id: edge.id,
      d: `M ${sourceX} ${sourceY} L ${railX} ${sourceY} L ${railX} ${targetY} L ${targetX} ${targetY}`,
      label: edge.label ?? null,
      labelX: railX,
      labelY,
      isActive: Boolean(edge.isActive),
      isVisited: Boolean(edge.isVisited),
      visitCount: edge.visitCount,
    });
  });

  return paths;
}

function getNodeVisualRect(element: HTMLDivElement): DOMRect {
  const visualElement = element.firstElementChild;
  if (visualElement instanceof HTMLElement) {
    return visualElement.getBoundingClientRect();
  }
  return element.getBoundingClientRect();
}

function calculateSideRailX({
  side,
  lane,
  totalLanes,
  chartWidth,
  sourceX,
  targetX,
  distance,
  isLoopBack,
}: {
  side: 'left' | 'right';
  lane: number;
  totalLanes: number;
  chartWidth: number;
  sourceX: number;
  targetX: number;
  distance: number;
  isLoopBack: boolean;
}) {
  const edgeX = side === 'left' ? Math.min(sourceX, targetX) : Math.max(sourceX, targetX);
  const gutterStart = side === 'left' ? 12 : edgeX + 38;
  const gutterEnd = side === 'left' ? Math.max(42, edgeX - 38) : Math.max(edgeX + 42, chartWidth - 12);
  const laneCount = Math.max(1, totalLanes);
  const laneStep = laneCount === 1
    ? 0
    : Math.max(18, Math.min(34, (gutterEnd - gutterStart) / (laneCount - 1)));
  const distanceBias = Math.min(10, Math.max(0, distance - 2) * 2);
  const loopBias = isLoopBack ? 4 : 0;

  if (side === 'left') {
    return Math.max(8, gutterStart + lane * laneStep - distanceBias - loopBias);
  }
  return Math.min(chartWidth - 8, gutterStart + lane * laneStep + distanceBias + loopBias);
}

function getLaneLabelOffset(lane: number) {
  return lane % 2 === 0 ? -6 : 8;
}

function shouldDrawSideEdge(edge: FlowchartEdge, nodeIndexMap: Map<string, number>) {
  const sourceIndex = nodeIndexMap.get(edge.from);
  const targetIndex = nodeIndexMap.get(edge.to);
  if (sourceIndex === undefined || targetIndex === undefined) {
    return false;
  }
  if (edge.relation === 'loop-back' || edge.relation === 'back' || edge.relation === 'jump') {
    return true;
  }
  if (edge.relation === 'decision-no' && targetIndex > sourceIndex + 1) {
    return true;
  }
  return targetIndex <= sourceIndex || targetIndex > sourceIndex + 1;
}

function FlowchartNodeCard({
  node,
  compact,
  summary,
}: {
  node: FlowchartNode;
  compact: boolean;
  summary: boolean;
}) {
  const depth = Math.max(0, node.nestingDepth ?? 0);
  const nestedLoop = node.type === 'loop' && depth > 0;
  const denseCard = compact || depth > 0;
  const isDecision = node.type === 'branch' || node.type === 'loop';
  const classes = node.isActive
    ? 'border-accent bg-accent-light/40 text-accent ring-1 ring-accent/30'
    : node.isVisited
      ? 'border-emerald-500 bg-emerald-50 text-emerald-800'
      : 'border-surface-border bg-white text-ink';
  const typeLabel = getTypeLabel(node.type);
  const shapeClass = node.type === 'terminal' ? 'rounded-full' : 'rounded-lg';
  const sizeClass = summary
    ? 'w-36 px-2.5 py-1.5'
    : nestedLoop
      ? 'w-max min-w-52 max-w-none px-3 py-2'
      : denseCard
        ? 'w-max min-w-60 max-w-none px-3.5 py-2.5'
        : 'w-max min-w-64 max-w-none px-4 py-3';
  const labelClass = summary ? 'text-xs' : nestedLoop ? 'text-[11px]' : denseCard ? 'text-xs' : 'text-sm';
  const primaryLabel = summary ? buildCompactNodeLabel(node) : node.label;
  const label = (
    <>
      <div className="flex flex-wrap items-center justify-center gap-1.5 text-[10px] font-semibold uppercase tracking-wide opacity-70">
        {!summary && node.lineNumber ? <span>line {node.lineNumber}</span> : null}
        {!summary ? <span>{typeLabel}</span> : null}
        {!summary && depth > 0 ? <span>depth {depth}</span> : null}
        {node.visitCount && node.visitCount > 1 ? <span>{node.visitCount}회</span> : null}
      </div>
      <div className={`mt-1 whitespace-nowrap font-mono font-semibold leading-snug ${labelClass}`}>
        {primaryLabel}
      </div>
      {summary && node.type !== 'terminal' ? (
        <div className="mt-0.5 text-[10px] font-semibold uppercase tracking-wide opacity-60">{typeLabel}</div>
      ) : null}
    </>
  );

  if (isDecision) {
    const outerClass = node.isActive
      ? 'bg-accent ring-2 ring-accent/20'
      : node.isVisited
        ? 'bg-emerald-500'
        : 'bg-surface-border';
    const innerClass = node.isActive
      ? 'bg-accent-light/40 text-accent'
      : node.isVisited
        ? 'bg-emerald-50 text-emerald-800'
        : 'bg-white text-ink';
    const diamondSize = summary
      ? 'h-16 w-44'
      : nestedLoop
        ? 'h-24 w-max min-w-72 max-w-none px-16'
        : denseCard
          ? 'h-28 w-max min-w-96 max-w-none px-20'
          : 'h-32 w-max min-w-[28rem] max-w-none px-24';

    return (
      <div className={`relative flex shrink-0 items-center justify-center ${diamondSize}`}>
        <div
          className={`absolute inset-0 shadow-sm ${outerClass}`}
          style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
        />
        <div
          className={`absolute inset-[1px] ${innerClass}`}
          style={{ clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)' }}
        />
        <div
          className={`relative z-10 flex flex-col items-center justify-center text-center ${
            summary ? 'max-w-[78%]' : 'max-w-none'
          }`}
        >
          {label}
        </div>
      </div>
    );
  }

  return (
    <div className={`border text-center shadow-sm transition-colors ${classes} ${shapeClass} ${sizeClass}`}>
      {label}
    </div>
  );
}

function buildCompactNodeLabel(node: FlowchartNode) {
  if (node.type === 'terminal') {
    return node.label;
  }
  return node.lineNumber ? `LINE ${node.lineNumber}` : node.label;
}

function asFlowchartNodes(value: unknown): FlowchartNode[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((item) => ({
      id: String(item.id ?? ''),
      label: String(item.label ?? item.id ?? ''),
      type: normalizeNodeType(item.type),
      lineNumber: typeof item.lineNumber === 'number' ? item.lineNumber : null,
      isActive: Boolean(item.isActive),
      isVisited: Boolean(item.isVisited),
      visitCount: typeof item.visitCount === 'number' ? item.visitCount : 0,
      nestingDepth: typeof item.nestingDepth === 'number' ? item.nestingDepth : 0,
    }))
    .filter((node) => node.id && node.label);
}

function asFlowchartEdges(value: unknown): FlowchartEdge[] {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
    .map((item) => ({
      id: String(item.id ?? `${String(item.from ?? '')}->${String(item.to ?? '')}`),
      from: String(item.from ?? ''),
      to: String(item.to ?? ''),
      label: typeof item.label === 'string' ? item.label : null,
      relation: normalizeEdgeRelation(item.relation),
      isActive: Boolean(item.isActive),
      isVisited: Boolean(item.isVisited),
      visitCount: typeof item.visitCount === 'number' ? item.visitCount : 0,
    }))
    .filter((edge) => edge.id && edge.from && edge.to);
}

function normalizeEdgeRelation(value: unknown): EdgeRelation {
  if (
    value === 'flow'
    || value === 'decision-yes'
    || value === 'decision-no'
    || value === 'loop-back'
    || value === 'jump'
    || value === 'back'
  ) {
    return value;
  }
  return 'flow';
}

function normalizeNodeType(value: unknown): FlowchartNode['type'] {
  if (
    value === 'terminal'
    || value === 'branch'
    || value === 'loop'
    || value === 'output'
    || value === 'return'
    || value === 'statement'
  ) {
    return value;
  }
  return 'statement';
}

function getTypeLabel(type: FlowchartNode['type']) {
  const labels: Record<FlowchartNode['type'], string> = {
    terminal: 'start/end',
    branch: 'condition',
    loop: 'loop',
    output: 'output',
    return: 'return',
    statement: 'step',
  };
  return labels[type];
}

function findEdgeBetween(
  edges: FlowchartEdge[],
  from: string,
  to: string | undefined,
  activeEdgeId: string | null,
): FlowchartEdge | undefined {
  if (!to) {
    return undefined;
  }
  return edges.find((edge) => edge.from === from && edge.to === to && (edge.isActive || edge.id === activeEdgeId))
    ?? edges.find((edge) => edge.from === from && edge.to === to);
}
