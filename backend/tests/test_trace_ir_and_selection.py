from app.modules.executions.domain.trace import TraceExecutionResult
from app.modules.executions.selection.providers.manual_selector import ManualVisualizationSelector
from app.modules.executions.selection.base.schemas import VisualizationSelectionContext


def test_trace_execution_result_from_payload_builds_summary():
    result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "3\n",
            "stderr": "",
            "error_message": None,
            "steps": [
                {
                    "line_number": 1,
                    "event_type": "line",
                    "function_name": "main",
                    "locals_snapshot": {"value": 1},
                    "stdout_snapshot": "",
                },
                {
                    "line_number": 2,
                    "event_type": "line",
                    "function_name": "main",
                    "locals_snapshot": {"value": 3},
                    "stdout_snapshot": "3\n",
                },
            ],
        },
    )

    assert result.language == "python"
    assert result.summary is not None
    assert result.summary.total_steps == 2
    assert result.summary.function_names == ["main"]
    assert result.summary.has_stdout is True
    assert result.summary.has_errors is False


def test_manual_selector_auto_detects_array_bars_for_c_sort_like_code():
    selector = ManualVisualizationSelector(
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
        default_mode="none",
    )

    selection = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            language="c",
            source_code=(
                "#include <stdio.h>\n"
                "int main(void) {\n"
                "    int arr[] = {5, 2, 4, 1};\n"
                "    for (int i = 1; i < 4; i++) {\n"
                "        int key = arr[i];\n"
                "        int j = i - 1;\n"
                "        while (j >= 0 && arr[j] > key) {\n"
                "            arr[j + 1] = arr[j];\n"
                "            j--;\n"
                "        }\n"
                "        arr[j + 1] = key;\n"
                "    }\n"
                "    printf(\"%d\\n\", arr[0]);\n"
                "    return 0;\n"
                "}\n"
            ),
        )
    )

    assert selection.selected_mode == "array-bars"


def test_manual_selector_auto_detects_call_stack_for_c_multi_function_code():
    selector = ManualVisualizationSelector(
        supported_modes={"none", "array-bars", "call-stack"},
        default_mode="none",
    )

    selection = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            language="c",
            source_code=(
                "#include <stdio.h>\n"
                "int add(int a, int b) {\n"
                "    return a + b;\n"
                "}\n"
                "int main(void) {\n"
                "    int result = add(2, 3);\n"
                "    printf(\"%d\\n\", result);\n"
                "    return 0;\n"
                "}\n"
            ),
        )
    )

    assert selection.selected_mode == "call-stack"
