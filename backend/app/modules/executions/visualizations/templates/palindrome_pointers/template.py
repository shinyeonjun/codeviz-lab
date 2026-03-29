from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_character_sequence_map,
    build_index_pointers,
    merge_scope_snapshots,
    build_scalar_badges,
    select_primary_name,
)


def resolve_matched_indices(length: int, left_index: int | None, right_index: int | None) -> list[int]:
    if length <= 0:
        return []

    if left_index is None or right_index is None:
        return []

    matched = [index for index in range(length) if index < left_index or index > right_index]

    if left_index == right_index and 0 <= left_index < length:
        matched.append(left_index)

    return sorted(set(matched))


def build_status_message(
    *,
    left_index: int | None,
    right_index: int | None,
    comparison_result: bool | None,
) -> str:
    if left_index is None or right_index is None:
        return "양끝 포인터가 준비되면 비교를 시작합니다."

    if left_index > right_index:
        return "가운데를 지나 비교가 끝났습니다."

    if left_index == right_index:
        return "가운데 문자만 남아 팰린드롬 판별이 마무리됩니다."

    if comparison_result is False:
        return f"{left_index}와 {right_index} 위치 문자가 달라서 팰린드롬이 아닙니다."

    return f"{left_index}와 {right_index} 위치 문자를 비교하고 있습니다."


class PalindromePointersExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "palindrome-pointers"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable = select_primary_name(
            execution,
            extractor=build_character_sequence_map,
            size_of=len,
        )
        if source_variable is None:
            return None

        extracted_steps: list[tuple[int, int, list[str], dict[str, object]]] = []
        for step in execution.steps:
            merged_snapshot = merge_scope_snapshots(step.locals_snapshot, step.globals_snapshot)
            sequence_map = build_character_sequence_map(merged_snapshot)
            items = sequence_map.get(source_variable)
            if items is None:
                continue
            extracted_steps.append((step.step_index, step.line_number, items, merged_snapshot))

        if not extracted_steps:
            return None

        step_states: list[ExecutionVisualizationStepRead] = []
        for step_index, line_number, items, locals_snapshot in extracted_steps:
            left_index = locals_snapshot.get("left")
            right_index = locals_snapshot.get("right")

            normalized_left = left_index if isinstance(left_index, int) and 0 <= left_index < len(items) else None
            normalized_right = (
                right_index if isinstance(right_index, int) and 0 <= right_index < len(items) else None
            )

            active_indices = [
                index
                for index in [normalized_left, normalized_right]
                if index is not None
            ]
            active_indices = sorted(set(active_indices))

            comparison_result: bool | None = None
            if (
                normalized_left is not None
                and normalized_right is not None
                and normalized_left <= normalized_right
            ):
                comparison_result = items[normalized_left] == items[normalized_right]

            matched_indices = resolve_matched_indices(
                len(items),
                normalized_left,
                normalized_right,
            )

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
                        "leftIndex": normalized_left,
                        "rightIndex": normalized_right,
                        "comparisonResult": comparison_result,
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
                    message=build_status_message(
                        left_index=normalized_left,
                        right_index=normalized_right,
                        comparison_result=comparison_result,
                    ),
                )
            )

        return ExecutionVisualizationRead(
            kind="palindrome-pointers",
            source_variable=source_variable,
            step_states=step_states,
            metadata={"length": len(extracted_steps[-1][2]), "displayMode": "string-cells"},
        )
