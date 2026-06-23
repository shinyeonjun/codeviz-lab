from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate


VisualizationBuilder = Callable[[ExecutionRead], ExecutionVisualizationRead | None]


class HybridExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "hybrid"

    def __init__(
        self,
        *,
        flowchart_builder: VisualizationBuilder,
        structure_builders: list[tuple[str, VisualizationBuilder]],
    ) -> None:
        self._flowchart_builder = flowchart_builder
        self._structure_builders = structure_builders

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        flowchart = self._flowchart_builder(execution)
        structure = self._build_structure_visualization(execution)

        if flowchart is None or structure is None:
            return flowchart or structure

        flowchart_states = {state.step_index: state for state in flowchart.step_states}
        structure_states = _index_latest_states(structure.step_states)

        hybrid_states: list[ExecutionVisualizationStepRead] = []
        for step in execution.steps:
            flowchart_state = flowchart_states.get(step.step_index)
            structure_state = _latest_state_at_or_before(structure_states, step.step_index)
            if flowchart_state is None or structure_state is None:
                continue

            hybrid_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    payload={
                        "flowchart": {
                            "kind": flowchart.kind,
                            "sourceVariable": flowchart.source_variable,
                            "state": _serialize_step_state(flowchart_state),
                            "metadata": flowchart.metadata,
                        },
                        "structure": {
                            "kind": structure.kind,
                            "sourceVariable": structure.source_variable,
                            "state": _serialize_step_state(structure_state),
                            "metadata": structure.metadata,
                        },
                    },
                    message=flowchart_state.message or structure_state.message,
                )
            )

        if not hybrid_states:
            return flowchart or structure

        return ExecutionVisualizationRead(
            kind="hybrid",
            source_variable=structure.source_variable,
            step_states=hybrid_states,
            metadata={
                "flowchartKind": flowchart.kind,
                "structureKind": structure.kind,
                "structureSourceVariable": structure.source_variable,
            },
        )

    def _build_structure_visualization(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        for _, builder in self._prioritized_builders(execution):
            visualization = builder(execution)
            if visualization is not None and visualization.step_states:
                return visualization
        return None

    def _prioritized_builders(self, execution: ExecutionRead) -> list[tuple[str, VisualizationBuilder]]:
        source = execution.source_code.lower()
        priority_groups: list[tuple[str, ...]] = []
        if any(hint in source for hint in ("graph", "adj", "neighbor", "visited")):
            priority_groups.append(("graph-node-edge",))
        if any(hint in source for hint in ("tree", "root", "left", "right")):
            priority_groups.append(("tree-binary",))
        if "dp" in source or "matrix" in source:
            priority_groups.append(("dp-table",))
        if any(hint in source for hint in ("queue", "enqueue", "dequeue", "front", "rear", "poll", "offer")):
            priority_groups.append(("queue-horizontal",))
        if any(hint in source for hint in ("stack", "push", "pop", "top")):
            priority_groups.append(("stack-vertical",))

        priority_groups.extend(
            [
                ("palindrome-pointers",),
                ("array-bars", "array-cells"),
                ("stack-vertical",),
                ("queue-horizontal",),
                ("graph-node-edge",),
                ("tree-binary",),
                ("dp-table",),
            ]
        )

        builder_map = dict(self._structure_builders)
        ordered: list[tuple[str, VisualizationBuilder]] = []
        seen: set[str] = set()
        for group in priority_groups:
            for mode in group:
                builder = builder_map.get(mode)
                if builder is None or mode in seen:
                    continue
                ordered.append((mode, builder))
                seen.add(mode)
        for mode, builder in self._structure_builders:
            if mode not in seen:
                ordered.append((mode, builder))
        return ordered


def _index_latest_states(
    states: list[ExecutionVisualizationStepRead],
) -> list[tuple[int, ExecutionVisualizationStepRead]]:
    return sorted((state.step_index, state) for state in states)


def _latest_state_at_or_before(
    indexed_states: list[tuple[int, ExecutionVisualizationStepRead]],
    step_index: int,
) -> ExecutionVisualizationStepRead | None:
    latest: ExecutionVisualizationStepRead | None = None
    for candidate_index, state in indexed_states:
        if candidate_index > step_index:
            break
        latest = state
    return latest or (indexed_states[0][1] if indexed_states else None)


def _serialize_step_state(state: ExecutionVisualizationStepRead) -> dict[str, Any]:
    return {
        "step_index": state.step_index,
        "line_number": state.line_number,
        "values": state.values,
        "activeIndices": state.active_indices,
        "matchedIndices": state.matched_indices,
        "payload": state.payload,
        "message": state.message,
    }
