from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_graph_map,
    resolve_focus_node_ids,
    select_primary_name,
)


class GraphNodeEdgeExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "graph-node-edge"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable = select_primary_name(
            execution,
            extractor=build_graph_map,
            size_of=lambda graph: len(graph["edges"]),
        )
        if source_variable is None:
            return None

        step_states: list[ExecutionVisualizationStepRead] = []
        final_graph = None
        previous_node_ids: list[str] | None = None
        previous_edge_keys: list[str] | None = None

        for step in execution.steps:
            graph_map = build_graph_map(step.locals_snapshot)
            graph = graph_map.get(source_variable)
            if graph is None:
                continue
            node_ids = [node["id"] for node in graph["nodes"]]
            edge_keys = [f"{edge['from']}->{edge['to']}" for edge in graph["edges"]]
            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    payload={
                        "nodes": graph["nodes"],
                        "edges": graph["edges"],
                        "activeNodeIds": (
                            [node_id for node_id in node_ids if node_id not in previous_node_ids]
                            if previous_node_ids is not None
                            else []
                        ),
                        "activeEdgeIds": (
                            [edge_key for edge_key in edge_keys if edge_key not in previous_edge_keys]
                            if previous_edge_keys is not None
                            else []
                        ),
                        "focusNodeIds": resolve_focus_node_ids(
                            step.locals_snapshot,
                            graph["nodes"],
                            exclude_names={source_variable},
                        ),
                        "isolatedNodeIds": [
                            node["id"]
                            for node in graph["nodes"]
                            if not any(
                                edge["from"] == node["id"] or edge["to"] == node["id"]
                                for edge in graph["edges"]
                            )
                        ],
                    },
                    message="그래프 노드와 연결 관계를 표시합니다.",
                )
            )
            previous_node_ids = node_ids
            previous_edge_keys = edge_keys
            final_graph = graph

        if not step_states or final_graph is None:
            return None

        return ExecutionVisualizationRead(
            kind="graph-node-edge",
            source_variable=source_variable,
            step_states=step_states,
            metadata={
                "nodeCount": len(final_graph["nodes"]),
                "edgeCount": len(final_graph["edges"]),
                "isolatedNodeCount": sum(
                    1
                    for node in final_graph["nodes"]
                    if not any(
                        edge["from"] == node["id"] or edge["to"] == node["id"]
                        for edge in final_graph["edges"]
                    )
                ),
            },
        )
