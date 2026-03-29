from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_index_pointers,
    build_numeric_sequence_map,
    build_scalar_badges,
    resolve_active_indices,
    resolve_matched_indices,
    select_primary_name,
)


def build_array_visualization(execution: ExecutionRead) -> ExecutionVisualizationRead | None:
    primary_sequence_name = select_primary_name(
        execution,
        extractor=build_numeric_sequence_map,
        size_of=len,
    )
    if primary_sequence_name is None:
        return None

    extracted_steps: list[tuple[int, int, list[int | float], dict[str, object]]] = []

    for step in execution.steps:
        sequence_map = build_numeric_sequence_map(step.locals_snapshot)
        values = sequence_map.get(primary_sequence_name)
        if values is None:
            continue
        extracted_steps.append((step.step_index, step.line_number, values, step.locals_snapshot))

    if not extracted_steps:
        return None

    final_values = extracted_steps[-1][2]
    sequence_changed = any(
        previous_step[2] != current_step[2]
        for previous_step, current_step in zip(extracted_steps, extracted_steps[1:])
    )
    previous_values: list[int | float] | None = None
    step_states: list[ExecutionVisualizationStepRead] = []

    for step_index, line_number, values, locals_snapshot in extracted_steps:
        active_indices = resolve_active_indices(previous_values, values)
        matched_indices = resolve_matched_indices(values, final_values) if sequence_changed else []
        index_pointers = build_index_pointers(
            locals_snapshot,
            length=len(values),
            exclude_names={primary_sequence_name},
        )
        scalar_badges = build_scalar_badges(
            locals_snapshot,
            exclude_names={primary_sequence_name},
        )
        step_states.append(
            ExecutionVisualizationStepRead(
                step_index=step_index,
                line_number=line_number,
                values=values,
                active_indices=active_indices,
                matched_indices=matched_indices,
                payload={
                    "values": values,
                    "activeIndices": active_indices,
                    "matchedIndices": matched_indices,
                    "indexPointers": index_pointers,
                    "scalarBadges": scalar_badges,
                },
                message=(
                    f"변화한 인덱스: {', '.join(str(index) for index in active_indices)}"
                    if active_indices
                    else "현재 배열 상태를 표시합니다."
                ),
            )
        )
        previous_values = values

    return ExecutionVisualizationRead(
        kind="array-bars",
        source_variable=primary_sequence_name,
        step_states=step_states,
        metadata={"length": len(final_values)},
    )
