import pytest

from app.modules.executions.domain.trace import TraceExecutionResult
from app.modules.executions.application.services.execution_service import ExecutionService
from app.modules.executions.infrastructure.runners.languages.c.c_trace_runner import (
    detect_global_names,
)
from app.modules.executions.infrastructure.runners.languages.java.java_execute_runner import (
    detect_candidate_lines as detect_java_candidate_lines,
    detect_java_variable_names,
    should_skip_trace_for_consistency,
)
from app.modules.executions.selection.providers.manual_selector import ManualVisualizationSelector
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)
from app.modules.executions.selection.shared.code_analysis import analyze_source_code
from app.modules.executions.selection.shared.trace_analysis import (
    suggest_visualization_mode_from_trace,
)
from app.modules.executions.shared.language_detection import (
    detect_source_language,
    get_language_mismatch_message,
)
from app.modules.executions.visualizations.shared.call_stack import build_call_stack_visualization
from app.modules.executions.visualizations.shared.structure_extractors import (
    build_graph_map,
    build_scalar_badges,
    build_scalar_sequence_map,
)
from app.modules.executions.presentation.http.schemas import (
    ExecutionCreate,
    ExecutionFrameRead,
    ExecutionRead,
    ExecutionStepRead,
)


pytestmark = pytest.mark.no_db


def test_language_detection_identifies_clear_source_language_mismatches():
    java_source = "public class Main { public static void main(String[] args) { System.out.println(1); } }"
    c_source = "#include <stdio.h>\nint main(void) { printf(\"hi\\n\"); return 0; }"
    python_source = "def solve(value):\n    return value + 1\n"

    assert detect_source_language(java_source) == "java"
    assert detect_source_language(c_source) == "c"
    assert detect_source_language(python_source) == "python"

    message = get_language_mismatch_message(
        selected_language="python",
        source_code=java_source,
    )

    assert message is not None
    assert "선택한 언어는 Python" in message
    assert "Java 코드로 보입니다" in message


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
                    "globals_snapshot": {"numbers": [1, 2, 3]},
                    "stdout_snapshot": "",
                    "call_stack": [
                        {
                            "function_name": "main",
                            "line_number": 1,
                            "locals_snapshot": {"value": 1},
                        }
                    ],
                    "metadata": {"callStackDepth": 1},
                },
                {
                    "line_number": 2,
                    "event_type": "line",
                    "function_name": "main",
                    "locals_snapshot": {"value": 3},
                    "globals_snapshot": {"numbers": [1, 3, 2]},
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
    assert result.steps[0].globals_snapshot == {"numbers": [1, 2, 3]}
    assert result.steps[0].call_stack[0].function_name == "main"
    assert result.steps[0].metadata["callStackDepth"] == 1
    assert result.steps[0].merged_snapshot["numbers"] == [1, 2, 3]


def test_unavailable_c_trace_values_are_not_visualization_candidates():
    snapshot = {
        "low": "<optimized out>",
        "high": 4,
        "values": [1, "<optimized out>", 3],
    }

    assert build_scalar_badges(snapshot) == [{"name": "high", "value": 4}]
    assert build_scalar_sequence_map(snapshot) == {}


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


def test_manual_selector_auto_detects_array_bars_for_java_sort_like_code():
    selector = ManualVisualizationSelector(
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
        default_mode="none",
    )

    selection = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            language="java",
            source_code=(
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        int[] arr = {5, 2, 4, 1};\n"
                "        for (int i = 1; i < arr.length; i++) {\n"
                "            int key = arr[i];\n"
                "            int j = i - 1;\n"
                "            while (j >= 0 && arr[j] > key) {\n"
                "                arr[j + 1] = arr[j];\n"
                "                j--;\n"
                "            }\n"
                "            arr[j + 1] = key;\n"
                "        }\n"
                "        System.out.println(arr[0]);\n"
                "    }\n"
                "}\n"
            ),
        )
    )

    assert selection.selected_mode == "array-bars"


def test_java_static_analysis_ignores_main_args_and_scalar_variables():
    analysis = analyze_source_code(
        language="java",
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
        source_code=(
            "public class Main { "
            "public static void main(String[] args) { "
            "int a = 2; int b = 4; System.out.println(a + b); "
            "} }"
        ),
    )

    assert analysis.suggested_mode is None
    assert "array" not in analysis.detected_structures


def test_manual_selector_auto_detects_call_stack_for_one_line_java_methods():
    selector = ManualVisualizationSelector(
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
        default_mode="none",
    )

    selection = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            language="java",
            source_code=(
                "public class Main { "
                "static int add(int a, int b) { return a + b; } "
                "public static void main(String[] args) { System.out.println(add(1, 2)); } "
                "}"
            ),
        )
    )

    assert selection.selected_mode == "call-stack"


def test_c_trace_global_detection_handles_nested_initializers():
    source_code = "\n".join(
        [
            "#include <stdio.h>",
            "#define N 2",
            "int matrix[N + 1][N + 1] = {{0, 0, 0}, {0, 1, 2}, {0, 3, 4}};",
            "int queue[4], front = 0, rear = 0;",
            "int main(void) {",
            "    return matrix[1][1];",
            "}",
        ]
    )

    assert detect_global_names(source_code) == ["matrix", "queue", "front", "rear"]


def test_trace_analysis_prefers_runtime_array_state_for_numeric_lists():
    result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {"line_number": 1, "locals_snapshot": {"numbers": [3, 1, 2]}},
                {"line_number": 2, "locals_snapshot": {"numbers": [1, 3, 2]}},
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "array-bars", "array-cells"},
    )

    assert mode == "array-bars"


def test_trace_analysis_prefers_array_bars_over_non_recursive_java_helper_stack():
    result = TraceExecutionResult.from_payload(
        language="java",
        payload={
            "status": "completed",
            "stdout": "1 2 3 4 5 ",
            "stderr": "",
            "steps": [
                {
                    "line_number": 17,
                    "function_name": "insertionSort",
                    "locals_snapshot": {"arr": [5, 4, 1, 3, 2], "i": 1, "key": 4, "j": 0},
                    "call_stack": [
                        {"function_name": "main", "line_number": 8},
                        {"function_name": "insertionSort", "line_number": 17},
                    ],
                },
                {
                    "line_number": 21,
                    "function_name": "insertionSort",
                    "locals_snapshot": {"arr": [4, 5, 1, 3, 2], "i": 1, "key": 4, "j": -1},
                    "call_stack": [
                        {"function_name": "main", "line_number": 8},
                        {"function_name": "insertionSort", "line_number": 21},
                    ],
                },
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "array-bars", "array-cells", "call-stack"},
    )

    assert mode == "array-bars"


def test_trace_analysis_detects_scalar_value_changes_as_array_cells():
    result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "14\n",
            "stderr": "",
            "steps": [
                {"line_number": 1, "locals_snapshot": {"value": 2}},
                {"line_number": 2, "locals_snapshot": {"value": 7}},
                {"line_number": 3, "locals_snapshot": {"value": 14}},
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "array-cells"},
    )

    assert mode == "array-cells"


def test_trace_analysis_detects_dp_table_from_floyd_matrix_trace():
    result = TraceExecutionResult.from_payload(
        language="c",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 10,
                    "function_name": "FloydWarshall",
                    "globals_snapshot": {
                        "ArrayFY": [
                            [0, 0, 0],
                            [0, 0, 1],
                            [0, 1, 0],
                        ],
                    },
                }
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "dp-table", "graph-node-edge"},
    )

    assert mode == "dp-table"


def test_trace_analysis_detects_graph_traversal_from_trace_names():
    result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 3,
                    "locals_snapshot": {
                        "graph": {1: [2, 3], 2: [4]},
                        "queue": [1, 2],
                        "visited": [True, False, False],
                    },
                }
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "graph-bfs-traversal", "graph-node-edge"},
    )

    assert mode == "graph-bfs-traversal"


def test_manual_selector_prioritizes_trace_tree_over_flowchart():
    selector = ManualVisualizationSelector(
        supported_modes={"none", "flowchart", "hybrid", "tree-binary"},
        default_mode="none",
    )
    result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "True\n",
            "stderr": "",
            "steps": [
                {
                    "line_number": 9,
                    "locals_snapshot": {
                        "tree": {
                            "value": 8,
                            "left": {"value": 3, "left": None, "right": None},
                            "right": {"value": 10, "left": None, "right": None},
                        },
                        "target": 10,
                        "node": {"value": 8, "left": None, "right": None},
                    },
                }
            ],
        },
    )

    selection = selector.select(
        VisualizationSelectionContext(
            requested_mode="auto",
            language="python",
            source_code=(
                "tree = {'value': 8, 'left': None, 'right': None}\n"
                "target = 10\n"
                "node = tree\n"
                "while node is not None:\n"
                "    if node['value'] == target:\n"
                "        break\n"
            ),
            trace_result=result,
        )
    )

    assert selection.selected_mode == "tree-binary"


def test_graph_map_supports_weighted_edge_lists_from_python_trace():
    graph_map = build_graph_map(
        {
            "edges": [
                {"type": "tuple", "items": [1, 1, 2]},
                {"type": "tuple", "items": [2, 2, 3]},
                {"type": "tuple", "items": [3, 1, 3]},
            ]
        }
    )

    graph = graph_map["edges"]

    assert {node["id"] for node in graph["nodes"]} == {"1", "2", "3"}
    assert graph["edges"][:2] == [
        {"from": "1", "to": "2", "label": "1"},
        {"from": "2", "to": "3", "label": "2"},
    ]
    assert {"from": "1", "to": "3", "label": "3"} in graph["edges"]


def test_graph_map_supports_edge_matrices_from_java_trace():
    graph_map = build_graph_map({"edges": [[1, 2], [1, 3], [2, 4], [3, 5]]})

    graph = graph_map["edges"]

    assert {node["id"] for node in graph["nodes"]} == {"1", "2", "3", "4", "5"}
    assert {"from": "1", "to": "2"} in graph["edges"]
    assert {"from": "3", "to": "5"} in graph["edges"]


def test_graph_map_supports_adjacency_matrices_from_c_trace():
    graph_map = build_graph_map(
        {
            "graph": [
                [0, 1, 1],
                [0, 0, 1],
                [0, 0, 0],
            ]
        }
    )

    graph = graph_map["graph"]

    assert {node["id"] for node in graph["nodes"]} == {"0", "1", "2"}
    assert graph["edges"] == [
        {"from": "0", "to": "1"},
        {"from": "0", "to": "2"},
        {"from": "1", "to": "2"},
    ]


def test_graph_map_supports_weighted_adjacency_lists():
    graph_map = build_graph_map(
        {
            "graph": {
                1: [{"type": "tuple", "items": [2, 2]}, {"type": "tuple", "items": [3, 5]}],
                2: [{"type": "tuple", "items": [3, 1]}],
                3: [],
            }
        }
    )

    graph = graph_map["graph"]

    assert {"from": "1", "to": "2", "label": "2"} in graph["edges"]
    assert {"from": "1", "to": "3", "label": "5"} in graph["edges"]
    assert {"from": "2", "to": "3", "label": "1"} in graph["edges"]


def test_graph_map_supports_weight_first_adjacency_lists():
    graph_map = build_graph_map(
        {
            "graph": {
                1: [{"type": "tuple", "items": [1, 2]}, {"type": "tuple", "items": [3, 3]}],
                2: [{"type": "tuple", "items": [1, 1]}, {"type": "tuple", "items": [2, 3]}],
                3: [{"type": "tuple", "items": [3, 1]}, {"type": "tuple", "items": [2, 2]}],
            }
        }
    )

    graph = graph_map["graph"]

    assert {"from": "1", "to": "2", "label": "1"} in graph["edges"]
    assert {"from": "3", "to": "1", "label": "3"} in graph["edges"]


def test_trace_analysis_does_not_treat_visited_only_as_graph():
    result = TraceExecutionResult.from_payload(
        language="python",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 3,
                    "locals_snapshot": {
                        "visited": [True, False, False],
                        "current": 0,
                    },
                }
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "graph-node-edge"},
    )

    assert mode is None


def test_trace_analysis_ignores_invalid_call_stack_depth_metadata():
    result = TraceExecutionResult.from_payload(
        language="java",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 3,
                    "function_name": "main",
                    "metadata": {"callStackDepth": "unknown"},
                }
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "call-stack"},
    )

    assert mode is None


def test_trace_analysis_detects_call_stack_depth_from_trace():
    result = TraceExecutionResult.from_payload(
        language="java",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 8,
                    "function_name": "factorial",
                    "call_stack": [
                        {"function_name": "main", "line_number": 3},
                        {"function_name": "factorial", "line_number": 8},
                    ],
                }
            ],
        },
    )

    mode = suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "call-stack"},
    )

    assert mode == "call-stack"


def test_execution_service_passes_trace_result_to_selector_for_auto_trace():
    class Repository:
        def save_execution(self, **kwargs):
            result = kwargs["result"]
            return ExecutionRead(
                run_id="run-1",
                language=kwargs["language"],
                visualization_mode=kwargs["visualization_mode"],
                status=result.status,
                source_code=kwargs["source_code"],
                stdin=kwargs["stdin"],
                stdout=result.stdout,
                stderr=result.stderr,
                error_message=result.error_message,
                step_count=len(result.steps),
                created_at="2026-05-30T00:00:00Z",
                steps=[],
            )

    class Runner:
        def run(self, command):
            return TraceExecutionResult.from_payload(
                language=command.language,
                payload={
                    "status": "completed",
                    "stdout": "Hello, World!\n",
                    "stderr": "",
                    "steps": [
                        {
                            "line_number": 1,
                            "function_name": "<module>",
                            "locals_snapshot": {},
                            "globals_snapshot": {},
                            "stdout_snapshot": "Hello, World!\n",
                        }
                    ],
                },
            )

    class Visualizer:
        supported_modes = {"none", "array-bars", "call-stack"}

        def build(self, execution):
            return None

    class Selector:
        def select(self, context):
            assert context.requested_mode == "auto"
            assert context.trace_result is not None
            assert context.trace_result.stdout == "Hello, World!\n"
            assert len(context.trace_result.steps) == 1
            return VisualizationSelectionResult(
                selected_mode="none",
                reason="trace를 선택기에 전달했습니다.",
                confidence=0.7,
                summary="간단한 출력 trace입니다.",
                observations=["총 1개의 trace step이 생성되었습니다."],
            )

    service = ExecutionService(
        repository=Repository(),
        runner=Runner(),
        visualizer=Visualizer(),
        selection_service=Selector(),
    )

    execution = service.create_execution(
        ExecutionCreate(
            language="python",
            source_code='print("Hello, World!")',
            stdin="",
            visualizationMode="auto",
        ),
        user_id="user-1",
    )

    assert execution.visualization_mode == "none"
    assert execution.stdout == "Hello, World!\n"
    assert execution.analysis is not None
    assert execution.analysis.summary == "간단한 출력 trace입니다."


def test_java_trace_helpers_detect_statement_lines_and_variables():
    source_code = (
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        int[] numbers = {3, 1, 2};\n"
        "        int value = numbers[0];\n"
        "        System.out.println(value);\n"
        "    }\n"
        "}\n"
    )

    assert detect_java_candidate_lines(source_code) == [3, 4, 5]
    assert detect_java_variable_names(source_code) == ({"numbers"}, {"value"})


def test_java_trace_helpers_detect_nondeterministic_code():
    assert should_skip_trace_for_consistency(
        "import java.util.*; public class Main { public static void main(String[] args) { "
        "System.out.println(Math.random()); } }"
    )
    assert not should_skip_trace_for_consistency(
        "public class Main { public static void main(String[] args) { System.out.println(1); } }"
    )


def test_trace_node_local_does_not_force_tree_visualization():
    result = TraceExecutionResult.from_payload(
        language="java",
        payload={
            "status": "completed",
            "stdout": "",
            "stderr": "",
            "steps": [
                {
                    "line_number": 31,
                    "function_name": "BFS",
                    "locals_snapshot": {"start": 1, "now": 1, "node": 2},
                    "globals_snapshot": {},
                    "stdout_snapshot": "",
                    "call_stack": [
                        {"function_name": "main", "line_number": 20},
                        {"function_name": "BFS", "line_number": 31},
                    ],
                }
            ],
        },
    )

    assert suggest_visualization_mode_from_trace(
        result=result,
        supported_modes={"none", "tree-binary", "call-stack"},
    ) == "call-stack"


def test_call_stack_visualization_allows_single_function_recursion_stack():
    execution = ExecutionRead(
        run_id="run-1",
        language="python",
        visualization_mode="call-stack",
        status="completed",
        source_code="",
        stdin="",
        stdout="",
        stderr="",
        step_count=1,
        created_at="2026-05-30T00:00:00Z",
        steps=[
            ExecutionStepRead(
                step_index=1,
                line_number=2,
                event_type="line",
                function_name="factorial",
                locals_snapshot={},
                stdout_snapshot="",
                call_stack=[
                    ExecutionFrameRead(function_name="factorial", line_number=1),
                    ExecutionFrameRead(function_name="factorial", line_number=2),
                ],
            )
        ],
    )

    visualization = build_call_stack_visualization(execution)

    assert visualization is not None
    assert visualization.step_states[0].payload["frameCount"] == 2


def test_graph_map_includes_neighbor_only_nodes():
    graph_map = build_graph_map({"graph": {1: [2], 2: [3]}})

    assert {node["id"] for node in graph_map["graph"]["nodes"]} == {"1", "2", "3"}
