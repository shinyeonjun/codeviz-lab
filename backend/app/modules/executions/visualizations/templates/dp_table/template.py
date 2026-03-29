from app.modules.executions.presentation.http.schemas import (
    ExecutionRead,
    ExecutionVisualizationRead,
    ExecutionVisualizationStepRead,
)
from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_numeric_matrix_map,
    build_scalar_badges,
    resolve_active_cells,
    resolve_matched_cells,
    select_primary_name,
)


class DpTableExecutionTemplate(ExecutionVisualizationTemplate):
    visualization_mode = "dp-table"

    def build(self, execution: ExecutionRead) -> ExecutionVisualizationRead | None:
        source_variable = select_primary_name(
            execution,
            extractor=build_numeric_matrix_map,
            size_of=lambda matrix: len(matrix) * max((len(row) for row in matrix), default=0),
        )
        if source_variable is None:
            return None

        extracted_steps: list[tuple[int, int, list[list[int | float]], dict[str, object]]] = []
        for step in execution.steps:
            matrix_map = build_numeric_matrix_map(step.locals_snapshot)
            matrix = matrix_map.get(source_variable)
            if matrix is None:
                continue
            extracted_steps.append((step.step_index, step.line_number, matrix, step.locals_snapshot))

        if not extracted_steps:
            return None

        final_matrix = extracted_steps[-1][2]
        previous_matrix: list[list[int | float]] | None = None
        step_states: list[ExecutionVisualizationStepRead] = []
        for step_index, line_number, matrix, locals_snapshot in extracted_steps:
            active_cells = resolve_active_cells(previous_matrix, matrix)
            matched_cells = resolve_matched_cells(matrix, final_matrix)
            step_states.append(
                ExecutionVisualizationStepRead(
                    step_index=step_index,
                    line_number=line_number,
                    payload={
                        "matrix": matrix,
                        "activeCells": active_cells,
                        "matchedCells": matched_cells,
                        "rows": len(matrix),
                        "cols": max((len(row) for row in matrix), default=0),
                        "activeCellCount": len(active_cells),
                        "scalarBadges": build_scalar_badges(
                            locals_snapshot,
                            exclude_names={source_variable},
                        ),
                    },
                    message=(
                        "변화한 셀: "
                        + ", ".join(f"({row},{col})" for row, col in active_cells[:4])
                        if active_cells
                        else "현재 DP 테이블 상태를 표시합니다."
                    ),
                )
            )
            previous_matrix = matrix

        return ExecutionVisualizationRead(
            kind="dp-table",
            source_variable=source_variable,
            step_states=step_states,
            metadata={
                "rows": len(final_matrix),
                "cols": max((len(row) for row in final_matrix), default=0),
                "rowHeaders": list(range(len(final_matrix))),
                "colHeaders": list(range(max((len(row) for row in final_matrix), default=0))),
            },
        )
