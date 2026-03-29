from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_scalar_sequence_map,
    build_scalar_badges,
    resolve_active_indices,
    select_primary_name,
)


class StackVerticalExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "stack-vertical"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable = select_primary_name(
            execution,
            extractor=build_scalar_sequence_map,
            size_of=len,
        )
        if source_variable is None:
            return None

        previous_items: list[object] | None = None
        step_states: list[ExecutionVisualizationStepRead] = []

        for step in execution.steps:
            sequence_map = build_scalar_sequence_map(step.locals_snapshot)
            items = sequence_map.get(source_variable)
            if items is None:
                continue

            active_indices = resolve_active_indices(previous_items, items)
            operation = "peek"
            if previous_items is not None:
                if len(items) > len(previous_items):
                    operation = "push"
                elif len(items) < len(previous_items):
                    operation = "pop"
                elif active_indices:
                    operation = "update"
            pushed_value = items[-1] if operation == "push" and items else None
            popped_value = previous_items[-1] if operation == "pop" and previous_items else None

            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    active_indices=active_indices,
                    payload={
                        "items": items,
                        "topIndex": len(items) - 1 if items else None,
                        "topValue": items[-1] if items else None,
                        "size": len(items),
                        "activeIndices": active_indices,
                        "operation": operation,
                        "pushedValue": pushed_value,
                        "poppedValue": popped_value,
                        "scalarBadges": build_scalar_badges(
                            step.locals_snapshot,
                            exclude_names={source_variable},
                        ),
                    },
                    message=(
                        f"스택 {operation} 상태를 표시합니다."
                        if operation != "peek"
                        else "현재 스택 top 상태를 표시합니다."
                    ),
                )
            )
            previous_items = items

        if not step_states:
            return None

        final_items = step_states[-1].payload["items"]
        return ExecutionVisualizationRead(
            kind="stack-vertical",
            source_variable=source_variable,
            step_states=step_states,
            metadata={"size": len(final_items), "topValue": final_items[-1] if final_items else None},
        )
