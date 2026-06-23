from collections.abc import Callable
from typing import Any

from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_index_pointers,
    build_scalar_badges,
    build_scalar_sequence_map,
    build_scalar_value_map,
    merge_scope_snapshots,
    resolve_active_indices,
    resolve_matched_indices,
    select_primary_name,
)


SnapshotExtractor = Callable[[dict[str, Any]], dict[str, list[Any]]]


class ArrayCellsExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "array-cells"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable, extractor, is_scalar_value_track = self._select_source(execution)
        if source_variable is None:
            return None

        extracted_steps: list[tuple[int, int, list[Any], dict[str, Any]]] = []
        for step in execution.steps:
            merged_snapshot = merge_scope_snapshots(step.locals_snapshot, step.globals_snapshot)
            sequence_map = extractor(merged_snapshot)
            items = sequence_map.get(source_variable)
            if items is None:
                continue
            extracted_steps.append((step.step_index, step.line_number, items, merged_snapshot))

        if not extracted_steps:
            return None

        final_items = extracted_steps[-1][2]
        previous_items: list[Any] | None = None
        step_states: list[ExecutionVisualizationStepRead] = []
        for step_index, line_number, items, locals_snapshot in extracted_steps:
            active_indices = resolve_active_indices(previous_items, items)
            matched_indices = resolve_matched_indices(items, final_items)
            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step_index,
                    line_number=line_number,
                    active_indices=active_indices,
                    matched_indices=matched_indices,
                    payload={
                        "items": items,
                        "activeIndices": active_indices,
                        "matchedIndices": matched_indices,
                        "indexPointers": build_index_pointers(
                            locals_snapshot,
                            length=len(items),
                            exclude_names={source_variable},
                        ),
                        "scalarBadges": build_scalar_badges(
                            locals_snapshot,
                            exclude_names={source_variable},
                        ),
                    },
                    message=self._build_message(
                        source_variable=source_variable,
                        items=items,
                        active_indices=active_indices,
                        is_scalar_value_track=is_scalar_value_track,
                    ),
                )
            )
            previous_items = items

        return ExecutionVisualizationRead(
            kind="array-cells",
            source_variable=source_variable,
            step_states=step_states,
            metadata={
                "length": len(final_items),
                "scalarValueTrack": is_scalar_value_track,
            },
        )

    def _select_source(
        self,
        execution: ExecutionRead,
    ) -> tuple[str | None, SnapshotExtractor, bool]:
        source_variable = select_primary_name(
            execution,
            extractor=build_scalar_sequence_map,
            size_of=len,
        )
        if source_variable is not None:
            return source_variable, build_scalar_sequence_map, False

        source_variable = select_primary_name(
            execution,
            extractor=build_scalar_value_map,
            size_of=len,
        )
        return source_variable, build_scalar_value_map, source_variable is not None

    def _build_message(
        self,
        *,
        source_variable: str,
        items: list[Any],
        active_indices: list[int],
        is_scalar_value_track: bool,
    ) -> str:
        if is_scalar_value_track:
            return f"{source_variable} = {items[0]}"
        if active_indices:
            return f"변경된 셀: {', '.join(str(index) for index in active_indices)}"
        return "현재 셀 상태를 표시합니다."
