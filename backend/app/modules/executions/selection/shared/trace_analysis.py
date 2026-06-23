from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.modules.executions.domain.trace import TraceExecutionResult


GRAPH_NAME_HINTS = {
    "adj",
    "adjacency",
    "edge",
    "edges",
    "graph",
    "neighbor",
    "neighbors",
    "visited",
}
GRAPH_STRUCTURE_NAME_HINTS = GRAPH_NAME_HINTS - {"visited"}
DP_NAME_HINTS = {"arrayfy", "cost", "dist", "distance", "dp", "fy", "matrix", "table"}
QUEUE_NAME_HINTS = {"deque", "enqueue", "front", "poll", "queue", "rear"}
STACK_NAME_HINTS = {"pop", "push", "stack", "top"}
TREE_NAME_HINTS = {"left", "right", "root", "tree"}
ARRAY_NAME_HINTS = {"arr", "array", "list", "numbers", "nums", "values"}
SCALAR_TRACE_TYPES = (str, int, float, bool, type(None))


def suggest_visualization_mode_from_trace(
    *,
    result: TraceExecutionResult,
    supported_modes: set[str],
) -> str | None:
    if not result.steps:
        return None

    function_names = {step.function_name.lower() for step in result.steps if step.function_name}
    max_call_depth = max(
        (
            len(step.call_stack)
            or _safe_metadata_int(step.metadata.get("callStackDepth"), default=0)
        )
        for step in result.steps
    )

    snapshots = [step.merged_snapshot for step in result.steps if step.merged_snapshot]
    if not snapshots:
        if max_call_depth >= 2 or _has_recursive_call(result):
            return _first_supported(("call-stack",), supported_modes)
        return None

    states = _collect_variable_states(snapshots)
    names = set(states)

    if _has_palindrome_pointers(snapshots):
        return _first_supported(("palindrome-pointers", "array-cells"), supported_modes)

    if _has_dp_matrix(states=states, function_names=function_names):
        return _first_supported(("dp-table", "array-cells"), supported_modes)

    if _has_tree(states=states, names=names):
        return _first_supported(("tree-binary", "graph-node-edge"), supported_modes)

    if _has_graph(states=states, names=names):
        if _has_any_name(names, QUEUE_NAME_HINTS):
            return _first_supported(("graph-bfs-traversal", "graph-node-edge"), supported_modes)
        if _has_any_name(names, STACK_NAME_HINTS) or _has_recursive_call(result):
            return _first_supported(("graph-dfs-traversal", "graph-node-edge"), supported_modes)
        return _first_supported(("graph-node-edge",), supported_modes)

    if _has_any_name(names, QUEUE_NAME_HINTS):
        return _first_supported(("queue-horizontal", "queue"), supported_modes)

    if _has_any_name(names, STACK_NAME_HINTS):
        return _first_supported(("stack-vertical", "stack"), supported_modes)

    has_recursive_call = _has_recursive_call(result)

    if has_recursive_call:
        return _first_supported(("call-stack",), supported_modes)

    if _has_numeric_array(states=states):
        return _first_supported(("array-bars", "array-cells"), supported_modes)

    if _has_sequence(states=states):
        return _first_supported(("array-cells",), supported_modes)

    if max_call_depth >= 2:
        return _first_supported(("call-stack",), supported_modes)

    if _has_repeated_line_transition(result):
        return _first_supported(("flowchart", "array-cells"), supported_modes)

    if _has_scalar_state_change(states=states):
        return _first_supported(("array-cells",), supported_modes)

    return None


def has_visualization_signal_from_trace(result: TraceExecutionResult) -> bool:
    function_names = {step.function_name for step in result.steps if step.function_name}
    if len(function_names - {"<module>", "main"}) > 0:
        return True

    for step in result.steps:
        if len(step.call_stack) > 1:
            return True
        if _snapshot_has_visual_structure(step.locals_snapshot):
            return True
        if _snapshot_has_visual_structure(step.globals_snapshot):
            return True
        if _snapshot_has_scalar_state(step.locals_snapshot):
            return True
        if _snapshot_has_scalar_state(step.globals_snapshot):
            return True

    return False


def _collect_variable_states(snapshots: Iterable[dict[str, Any]]) -> dict[str, list[Any]]:
    states: dict[str, list[Any]] = {}
    for snapshot in snapshots:
        for name, value in snapshot.items():
            if name.startswith("__"):
                continue
            states.setdefault(str(name), []).append(value)
    return states


def _snapshot_has_visual_structure(snapshot: dict[str, Any]) -> bool:
    for value in snapshot.values():
        if not isinstance(value, SCALAR_TRACE_TYPES):
            return True
    return False


def _snapshot_has_scalar_state(snapshot: dict[str, Any]) -> bool:
    return any(
        not str(name).startswith("__") and isinstance(value, SCALAR_TRACE_TYPES)
        for name, value in snapshot.items()
    )


def _first_supported(candidates: Iterable[str], supported_modes: set[str]) -> str | None:
    for candidate in candidates:
        if candidate in supported_modes:
            return candidate
    return None


def _has_any_name(names: set[str], hints: set[str]) -> bool:
    lowered_names = {name.lower() for name in names}
    return any(any(hint in name for hint in hints) for name in lowered_names)


def _safe_metadata_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _has_recursive_call(result: TraceExecutionResult) -> bool:
    for step in result.steps:
        frame_names = [frame.function_name for frame in step.call_stack if frame.function_name]
        if len(frame_names) != len(set(frame_names)):
            return True
    return False


def _has_palindrome_pointers(snapshots: list[dict[str, Any]]) -> bool:
    for snapshot in snapshots:
        has_left = isinstance(snapshot.get("left"), int)
        has_right = isinstance(snapshot.get("right"), int)
        if not (has_left and has_right):
            continue
        if any(_is_sequence(value) for value in snapshot.values()):
            return True
    return False


def _has_dp_matrix(
    *,
    states: dict[str, list[Any]],
    function_names: set[str],
) -> bool:
    has_dp_function = any("floyd" in name or "warshall" in name or "dp" in name for name in function_names)
    for name, values in states.items():
        if not any(_is_matrix(value) for value in values):
            continue
        lowered_name = name.lower()
        if has_dp_function or any(hint in lowered_name for hint in DP_NAME_HINTS):
            return True
    return False


def _has_graph(
    *,
    states: dict[str, list[Any]],
    names: set[str],
) -> bool:
    if _has_any_name(names, GRAPH_STRUCTURE_NAME_HINTS):
        return True

    for values in states.values():
        if any(_is_adjacency_map(value) for value in values):
            return True
    return False


def _has_tree(
    *,
    states: dict[str, list[Any]],
    names: set[str],
) -> bool:
    if _has_any_name(names, TREE_NAME_HINTS):
        return True
    for values in states.values():
        if any(_is_tree_node(value) for value in values):
            return True
    return False


def _has_numeric_array(*, states: dict[str, list[Any]]) -> bool:
    named_candidates: list[str] = []
    fallback_candidates: list[str] = []

    for name, values in states.items():
        if not any(_is_numeric_sequence(value) for value in values):
            continue
        if any(hint in name.lower() for hint in ARRAY_NAME_HINTS):
            named_candidates.append(name)
        else:
            fallback_candidates.append(name)

    return bool(named_candidates or fallback_candidates)


def _has_sequence(*, states: dict[str, list[Any]]) -> bool:
    return any(any(_is_sequence(value) for value in values) for values in states.values())


def _has_scalar_state_change(*, states: dict[str, list[Any]]) -> bool:
    for name, values in states.items():
        if name.startswith("__"):
            continue
        scalar_values = [value for value in values if isinstance(value, SCALAR_TRACE_TYPES)]
        if len(scalar_values) < 2:
            continue
        if any(previous != current for previous, current in zip(scalar_values, scalar_values[1:])):
            return True
    return False


def _has_repeated_line_transition(result: TraceExecutionResult) -> bool:
    seen: set[int] = set()
    for step in result.steps:
        if step.line_number in seen:
            return True
        seen.add(step.line_number)
    return False


def _is_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple, str)) and len(value) >= 2


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_numeric_sequence(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and len(value) >= 2 and all(_is_number(item) for item in value)


def _is_matrix(value: Any) -> bool:
    return (
        isinstance(value, (list, tuple))
        and len(value) >= 2
        and all(isinstance(row, (list, tuple)) for row in value)
    )


def _is_adjacency_map(value: Any) -> bool:
    if not isinstance(value, dict) or not value:
        return False
    if _is_tree_node(value):
        return False
    edge_like_values = 0
    for child in value.values():
        if isinstance(child, (list, tuple, dict)):
            edge_like_values += 1
    return edge_like_values >= max(1, len(value) // 2)


def _is_tree_node(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    keys = {str(key).lower() for key in value}
    return bool({"left", "right"} & keys) and bool({"value", "val", "data", "key"} & keys)
