from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_index_pointers,
    build_scalar_sequence_map,
    build_scalar_badges,
    merge_scope_snapshots,
    resolve_active_indices,
    resolve_matched_indices,
    select_primary_name,
)


class ArrayCellsExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "array-cells"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable = select_primary_name(
            execution,
            extractor=build_scalar_sequence_map,
            size_of=len,
        )
        if source_variable is None:
            return None

        extracted_steps: list[tuple[int, int, list[object], dict[str, object]]] = []
        for step in execution.steps:
            merged_snapshot = merge_scope_snapshots(step.locals_snapshot, step.globals_snapshot)
            sequence_map = build_scalar_sequence_map(merged_snapshot)
            items = sequence_map.get(source_variable)
            if items is None:
                continue
            extracted_steps.append((step.step_index, step.line_number, items, merged_snapshot))

        if not extracted_steps:
            return None

        final_items = extracted_steps[-1][2]
        previous_items: list[object] | None = None
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
                    message=(
                        f"변화한 셀: {', '.join(str(index) for index in active_indices)}"
                        if active_indices
                        else "현재 배열 셀 상태를 표시합니다."
                    ),
                )
            )
            previous_items = items

        return ExecutionVisualizationRead(
            kind="array-cells",
            source_variable=source_variable,
            step_states=step_states,
            metadata={"length": len(final_items)},
        )
