from __future__ import annotations

from collections import Counter
import re
from typing import Any

from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate


class FlowchartExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "flowchart"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        if not execution.steps:
            return None

        source_lines = execution.source_code.splitlines()
        trace_line_numbers = [
            step.line_number
            for step in execution.steps
            if 1 <= step.line_number <= len(source_lines)
        ]
        if not trace_line_numbers:
            return None

        line_numbers = sorted(set(trace_line_numbers))
        nesting_depths = _compute_nesting_depths(source_lines)
        nodes = [
            {
                "id": "start",
                "label": "START",
                "type": "terminal",
                "lineNumber": None,
                "nestingDepth": 0,
            },
            *[
                {
                    "id": _node_id(line_number),
                    "label": source_lines[line_number - 1].strip() or f"line {line_number}",
                    "type": _classify_line(source_lines[line_number - 1]),
                    "lineNumber": line_number,
                    "nestingDepth": nesting_depths.get(line_number, 0),
                }
                for line_number in line_numbers
            ],
            {
                "id": "end",
                "label": "END",
                "type": "terminal",
                "lineNumber": None,
                "nestingDepth": 0,
            },
        ]

        base_edges = _build_base_edges(
            nodes=nodes,
            line_numbers=line_numbers,
            trace_line_numbers=trace_line_numbers,
        )
        cumulative_edge_counts: Counter[tuple[str, str]] = Counter()
        cumulative_line_counts: Counter[int] = Counter()
        step_states: list[ExecutionVisualizationStepRead] = []
        previous_node_id = "start"

        for step in execution.steps:
            current_node_id = _node_id(step.line_number)
            if current_node_id not in {node["id"] for node in nodes}:
                continue

            cumulative_line_counts[step.line_number] += 1
            cumulative_edge_counts[(previous_node_id, current_node_id)] += 1
            active_edge_id = f"{previous_node_id}->{current_node_id}"

            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    payload={
                        "nodes": _decorate_nodes(
                            nodes=nodes,
                            current_node_id=current_node_id,
                            line_counts=cumulative_line_counts,
                        ),
                        "edges": _decorate_edges(
                            edges=base_edges,
                            active_edge_id=active_edge_id,
                            edge_counts=cumulative_edge_counts,
                        ),
                        "currentNodeId": current_node_id,
                        "activeEdgeId": active_edge_id,
                        "visitCounts": dict(cumulative_line_counts),
                    },
                    message=_build_message(
                        source_lines=source_lines,
                        line_number=step.line_number,
                        visit_count=cumulative_line_counts[step.line_number],
                    ),
                )
            )
            previous_node_id = current_node_id

        if step_states:
            last_node_id = step_states[-1].payload.get("currentNodeId")
            if isinstance(last_node_id, str):
                cumulative_edge_counts[(last_node_id, "end")] += 1
                last_state = step_states[-1]
                last_state.payload["edges"] = _decorate_edges(
                    edges=base_edges,
                    active_edge_id=f"{last_node_id}->end",
                    edge_counts=cumulative_edge_counts,
                )
                last_state.payload["activeEdgeId"] = f"{last_node_id}->end"

        return ExecutionVisualizationRead(
            kind="flowchart",
            source_variable=None,
            step_states=step_states,
            metadata={
                "nodeCount": len(nodes),
                "edgeCount": len(base_edges),
                "maxNestingDepth": max(nesting_depths.values(), default=0),
            },
        )


def _node_id(line_number: int) -> str:
    return f"line-{line_number}"


def _compute_nesting_depths(source_lines: list[str]) -> dict[int, int]:
    if any("{" in line or "}" in line for line in source_lines):
        return _compute_brace_nesting_depths(source_lines)
    return _compute_indent_nesting_depths(source_lines)


def _compute_indent_nesting_depths(source_lines: list[str]) -> dict[int, int]:
    indent_widths = sorted(
        {
            len(line) - len(line.lstrip(" "))
            for line in source_lines
            if line.strip() and len(line) > len(line.lstrip(" "))
        }
    )
    if not indent_widths:
        return {index: 0 for index, _ in enumerate(source_lines, start=1)}

    return {
        index: sum(1 for width in indent_widths if width <= len(line) - len(line.lstrip(" ")))
        for index, line in enumerate(source_lines, start=1)
    }


def _compute_brace_nesting_depths(source_lines: list[str]) -> dict[int, int]:
    depths: dict[int, int] = {}
    depth = 0
    for index, line in enumerate(source_lines, start=1):
        stripped = line.strip()
        leading_closers = len(re.match(r"^\}*", stripped).group(0)) if stripped else 0
        line_depth = max(depth - leading_closers, 0)
        depths[index] = line_depth
        depth = max(depth + line.count("{") - line.count("}"), 0)
    return depths


def _build_base_edges(
    *,
    nodes: list[dict[str, Any]],
    line_numbers: list[int],
    trace_line_numbers: list[int],
) -> list[dict[str, Any]]:
    edge_pairs: list[tuple[str, str]] = []
    if line_numbers:
        edge_pairs.append(("start", _node_id(trace_line_numbers[0])))

    for previous, current in zip(trace_line_numbers, trace_line_numbers[1:]):
        edge_pairs.append((_node_id(previous), _node_id(current)))

    if trace_line_numbers:
        edge_pairs.append((_node_id(trace_line_numbers[-1]), "end"))

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for source, target in edge_pairs:
        if (source, target) in seen:
            continue
        seen.add((source, target))
        deduped.append(
            {
                "id": f"{source}->{target}",
                "from": source,
                "to": target,
                **_describe_edge(source, target, nodes),
            }
        )
    return deduped


def _describe_edge(source_id: str, target_id: str, nodes: list[dict[str, Any]]) -> dict[str, str]:
    node_map = {str(node["id"]): node for node in nodes}
    source = node_map.get(source_id)
    target = node_map.get(target_id)
    if source is None or target is None:
        return {"relation": "flow"}

    source_line = source.get("lineNumber")
    target_line = target.get("lineNumber")
    source_type = str(source.get("type", "statement"))
    source_depth = int(source.get("nestingDepth") or 0)
    target_depth = int(target.get("nestingDepth") or 0)

    if not isinstance(source_line, int) or not isinstance(target_line, int):
        return {"relation": "flow"}

    if target_line <= source_line:
        if source_type == "loop" or target.get("type") == "loop":
            return {"relation": "loop-back", "label": "반복"}
        return {"relation": "back"}

    if source_type == "loop":
        if target_depth > source_depth:
            return {"relation": "decision-yes", "label": "YES"}
        return {"relation": "decision-no", "label": "NO"}

    if source_type == "branch":
        if target_depth > source_depth:
            return {"relation": "decision-yes", "label": "YES"}
        return {"relation": "decision-no", "label": "NO"}

    if target_line > source_line + 1:
        return {"relation": "jump"}
    return {"relation": "flow"}


def _decorate_nodes(
    *,
    nodes: list[dict[str, Any]],
    current_node_id: str,
    line_counts: Counter[int],
) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for node in nodes:
        line_number = node.get("lineNumber")
        visit_count = line_counts.get(line_number, 0) if isinstance(line_number, int) else 0
        decorated.append(
            {
                **node,
                "isActive": node["id"] == current_node_id,
                "isVisited": visit_count > 0,
                "visitCount": visit_count,
            }
        )
    return decorated


def _decorate_edges(
    *,
    edges: list[dict[str, Any]],
    active_edge_id: str,
    edge_counts: Counter[tuple[str, str]],
) -> list[dict[str, Any]]:
    decorated: list[dict[str, Any]] = []
    for edge in edges:
        key = (str(edge["from"]), str(edge["to"]))
        visit_count = edge_counts.get(key, 0)
        decorated.append(
            {
                **edge,
                "isActive": edge["id"] == active_edge_id,
                "isVisited": visit_count > 0,
                "visitCount": visit_count,
            }
        )
    return decorated


def _classify_line(raw_line: str) -> str:
    line = raw_line.strip()
    lowered = line.lower()
    if not line:
        return "statement"
    if lowered.startswith(("if ", "elif ", "else")) or lowered.startswith(("if(", "else if")):
        return "branch"
    if lowered.startswith(("for ", "while ")) or lowered.startswith(("for(", "while(")):
        return "loop"
    if "print(" in lowered or "printf(" in lowered or "system.out.print" in lowered:
        return "output"
    if lowered.startswith("return"):
        return "return"
    if _looks_like_comparison(line):
        return "branch"
    return "statement"


def _looks_like_comparison(line: str) -> bool:
    expression = re.sub(r"(['\"]).*?\1", "", line)
    return bool(re.search(r"(?<![<>=!])(?:==|!=|<=|>=|<|>)(?![<>=])", expression))


def _build_message(*, source_lines: list[str], line_number: int, visit_count: int) -> str:
    if not (1 <= line_number <= len(source_lines)):
        return f"line {line_number}"
    label = source_lines[line_number - 1].strip()
    suffix = f" ({visit_count}번째 방문)" if visit_count > 1 else ""
    return f"{line_number}번 줄 실행: {label}{suffix}"
