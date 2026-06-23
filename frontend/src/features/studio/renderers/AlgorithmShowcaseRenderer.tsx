import { motion } from 'framer-motion';
import type { VisualizationStepState } from '../../../types/execution';

type ShowcasePayload = Record<string, unknown>;

const BLUE = '#2563EB';
const BLUE_DARK = '#1D4ED8';
const BLUE_LIGHT = '#DBEAFE';
const GREEN = '#9bbb59';
const GREEN_DARK = '#77933c';
const RED = '#EF4444';
const EDGE = '#CBD5E1';
const EDGE_ACTIVE = '#2563EB';
const INK = '#111827';
const MUTED = '#94A3B8';

export function AlgorithmShowcaseRenderer({ state }: { state: VisualizationStepState }) {
  const payload = state.payload;
  const showcaseType = String(payload.showcaseType ?? '');

  if (showcaseType === 'dijkstra') {
    return <DijkstraShowcase payload={payload} />;
  }
  if (showcaseType === 'merge-sort') {
    return <MergeSortShowcase payload={payload} />;
  }
  if (showcaseType === 'radix-sort') {
    return <RadixSortShowcase payload={payload} />;
  }

  return (
    <div className="flex h-48 items-center justify-center rounded-lg border border-surface-border bg-white text-sm text-ink-muted">
      표시할 알고리즘 시각화 데이터가 없습니다.
    </div>
  );
}

function DijkstraShowcase({ payload }: { payload: ShowcasePayload }) {
  const nodes = asRecordArray(payload.nodes);
  const edges = asRecordArray(payload.edges);
  const distances = asStringArray(payload.distances);
  const currentNodeId = String(payload.currentNodeId ?? '');
  const settledNodeIds = new Set(asStringArray(payload.settledNodeIds));
  const activeEdgeIds = new Set(asStringArray(payload.activeEdgeIds));
  const updatedDistanceIndices = new Set(asNumberArray(payload.updatedDistanceIndices));
  const title = String(payload.title ?? '다익스트라 최단 경로');
  const description = String(payload.description ?? '');
  const nodeMap = new Map(nodes.map((node) => [String(node.id), node]));

  return (
    <div className="flex h-full min-h-[360px] flex-col justify-center gap-3 overflow-auto rounded-lg bg-white p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="text-sm font-semibold text-ink">{title}</div>
          <div className="mt-1 text-xs text-ink-secondary">{description}</div>
        </div>
        <div className="rounded-full bg-accent-light px-3 py-1 text-xs font-semibold text-accent">
          현재 노드 {currentNodeId || '-'}
        </div>
      </div>

      <svg viewBox="0 0 300 320" className="min-h-[330px] w-full max-w-[560px] self-center">
        <g>
          {edges.map((edge, index) => {
            const from = nodeMap.get(String(edge.from));
            const to = nodeMap.get(String(edge.to));
            if (!from || !to) return null;
            const x1 = asNumber(from.x);
            const y1 = asNumber(from.y);
            const x2 = asNumber(to.x);
            const y2 = asNumber(to.y);
            const isActive = isEdgeActive(edge, activeEdgeIds);
            return (
              <g key={`${edge.from}-${edge.to}-${index}`}>
                <motion.line
                  x1={x1}
                  y1={y1}
                  x2={x2}
                  y2={y2}
                  stroke={isActive ? EDGE_ACTIVE : EDGE}
                  strokeWidth={isActive ? 4 : 2}
                  strokeLinecap="round"
                  initial={false}
                  animate={{
                    opacity: isActive ? 1 : 0.72,
                    pathLength: isActive ? [0.35, 1] : 1,
                  }}
                  transition={{ duration: 0.45, ease: 'easeOut' }}
                />
                <motion.rect
                  x={(x1 + x2) / 2 - 9}
                  y={(y1 + y2) / 2 - 17}
                  width="18"
                  height="14"
                  rx="4"
                  fill={isActive ? BLUE_LIGHT : '#FFFFFF'}
                  stroke={isActive ? BLUE : '#E5E7EB'}
                  initial={false}
                  animate={{ scale: isActive ? 1.08 : 1 }}
                  transition={{ duration: 0.25 }}
                />
                <motion.text
                  x={(x1 + x2) / 2}
                  y={(y1 + y2) / 2 - 7}
                  textAnchor="middle"
                  className="text-[9px] font-bold"
                  fill={isActive ? BLUE_DARK : MUTED}
                  initial={false}
                  animate={{ scale: isActive ? 1.1 : 1 }}
                  transition={{ duration: 0.25 }}
                >
                  {String(edge.weight)}
                </motion.text>
              </g>
            );
          })}
        </g>

        <g>
          {nodes.map((node) => {
            const id = String(node.id);
            const isSource = Boolean(node.source);
            const isCurrent = id === currentNodeId;
            const isSettled = settledNodeIds.has(id);
            return (
              <g key={id}>
                <motion.circle
                  cx={asNumber(node.x)}
                  cy={asNumber(node.y)}
                  r={isCurrent ? 20 : 18}
                  fill={isSource ? RED : isSettled ? BLUE_LIGHT : '#FFFFFF'}
                  stroke={isCurrent ? BLUE_DARK : isSettled ? BLUE : '#CBD5E1'}
                  strokeWidth={isCurrent ? 4 : 2}
                  initial={false}
                  animate={{ scale: isCurrent ? [1, 1.08, 1] : 1 }}
                  transition={{ duration: 0.5 }}
                />
                <motion.text
                  x={asNumber(node.x)}
                  y={asNumber(node.y) + 4}
                  textAnchor="middle"
                  className="text-[13px] font-bold"
                  fill={isSource || isSettled ? (isSource ? '#FFFFFF' : BLUE_DARK) : INK}
                  initial={false}
                  animate={{ scale: isCurrent ? 1.08 : 1 }}
                  transition={{ duration: 0.25 }}
                >
                  {id}
                </motion.text>
              </g>
            );
          })}
        </g>

        <g transform="translate(18 244)">
          {distances.map((distance, index) => (
            <g key={`distance-${index}`} transform={`translate(${index * 44}, 0)`}>
              <motion.g
                initial={false}
                animate={{ y: updatedDistanceIndices.has(index) ? [0, -4, 0] : 0 }}
                transition={{ duration: 0.4 }}
              >
                <rect width="42" height="22" rx="5" fill={BLUE} stroke="#ffffff" strokeWidth="1.5" />
                <text x="21" y="15" textAnchor="middle" className="fill-white text-[9px] font-bold">
                  {index}
                </text>
                <motion.rect
                  y="23"
                  width="42"
                  height="28"
                  rx="5"
                  fill={updatedDistanceIndices.has(index) ? BLUE_LIGHT : '#F8FAFC'}
                  stroke={updatedDistanceIndices.has(index) ? BLUE : '#E5E7EB'}
                  strokeWidth="1.5"
                  initial={false}
                  animate={{ scale: updatedDistanceIndices.has(index) ? 1.04 : 1 }}
                  transition={{ duration: 0.3 }}
                />
                <text x="21" y="42" textAnchor="middle" className="fill-[#111827] text-[12px] font-bold">
                  {distance}
                </text>
              </motion.g>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

function MergeSortShowcase({ payload }: { payload: ShowcasePayload }) {
  const levels = asNestedRecordArray(payload.levels);
  const nodeWidth = (count: number) => count * 48;

  const boxes = levels.flatMap((level, levelIndex) =>
    level.map((node, nodeIndex) => ({
      ...node,
      key: `${levelIndex}-${nodeIndex}`,
      values: asNumberArray(node.values),
      final: Boolean(node.final),
      x: asNumber(node.x),
      y: asNumber(node.y),
    })),
  );

  const arrows = [
    [320, 54, 160, 82, '분할'],
    [320, 54, 480, 82, '분할'],
    [160, 128, 95, 157, '분할'],
    [160, 128, 225, 157, '분할'],
    [480, 128, 415, 157, '분할'],
    [480, 128, 545, 157, '분할'],
    [95, 203, 70, 232, '분할'],
    [95, 203, 140, 232, '분할'],
    [225, 203, 205, 232, '분할'],
    [225, 203, 275, 232, '분할'],
    [415, 203, 390, 232, '분할'],
    [415, 203, 460, 232, '분할'],
    [545, 203, 525, 232, '분할'],
    [545, 203, 595, 232, '분할'],
    [70, 278, 105, 307, '합병'],
    [140, 278, 105, 307, '합병'],
    [205, 278, 240, 307, '합병'],
    [275, 278, 240, 307, '합병'],
    [390, 278, 425, 307, '합병'],
    [460, 278, 425, 307, '합병'],
    [525, 278, 560, 307, '합병'],
    [595, 278, 560, 307, '합병'],
    [105, 354, 175, 382, '합병'],
    [240, 354, 175, 382, '합병'],
    [425, 354, 495, 382, '합병'],
    [560, 354, 495, 382, '합병'],
    [175, 430, 320, 456, '합병'],
    [495, 430, 320, 456, '합병'],
  ] as const;

  return (
    <div className="flex h-full min-h-[360px] items-center justify-center overflow-auto rounded-lg bg-white p-3">
      <svg viewBox="0 0 640 530" className="h-full min-h-[340px] w-full min-w-[620px] max-w-[900px]">
        <defs>
          <marker id="showcase-red-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
            <path d="M0,0 L8,4 L0,8 Z" fill={RED} />
          </marker>
        </defs>

        {arrows.map(([x1, y1, x2, y2, label], index) => (
          <g key={`arrow-${index}`}>
            <line
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
              stroke={RED}
              strokeWidth="2.5"
              markerEnd="url(#showcase-red-arrow)"
            />
            {index % 2 === 0 && (
              <text
                x={(x1 + x2) / 2}
                y={(y1 + y2) / 2 - 8}
                textAnchor="middle"
                className="fill-black text-[15px] font-semibold"
              >
                {label}
              </text>
            )}
          </g>
        ))}

        {boxes.map((box) => (
          <g key={box.key} transform={`translate(${box.x - nodeWidth(box.values.length) / 2}, ${box.y})`}>
            {box.values.map((value, index) => (
              <g key={`${box.key}-${index}`} transform={`translate(${index * 48}, 0)`}>
                <rect
                  width="48"
                  height="48"
                  fill={box.final ? GREEN : BLUE}
                  stroke={box.final ? GREEN_DARK : BLUE_DARK}
                  strokeWidth="2"
                />
                <text x="24" y="31" textAnchor="middle" className="fill-white text-[24px] font-bold">
                  {value}
                </text>
              </g>
            ))}
          </g>
        ))}
      </svg>
    </div>
  );
}

function RadixSortShowcase({ payload }: { payload: ShowcasePayload }) {
  const input = asNumberArray(payload.input);
  const output = asNumberArray(payload.output);
  const buckets = asNestedNumberArray(payload.buckets);

  return (
    <div className="flex h-full min-h-[300px] items-center justify-center overflow-auto rounded-lg bg-white p-3">
      <svg viewBox="0 0 520 230" className="h-full max-h-[360px] min-h-[250px] w-full min-w-[520px]">
        <defs>
          <marker id="showcase-red-small" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill={RED} />
          </marker>
          <marker id="showcase-blue-small" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="#1d4ed8" />
          </marker>
        </defs>

        <NumberRow values={input} x={15} y={96} fill="#f7d8c3" stroke="#b48568" />
        <NumberRow values={output} x={405} y={96} fill="#f7d8c3" stroke="#b48568" />

        {buckets.map((bucket, index) => {
          const y = 12 + index * 20;
          const hasValue = bucket.length > 0;
          const value = bucket[0];
          return (
            <g key={`bucket-${index}`}>
              <text x="222" y={y + 11} textAnchor="middle" className="fill-black text-[9px] font-semibold">
                {index}
              </text>
              <rect x="235" y={y} width="74" height="14" fill="#d7f0f2" stroke="#68aeb7" strokeWidth="1.5" />
              <path d={`M238 ${y + 11} L306 ${y + 7}`} stroke="#8bd1d8" strokeWidth="2" />
              {hasValue && (
                <g>
                  <circle cx="242" cy={y + 7} r="6" fill="#fff65a" stroke="#9a9a00" />
                  <text x="242" y={y + 10} textAnchor="middle" className="fill-black text-[8px] font-bold">
                    {value}
                  </text>
                  <line
                    x1="92"
                    y1="105"
                    x2="232"
                    y2={y + 7}
                    stroke={RED}
                    strokeWidth="1.2"
                    strokeDasharray="3 3"
                    markerEnd="url(#showcase-red-small)"
                  />
                  <line
                    x1="310"
                    y1={y + 7}
                    x2="405"
                    y2="105"
                    stroke="#1d4ed8"
                    strokeWidth="1.2"
                    strokeDasharray="3 3"
                    markerEnd="url(#showcase-blue-small)"
                  />
                </g>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function NumberRow({
  values,
  x,
  y,
  fill,
  stroke,
}: {
  values: number[];
  x: number;
  y: number;
  fill: string;
  stroke: string;
}) {
  return (
    <g transform={`translate(${x}, ${y})`}>
      {values.map((value, index) => (
        <g key={`${value}-${index}`} transform={`translate(${index * 16}, 0)`}>
          <rect width="16" height="20" fill={fill} stroke={stroke} strokeWidth="1" />
          <text x="8" y="14" textAnchor="middle" className="fill-black text-[10px] font-bold">
            {value}
          </text>
        </g>
      ))}
    </g>
  );
}

function asRecordArray(value: unknown): Record<string, unknown>[] {
  return Array.isArray(value)
    ? value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === 'object' && !Array.isArray(item))
    : [];
}

function asNestedRecordArray(value: unknown): Record<string, unknown>[][] {
  return Array.isArray(value) ? value.map(asRecordArray) : [];
}

function asNumberArray(value: unknown): number[] {
  return Array.isArray(value) ? value.filter((item): item is number => typeof item === 'number') : [];
}

function asNestedNumberArray(value: unknown): number[][] {
  return Array.isArray(value) ? value.map(asNumberArray) : [];
}

function isEdgeActive(edge: Record<string, unknown>, activeEdgeIds: Set<string>): boolean {
  const from = String(edge.from);
  const to = String(edge.to);
  return activeEdgeIds.has(`${from}-${to}`) || activeEdgeIds.has(`${to}-${from}`);
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function asNumber(value: unknown): number {
  return typeof value === 'number' ? value : 0;
}
