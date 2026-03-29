from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_scalar_sequence_map,
    build_scalar_badges,
    merge_scope_snapshots,
    resolve_active_indices,
    select_primary_name,
)


class QueueHorizontalExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "queue-horizontal"

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
            merged_snapshot = merge_scope_snapshots(step.locals_snapshot, step.globals_snapshot)
            sequence_map = build_scalar_sequence_map(merged_snapshot)
            items = sequence_map.get(source_variable)
            if items is None:
                continue

            active_indices = resolve_active_indices(previous_items, items)
            operation = "peek"
            if previous_items is not None:
                if len(items) > len(previous_items):
                    operation = "enqueue"
                elif len(items) < len(previous_items):
                    operation = "dequeue"
                elif active_indices:
                    operation = "update"
            enqueued_value = items[-1] if operation == "enqueue" and items else None
            dequeued_value = previous_items[0] if operation == "dequeue" and previous_items else None

            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step.step_index,
                    line_number=step.line_number,
                    active_indices=active_indices,
                    payload={
                        "items": items,
                        "frontIndex": 0 if items else None,
                        "rearIndex": len(items) - 1 if items else None,
                        "frontValue": items[0] if items else None,
                        "rearValue": items[-1] if items else None,
                        "size": len(items),
                        "activeIndices": active_indices,
                        "operation": operation,
                        "enqueuedValue": enqueued_value,
                        "dequeuedValue": dequeued_value,
                        "scalarBadges": build_scalar_badges(
                            merged_snapshot,
                            exclude_names={source_variable},
                        ),
                    },
                    message=(
                        f"큐 {operation} 상태를 표시합니다."
                        if operation != "peek"
                        else "현재 큐 front / rear 상태를 표시합니다."
                    ),
                )
            )
            previous_items = items

        if not step_states:
            return None

        final_items = step_states[-1].payload["items"]
        return ExecutionVisualizationRead(
            kind="queue-horizontal",
            source_variable=source_variable,
            step_states=step_states,
            metadata={
                "size": len(final_items),
                "frontValue": final_items[0] if final_items else None,
                "rearValue": final_items[-1] if final_items else None,
            },
        )
