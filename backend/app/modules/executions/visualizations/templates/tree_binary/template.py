from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_binary_tree_map,
    merge_scope_snapshots,
    resolve_focus_node_ids,
    select_primary_name,
)


class TreeBinaryExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "tree-binary"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable = select_primary_name(
            execution,
            extractor=build_binary_tree_map,
            size_of=lambda tree: len(tree["nodes"]),
        )
        if source_variable is None:
            return None

        step_states: list[ExecutionVisualizationStepRead] = []
        final_tree = None
        previous_node_ids: list[str] | None = None
        previous_edge_keys: list[str] | None = None

        for step in execution.steps:
            merged_snapshot = merge_scope_snapshots(step.locals_snapshot, step.globals_snapshot)
            tree_map = build_binary_tree_map(merged_snapshot)
            tree = tree_map.get(source_variable)
            if tree is None:
                continue
            node_ids = [node["id"] for node in tree["nodes"]]
            edge_keys = [f"{edge['from']}->{edge['to']}" for edge in tree["edges"]]
            active_node_ids = []
            active_edge_ids = []
            if previous_node_ids is not None:
                active_node_ids = [
                    node_id for node_id in node_ids if node_id not in previous_node_ids
                ]
            if previous_edge_keys is not None:
                active_edge_ids = [
                    edge_key for edge_key in edge_keys if edge_key not in previous_edge_keys
                ]
            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    payload={
                        "nodes": tree["nodes"],
                        "edges": tree["edges"],
                        "activeNodeIds": active_node_ids,
                        "activeEdgeIds": active_edge_ids,
                        "focusNodeIds": resolve_focus_node_ids(
                            merged_snapshot,
                            tree["nodes"],
                            exclude_names={source_variable},
                        ),
                        "rootNodeId": tree["nodes"][0]["id"] if tree["nodes"] else None,
                        "depthCount": max((node.get("depth", 0) for node in tree["nodes"]), default=0) + 1,
                        "leafNodeIds": [
                            node["id"]
                            for node in tree["nodes"]
                            if not any(edge["from"] == node["id"] for edge in tree["edges"])
                        ],
                    },
                    message="이진 트리 노드와 간선 관계를 표시합니다.",
                )
            )
            previous_node_ids = node_ids
            previous_edge_keys = edge_keys
            final_tree = tree

        if not step_states or final_tree is None:
            return None

        return ExecutionVisualizationRead(
            kind="tree-binary",
            source_variable=source_variable,
            step_states=step_states,
            metadata={
                "nodeCount": len(final_tree["nodes"]),
                "edgeCount": len(final_tree["edges"]),
                "depthCount": max((node.get("depth", 0) for node in final_tree["nodes"]), default=0) + 1,
                "leafCount": sum(
                    1
                    for node in final_tree["nodes"]
                    if not any(edge["from"] == node["id"] for edge in final_tree["edges"])
                ),
            },
        )
