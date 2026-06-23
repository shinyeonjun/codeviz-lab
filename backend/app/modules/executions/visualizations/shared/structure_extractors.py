from dataclasses import dataclass
from typing import Any

from app.modules.executions.presentation.http.schemas import ExecutionRead

UNAVAILABLE_TRACE_VALUE = "<optimized out>"


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
    if is_unavailable_trace_value(value):
        return False
    return isinstance(value, int | float) and not isinstance(value, bool)


def is_scalar(value: Any) -> bool:
    if is_unavailable_trace_value(value):
        return False
    return value is None or isinstance(value, (bool, int, float, str))


def is_unavailable_trace_value(value: Any) -> bool:
    return value == UNAVAILABLE_TRACE_VALUE


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


def build_scalar_value_map(locals_snapshot: dict[str, Any]) -> dict[str, list[Any]]:
    value_map: dict[str, list[Any]] = {}

    for name, value in locals_snapshot.items():
        if str(name).startswith("__"):
            continue
        if not is_scalar(value):
            continue
        value_map[name] = [value]

    return value_map


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
        graph = _graph_from_adjacency_map(value)
        if graph is None:
            graph = _graph_from_adjacency_matrix(name, value)
        if graph is None:
            graph = _graph_from_edge_list(name, value)
        if graph is not None:
            graph_map[name] = graph

    return graph_map


def _graph_from_adjacency_map(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not value:
        return None

    normalized: dict[Any, list[Any]] = {}
    weighted_neighbors: list[tuple[Any, list[Any]]] = []
    for node, neighbors in value.items():
        if not is_scalar(node):
            return None
        neighbor_values = _sequence_items(neighbors)
        if neighbor_values is None:
            return None
        for neighbor in neighbor_values:
            if is_scalar(neighbor):
                continue
            weighted_neighbor = _sequence_items(neighbor)
            if weighted_neighbor is None or len(weighted_neighbor) < 2:
                return None
            if not all(is_scalar(item) for item in weighted_neighbor):
                return None
            weighted_neighbors.append((node, weighted_neighbor))
        normalized[node] = neighbor_values

    weight_first = _uses_weight_first_neighbors(weighted_neighbors)
    node_ids = {str(node) for node in normalized}
    edges: list[dict[str, str]] = []

    for node, neighbors in normalized.items():
        for neighbor in neighbors:
            if is_scalar(neighbor):
                target = neighbor
                label = None
            else:
                items = _sequence_items(neighbor) or []
                if weight_first:
                    target = items[1]
                    label = items[0]
                else:
                    target = items[0]
                    label = items[1]

            node_ids.add(str(target))
            edge: dict[str, str] = {"from": str(node), "to": str(target)}
            if label is not None:
                edge["label"] = str(label)
            edges.append(edge)

    return _build_graph_payload(node_ids=node_ids, edges=_deduplicate_edges(edges))


def _uses_weight_first_neighbors(neighbors: list[tuple[Any, list[Any]]]) -> bool:
    if not neighbors:
        return False

    common_self_loops = sum(1 for node, items in neighbors if str(node) == str(items[0]))
    weight_first_self_loops = sum(1 for node, items in neighbors if str(node) == str(items[1]))
    if common_self_loops != weight_first_self_loops:
        return weight_first_self_loops < common_self_loops

    return False


def _graph_from_edge_list(name: str, value: Any) -> dict[str, Any] | None:
    if not _has_graphish_name(name):
        return None

    rows = _sequence_items(value)
    if rows is None or not rows:
        return None

    rows_for_edges: list[list[Any]] = []
    for row in rows:
        items = _sequence_items(row)
        if items is None or len(items) < 2:
            return None
        if not all(is_scalar(item) for item in items):
            return None
        rows_for_edges.append(items)

    edge_candidates = _select_edge_tuples(rows_for_edges)

    if not edge_candidates:
        return None

    node_ids = {source for source, _, _ in edge_candidates}
    node_ids.update(target for _, target, _ in edge_candidates)
    edges = [
        {"from": source, "to": target, **({"label": str(label)} if label is not None else {})}
        for source, target, label in edge_candidates
    ]
    return _build_graph_payload(node_ids=node_ids, edges=edges)


def _graph_from_adjacency_matrix(name: str, value: Any) -> dict[str, Any] | None:
    if not _has_adjacency_matrix_name(name):
        return None

    rows = _sequence_items(value)
    if rows is None or len(rows) < 2:
        return None

    matrix: list[list[Any]] = []
    for row in rows:
        row_items = _sequence_items(row)
        if row_items is None:
            return None
        matrix.append(row_items)

    if any(len(row) != len(matrix) for row in matrix):
        return None
    if not all(all(is_numeric(cell) for cell in row) for row in matrix):
        return None

    node_ids = {str(index) for index in range(len(matrix))}
    edges: list[dict[str, str]] = []
    for row_index, row in enumerate(matrix):
        for col_index, value in enumerate(row):
            if value == 0:
                continue
            edge: dict[str, str] = {"from": str(row_index), "to": str(col_index)}
            if value != 1:
                edge["label"] = str(value)
            edges.append(edge)

    if not edges:
        return None
    return _build_graph_payload(node_ids=node_ids, edges=edges)


def _select_edge_tuples(rows: list[list[Any]]) -> list[tuple[str, str, Any | None]]:
    weighted_first = _uses_weight_first_edges(rows)
    return [_select_edge_tuple(items, weighted_first=weighted_first) for items in rows]


def _select_edge_tuple(items: list[Any], *, weighted_first: bool) -> tuple[str, str, Any | None]:
    if len(items) == 2:
        return str(items[0]), str(items[1]), None
    if weighted_first:
        return str(items[1]), str(items[2]), items[0]
    return str(items[0]), str(items[1]), items[2]


def _uses_weight_first_edges(rows: list[list[Any]]) -> bool:
    triples = [row for row in rows if len(row) >= 3]
    if not triples:
        return False

    common_self_loops = sum(1 for row in triples if str(row[0]) == str(row[1]))
    weight_first_self_loops = sum(1 for row in triples if str(row[1]) == str(row[2]))
    if common_self_loops != weight_first_self_loops:
        return weight_first_self_loops < common_self_loops

    common_nodes = {str(row[0]) for row in triples} | {str(row[1]) for row in triples}
    weight_first_nodes = {str(row[1]) for row in triples} | {str(row[2]) for row in triples}
    if len(common_nodes) != len(weight_first_nodes):
        return len(weight_first_nodes) > len(common_nodes)

    return False


def _sequence_items(value: Any) -> list[Any] | None:
    if isinstance(value, (list, tuple)):
        return list(value)
    if isinstance(value, dict) and value.get("type") in {"tuple", "list"}:
        items = value.get("items")
        if isinstance(items, list):
            return items
    return None


def _has_graphish_name(name: str) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in ("edge", "edges", "graph", "mst"))


def _has_adjacency_matrix_name(name: str) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in ("adj", "graph", "matrix"))


def _edge_dicts(edge_set: set[tuple[str, str]]) -> list[dict[str, str]]:
    return [{"from": source, "to": target} for source, target in sorted(edge_set)]


def _deduplicate_edges(edges: list[dict[str, str]]) -> list[dict[str, str]]:
    deduplicated: list[dict[str, str]] = []
    seen: set[tuple[str, str, str | None]] = set()
    for edge in edges:
        key = (edge["from"], edge["to"], edge.get("label"))
        if key in seen:
            continue
        deduplicated.append(edge)
        seen.add(key)
    return deduplicated


def _build_graph_payload(
    *,
    node_ids: set[str],
    edges: list[dict[str, Any]],
) -> dict[str, Any]:
    nodes = [{"id": node_id, "label": node_id} for node_id in sorted(node_ids)]
    return {"nodes": nodes, "edges": edges}


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
