from dataclasses import dataclass
from typing import Any

from app.modules.executions.presentation.http.schemas import ExecutionRead


@dataclass(slots=True)
class TrackStats:
    occurrence_count: int = 0
    change_count: int = 0
    max_size: int = 0


def merge_scope_snapshots(
    locals_snapshot: dict[str, Any],
    globals_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {**(globals_snapshot or {}), **locals_snapshot}


def is_numeric(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def build_scalar_badges(
    locals_snapshot: dict[str, Any],
    *,
    exclude_names: set[str] | None = None,
    limit: int = 6,
) -> list[dict[str, Any]]:
    excluded = exclude_names or set()
    badges: list[dict[str, Any]] = []

    for name, value in locals_snapshot.items():
        if name in excluded:
            continue
        if isinstance(value, (list, tuple, dict)):
            continue
        if not is_scalar(value):
            continue
        badges.append({"name": name, "value": value})

    badges.sort(
        key=lambda badge: (
            0 if isinstance(badge["value"], int | float) and not isinstance(badge["value"], bool) else 1,
            badge["name"],
        )
    )
    return badges[:limit]


def build_index_pointers(
    locals_snapshot: dict[str, Any],
    *,
    length: int,
    exclude_names: set[str] | None = None,
    limit: int = 6,
) -> list[dict[str, int]]:
    if length <= 0:
        return []

    excluded = exclude_names or set()
    pointers: list[dict[str, int]] = []

    for name, value in locals_snapshot.items():
        if name in excluded:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            continue
        if 0 <= value < length:
            pointers.append({"name": name, "index": value})

    pointers.sort(key=lambda pointer: (pointer["index"], pointer["name"]))
    return pointers[:limit]


def build_numeric_sequence_map(locals_snapshot: dict[str, Any]) -> dict[str, list[int | float]]:
    sequence_map: dict[str, list[int | float]] = {}

    for name, value in locals_snapshot.items():
        if not isinstance(value, (list, tuple)):
            continue
        sequence = list(value)
        if not sequence or not all(is_numeric(item) for item in sequence):
            continue
        sequence_map[name] = sequence

    return sequence_map


def build_scalar_sequence_map(locals_snapshot: dict[str, Any]) -> dict[str, list[Any]]:
    sequence_map: dict[str, list[Any]] = {}

    for name, value in locals_snapshot.items():
        if not isinstance(value, (list, tuple)):
            continue
        sequence = list(value)
        if not sequence or not all(is_scalar(item) for item in sequence):
            continue
        sequence_map[name] = sequence

    return sequence_map


def build_character_sequence_map(locals_snapshot: dict[str, Any]) -> dict[str, list[str]]:
    sequence_map: dict[str, list[str]] = {}

    for name, value in locals_snapshot.items():
        if not isinstance(value, str):
            continue
        if not value:
            continue
        sequence_map[name] = list(value)

    return sequence_map


def build_numeric_matrix_map(locals_snapshot: dict[str, Any]) -> dict[str, list[list[int | float]]]:
    matrix_map: dict[str, list[list[int | float]]] = {}

    for name, value in locals_snapshot.items():
        if not isinstance(value, (list, tuple)) or not value:
            continue
        rows = list(value)
        if not all(isinstance(row, (list, tuple)) and row for row in rows):
            continue
        normalized_rows = [list(row) for row in rows]
        if not all(all(is_numeric(cell) for cell in row) for row in normalized_rows):
            continue
        matrix_map[name] = normalized_rows

    return matrix_map


def trim_leading_matrix_padding(
    matrix: list[list[int | float]],
) -> tuple[list[list[int | float]], list[int], list[int]]:
    if not matrix or not matrix[0]:
        return matrix, list(range(len(matrix))), []

    row_count = len(matrix)
    col_count = max((len(row) for row in matrix), default=0)
    if row_count < 2 or col_count < 2:
        return matrix, list(range(row_count)), list(range(col_count))

    if any(len(row) != col_count for row in matrix):
        return matrix, list(range(row_count)), list(range(col_count))

    first_row = matrix[0]
    first_col = [row[0] for row in matrix]
    row_sentinel = first_row[0]
    col_sentinel = first_col[0]

    if not all(value == row_sentinel for value in first_row):
        return matrix, list(range(row_count)), list(range(col_count))
    if not all(value == col_sentinel for value in first_col):
        return matrix, list(range(row_count)), list(range(col_count))
    if row_sentinel != col_sentinel:
        return matrix, list(range(row_count)), list(range(col_count))

    trimmed_matrix = [row[1:] for row in matrix[1:]]
    if not trimmed_matrix or not trimmed_matrix[0]:
        return matrix, list(range(row_count)), list(range(col_count))

    sentinel = row_sentinel
    has_non_sentinel_value = any(
        any(cell != sentinel for cell in row)
        for row in trimmed_matrix
    )
    if not has_non_sentinel_value:
        return matrix, list(range(row_count)), list(range(col_count))

    return trimmed_matrix, list(range(1, row_count)), list(range(1, col_count))


def select_primary_name(
    execution: ExecutionRead,
    *,
    extractor,
    size_of,
) -> str | None:
    track_stats: dict[str, TrackStats] = {}
    previous_values: dict[str, Any] = {}

    for step in execution.steps:
        current_values = extractor(
            merge_scope_snapshots(step.locals_snapshot, step.globals_snapshot)
        )
        for name, value in current_values.items():
            stats = track_stats.setdefault(name, TrackStats())
            stats.occurrence_count += 1
            stats.max_size = max(stats.max_size, size_of(value))

            previous = previous_values.get(name)
            if previous is not None and previous != value:
                stats.change_count += 1

        previous_values = current_values

    if not track_stats:
        return None

    return max(
        track_stats.items(),
        key=lambda item: (
            item[1].occurrence_count,
            item[1].change_count,
            item[1].max_size,
        ),
    )[0]


def resolve_active_indices(previous_values: list[Any] | None, current_values: list[Any]) -> list[int]:
    if previous_values is None:
        return []

    if len(previous_values) != len(current_values):
        return list(range(max(len(previous_values), len(current_values))))

    return [
        index
        for index, (previous, current) in enumerate(zip(previous_values, current_values))
        if previous != current
    ]


def resolve_matched_indices(values: list[Any], final_values: list[Any]) -> list[int]:
    return [
        index
        for index, (current, final) in enumerate(zip(values, final_values))
        if current == final
    ]


def resolve_active_cells(
    previous_matrix: list[list[Any]] | None,
    current_matrix: list[list[Any]],
) -> list[list[int]]:
    if previous_matrix is None:
        return []

    active_cells: list[list[int]] = []
    max_rows = max(len(previous_matrix), len(current_matrix))

    for row_index in range(max_rows):
        previous_row = previous_matrix[row_index] if row_index < len(previous_matrix) else []
        current_row = current_matrix[row_index] if row_index < len(current_matrix) else []
        max_cols = max(len(previous_row), len(current_row))
        for col_index in range(max_cols):
            previous = previous_row[col_index] if col_index < len(previous_row) else None
            current = current_row[col_index] if col_index < len(current_row) else None
            if previous != current:
                active_cells.append([row_index, col_index])

    return active_cells


def resolve_matched_cells(
    current_matrix: list[list[Any]],
    final_matrix: list[list[Any]],
) -> list[list[int]]:
    matched_cells: list[list[int]] = []
    for row_index, row in enumerate(current_matrix):
        if row_index >= len(final_matrix):
            break
        for col_index, value in enumerate(row):
            if col_index >= len(final_matrix[row_index]):
                break
            if value == final_matrix[row_index][col_index]:
                matched_cells.append([row_index, col_index])
    return matched_cells


def flatten_nested_binary_tree(value: Any, *, root_id: str = "root") -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    if "left" not in value and "right" not in value:
        return None

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []

    def walk(node: Any, node_id: str) -> None:
        if node is None or not isinstance(node, dict):
            return

        label = node.get("value", node.get("val", node.get("data", node_id)))
        nodes.append(
            {
                "id": node_id,
                "label": str(label),
                "value": label,
                "depth": node_id.count("."),
            }
        )

        left = node.get("left")
        right = node.get("right")
        if isinstance(left, dict):
            left_id = f"{node_id}.L"
            edges.append({"from": node_id, "to": left_id, "label": "left"})
            walk(left, left_id)
        if isinstance(right, dict):
            right_id = f"{node_id}.R"
            edges.append({"from": node_id, "to": right_id, "label": "right"})
            walk(right, right_id)

    walk(value, root_id)
    if not nodes:
        return None

    return {"nodes": nodes, "edges": edges}


def build_binary_tree_map(locals_snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tree_map: dict[str, dict[str, Any]] = {}

    for name, value in locals_snapshot.items():
        flattened = flatten_nested_binary_tree(value, root_id=name)
        if flattened is not None:
            tree_map[name] = flattened

    return tree_map


def build_graph_map(locals_snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
    graph_map: dict[str, dict[str, Any]] = {}

    for name, value in locals_snapshot.items():
        if not isinstance(value, dict) or not value:
            continue
        if not all(is_scalar(node) and isinstance(neighbors, list) for node, neighbors in value.items()):
            continue
        if not all(all(is_scalar(neighbor) for neighbor in neighbors) for neighbors in value.values()):
            continue

        nodes = [{"id": str(node), "label": str(node)} for node in value.keys()]
        edge_set = {
            (str(node), str(neighbor))
            for node, neighbors in value.items()
            for neighbor in neighbors
        }
        edges = [{"from": source, "to": target} for source, target in sorted(edge_set)]
        graph_map[name] = {"nodes": nodes, "edges": edges}

    return graph_map


def resolve_focus_node_ids(
    locals_snapshot: dict[str, Any],
    nodes: list[dict[str, Any]],
    *,
    exclude_names: set[str] | None = None,
) -> list[str]:
    excluded = exclude_names or set()
    label_to_ids: dict[str, list[str]] = {}

    for node in nodes:
        node_id = str(node["id"])
        candidates = {
            str(node.get("id", "")),
            str(node.get("label", "")),
            str(node.get("value", "")),
        }
        for candidate in candidates:
            if not candidate:
                continue
            current = label_to_ids.get(candidate, [])
            current.append(node_id)
            label_to_ids[candidate] = current

    focused_ids: list[str] = []
    seen: set[str] = set()
    for name, value in locals_snapshot.items():
        if name in excluded or not is_scalar(value):
            continue
        for node_id in label_to_ids.get(str(value), []):
            if node_id in seen:
                continue
            focused_ids.append(node_id)
            seen.add(node_id)

    return focused_ids
