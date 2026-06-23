import shutil

import pytest

from app.modules.executions.infrastructure.runners.languages.java.java_execute_runner import (
    find_jdb_executable,
)


def test_create_and_read_execution(authenticated_client):
    source_code = "\n".join(
        [
            "value = 1",
            "value = value + 2",
            "print(value)",
        ]
    )

    create_response = authenticated_client.post(
        "/api/v1/executions",
        json={"language": "python", "source_code": source_code, "stdin": ""},
    )

    assert create_response.status_code == 201

    created_payload = create_response.json()
    assert created_payload["status"] == "success"
    assert created_payload["data"]["visualizationMode"] == "none"
    assert created_payload["data"]["stdout"] == "3\n"
    assert created_payload["data"]["step_count"] >= 2
    assert created_payload["data"]["visualization"] is None

    run_id = created_payload["data"]["run_id"]
    read_response = authenticated_client.get(f"/api/v1/executions/{run_id}")

    assert read_response.status_code == 200
    read_payload = read_response.json()
    assert read_payload["data"]["run_id"] == run_id
    assert len(read_payload["data"]["steps"]) >= 2


def test_create_execution_with_visualization_mode_returns_visualization_payload(authenticated_client):
    source_code = "\n".join(
        [
            "numbers = [5, 2, 4, 6, 1, 3]",
            "",
            "for i in range(1, len(numbers)):",
            "    key = numbers[i]",
            "    j = i - 1",
            "",
            "    while j >= 0 and numbers[j] > key:",
            "        numbers[j + 1] = numbers[j]",
            "        j -= 1",
            "",
            "    numbers[j + 1] = key",
            "",
            "print(numbers)",
        ]
    )

    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": source_code,
            "stdin": "",
            "visualizationMode": "array-bars",
        },
    )

    assert response.status_code == 201

    payload = response.json()["data"]
    assert payload["visualizationMode"] == "array-bars"
    assert payload["visualization"]["kind"] == "array-bars"
    assert payload["visualization"]["sourceVariable"] == "numbers"
    assert len(payload["visualization"]["stepStates"]) >= 1
    assert any(
        len(step_state["values"]) == 6 for step_state in payload["visualization"]["stepStates"]
    )
    assert any(
        "activeIndices" in step_state and "matchedIndices" in step_state
        for step_state in payload["visualization"]["stepStates"]
    )
    assert any(
        step_state["payload"].get("indexPointers")
        for step_state in payload["visualization"]["stepStates"]
    )
    assert any(
        any(pointer["name"] in {"i", "j"} for pointer in step_state["payload"].get("indexPointers", []))
        for step_state in payload["visualization"]["stepStates"]
    )


def test_create_execution_accepts_auto_visualization_mode(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": "numbers = [3, 1, 2]\nnumbers.sort()\nprint(numbers)\n",
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "array-bars"
    assert payload["visualization"]["kind"] == "array-bars"


@pytest.mark.parametrize(
    ("selected_language", "source_code", "expected_detected_label"),
    [
        (
            "python",
            "public class Main { public static void main(String[] args) { System.out.println(1); } }",
            "Java",
        ),
        (
            "java",
            "def solve(value):\n    return value + 1\n",
            "Python",
        ),
        (
            "c",
            "public class Main { public static void main(String[] args) { System.out.println(1); } }",
            "Java",
        ),
    ],
)
def test_create_execution_returns_friendly_message_for_language_mismatch(
    authenticated_client,
    selected_language,
    source_code,
    expected_detected_label,
):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": selected_language,
            "source_code": source_code,
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["status"] == "failed"
    assert payload["step_count"] == 0
    assert f"{expected_detected_label} 코드로 보입니다" in payload["error_message"]
    assert "언어 선택" in payload["error_message"]


def test_create_execution_with_array_bars_handles_user_defined_variable_name(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "custom_payload = [4, 1, 3]\n"
                "custom_payload[0], custom_payload[1] = custom_payload[1], custom_payload[0]\n"
                "custom_payload[1], custom_payload[2] = custom_payload[2], custom_payload[1]\n"
                "print(custom_payload)\n"
            ),
            "stdin": "",
            "visualizationMode": "array-bars",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "array-bars"
    assert payload["visualization"]["kind"] == "array-bars"
    assert payload["visualization"]["sourceVariable"] == "custom_payload"


def test_create_execution_with_array_cells_returns_cell_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "tokens = ['A', 'B', 'C']\n"
                "tokens[1] = 'X'\n"
                "print(tokens)\n"
            ),
            "stdin": "",
            "visualizationMode": "array-cells",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "array-cells"
    assert payload["visualization"]["kind"] == "array-cells"
    assert payload["visualization"]["sourceVariable"] == "tokens"
    assert payload["visualization"]["stepStates"][0]["payload"]["items"] == ["A", "B", "C"]


def test_create_execution_with_scalar_updates_auto_returns_cell_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "value = 2\n"
                "value = value + 5\n"
                "value = value * 2\n"
                "print(value)\n"
            ),
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["stdout"] == "14\n"
    assert payload["visualizationMode"] in {"array-bars", "array-cells"}
    assert payload["visualization"]["kind"] == payload["visualizationMode"]
    assert payload["visualization"]["sourceVariable"] == "value"
    assert payload["visualization"]["stepStates"][-1]["payload"]["items"] == [14]


def test_create_execution_with_flowchart_returns_control_flow_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "total = 0\n"
                "for number in [1, 2, 3]:\n"
                "    total += number\n"
                "if total > 3:\n"
                "    print(total)\n"
            ),
            "stdin": "",
            "visualizationMode": "flowchart",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "flowchart"
    assert payload["visualization"]["kind"] == "flowchart"
    first_state = payload["visualization"]["stepStates"][0]["payload"]
    assert any(node["type"] == "loop" for node in first_state["nodes"])
    assert any(node["type"] == "branch" for node in first_state["nodes"])
    assert any(edge["from"] == "start" for edge in first_state["edges"])
    assert any(edge.get("label") == "YES" for edge in first_state["edges"])
    assert any(edge.get("label") == "NO" for edge in first_state["edges"])
    assert any(edge.get("label") == "반복" for edge in first_state["edges"])


def test_create_execution_auto_prefers_state_visualization_for_basic_if(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "score = 72\n"
                "passed = False\n"
                "if score >= 60:\n"
                "    passed = True\n"
                "print(passed)\n"
            ),
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "array-cells"
    assert payload["visualization"]["kind"] == "array-cells"


def test_create_execution_flowchart_marks_comparison_expression_as_branch(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "value = 3\n"
                "is_big = value > 1\n"
                "print(is_big)\n"
            ),
            "stdin": "",
            "visualizationMode": "flowchart",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    first_state = payload["visualization"]["stepStates"][0]["payload"]
    comparison_node = next(
        node for node in first_state["nodes"] if node.get("lineNumber") == 2
    )
    assert comparison_node["type"] == "branch"


def test_create_execution_auto_prefers_array_visualization_for_array_control_flow(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "numbers = [3, 1, 2]\n"
                "for i in range(len(numbers)):\n"
                "    if numbers[i] > 1:\n"
                "        numbers[i] = numbers[i] * 2\n"
                "print(numbers)\n"
            ),
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "array-bars"
    assert payload["visualization"]["kind"] == "array-bars"


def test_create_execution_with_palindrome_pointers_returns_pointer_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "text = 'level'\n"
                "left = 0\n"
                "right = len(text) - 1\n"
                "while left < right:\n"
                "    if text[left] != text[right]:\n"
                "        break\n"
                "    left += 1\n"
                "    right -= 1\n"
                "print(True)\n"
            ),
            "stdin": "",
            "visualizationMode": "palindrome-pointers",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["visualizationMode"] == "palindrome-pointers"
    assert payload["visualization"]["kind"] == "palindrome-pointers"
    assert payload["visualization"]["sourceVariable"] == "text"
    first_step = payload["visualization"]["stepStates"][0]["payload"]
    assert first_step["items"] == ["l", "e", "v", "e", "l"]
    assert "leftIndex" in first_step
    assert "rightIndex" in first_step


def test_create_execution_with_stack_vertical_returns_stack_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "stack = []\n"
                "stack.append(1)\n"
                "stack.append(2)\n"
                "stack.pop()\n"
                "print(stack)\n"
            ),
            "stdin": "",
            "visualizationMode": "stack-vertical",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]["visualization"]
    assert payload["kind"] == "stack-vertical"
    assert payload["sourceVariable"] == "stack"
    assert any(
        step_state["payload"]["operation"] in {"push", "pop"}
        for step_state in payload["stepStates"]
    )
    assert any("topValue" in step_state["payload"] for step_state in payload["stepStates"])


def test_create_execution_with_queue_horizontal_returns_queue_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "queue = [1]\n"
                "queue.append(2)\n"
                "queue.pop(0)\n"
                "print(queue)\n"
            ),
            "stdin": "",
            "visualizationMode": "queue-horizontal",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]["visualization"]
    assert payload["kind"] == "queue-horizontal"
    assert payload["sourceVariable"] == "queue"
    assert any(
        step_state["payload"]["operation"] in {"enqueue", "dequeue"}
        for step_state in payload["stepStates"]
    )
    assert any("frontValue" in step_state["payload"] for step_state in payload["stepStates"])


def test_create_execution_with_call_stack_returns_frame_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "def add_one(value):\n"
                "    return value + 1\n"
                "\n"
                "def wrap(value):\n"
                "    return add_one(value)\n"
                "\n"
                "result = wrap(1)\n"
                "print(result)\n"
            ),
            "stdin": "",
            "visualizationMode": "call-stack",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]["visualization"]
    assert payload["kind"] == "call-stack"
    assert any(
        len(step_state["payload"]["frames"]) >= 2 for step_state in payload["stepStates"]
    )


def test_create_execution_with_dp_table_returns_matrix_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "dp = [[0, 0, 0], [0, 0, 0]]\n"
                "dp[0][0] = 1\n"
                "dp[0][1] = 1\n"
                "dp[1][1] = 2\n"
                "print(dp)\n"
            ),
            "stdin": "",
            "visualizationMode": "dp-table",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]["visualization"]
    assert payload["kind"] == "dp-table"
    assert payload["sourceVariable"] == "dp"
    assert payload["stepStates"][0]["payload"]["matrix"] == [[0, 0, 0], [0, 0, 0]]
    assert payload["metadata"]["rowHeaders"] == [0, 1]
    assert payload["metadata"]["colHeaders"] == [0, 1, 2]


def test_create_execution_with_tree_binary_returns_tree_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "tree = {\n"
                "    'value': 10,\n"
                "    'left': {'value': 5, 'left': None, 'right': None},\n"
                "    'right': {'value': 15, 'left': None, 'right': None},\n"
                "}\n"
                "print(tree['value'])\n"
            ),
            "stdin": "",
            "visualizationMode": "tree-binary",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]["visualization"]
    assert payload["kind"] == "tree-binary"
    assert payload["sourceVariable"] == "tree"
    assert len(payload["stepStates"][0]["payload"]["nodes"]) >= 3
    assert payload["stepStates"][0]["payload"]["rootNodeId"] == "tree"
    assert payload["metadata"]["leafCount"] >= 2


def test_create_execution_with_graph_node_edge_returns_graph_payload(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "graph = {'A': ['B', 'C'], 'B': ['C'], 'C': []}\n"
                "graph['B'].append('D')\n"
                "graph['D'] = []\n"
                "print(graph)\n"
            ),
            "stdin": "",
            "visualizationMode": "graph-node-edge",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]["visualization"]
    assert payload["kind"] == "graph-node-edge"
    assert payload["sourceVariable"] == "graph"
    assert len(payload["stepStates"][0]["payload"]["edges"]) >= 2
    assert "isolatedNodeIds" in payload["stepStates"][0]["payload"]
    assert "isolatedNodeCount" in payload["metadata"]


def test_read_execution_when_run_id_does_not_exist_returns_404(authenticated_client):
    response = authenticated_client.get("/api/v1/executions/not-found")

    assert response.status_code == 404
    assert "실행 결과를 찾을 수 없습니다" in response.json()["detail"]


def test_create_execution_when_runtime_error_occurs_returns_failed_status(authenticated_client):
    source_code = "\n".join(
        [
            "value = 10",
            "print(value)",
            "result = value / 0",
        ]
    )

    response = authenticated_client.post(
        "/api/v1/executions",
        json={"language": "python", "source_code": source_code, "stdin": ""},
    )

    assert response.status_code == 201

    payload = response.json()["data"]
    assert payload["status"] == "failed"
    assert payload["stdout"] == "10\n"
    assert payload["error_message"] == "division by zero"
    assert any(step["event_type"] == "exception" for step in payload["steps"])


def test_create_execution_when_timeout_occurs_returns_timeout_status(authenticated_client):
    source_code = "\n".join(
        [
            "import time",
            "time.sleep(3)",
            "print('done')",
        ]
    )

    response = authenticated_client.post(
        "/api/v1/executions",
        json={"language": "python", "source_code": source_code, "stdin": ""},
    )

    assert response.status_code == 201

    payload = response.json()["data"]
    assert payload["status"] == "timeout"
    assert payload["error_message"] == "코드 실행 시간이 제한을 초과했습니다."
    assert payload["step_count"] == 0


def test_execution_websocket_returns_snapshot_for_existing_run(authenticated_client):
    create_response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": "value = 1\nprint(value)\n",
            "stdin": "",
        },
    )
    run_id = create_response.json()["data"]["run_id"]

    with authenticated_client.websocket_connect(f"/api/v1/executions/{run_id}/stream") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "execution.snapshot"
    assert payload["data"]["run_id"] == run_id


def test_execution_websocket_returns_not_found_for_missing_run(authenticated_client):
    with authenticated_client.websocket_connect("/api/v1/executions/missing-run/stream") as websocket:
        payload = websocket.receive_json()

    assert payload["type"] == "execution.not_found"
    assert payload["run_id"] == "missing-run"


def test_execution_websocket_requires_login(client):
    try:
        client.websocket_connect("/api/v1/executions/missing-run/stream")
        assert False, "인증 없는 websocket 연결은 실패해야 합니다."
    except Exception:
        assert True


def test_create_execution_when_source_code_is_too_large_returns_422(authenticated_client):
    source_code = "a" * 20001

    response = authenticated_client.post(
        "/api/v1/executions",
        json={"language": "python", "source_code": source_code, "stdin": ""},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "소스 코드 길이가 허용 범위를 초과했습니다."


def test_create_execution_when_stdout_contains_surrogate_returns_sanitized_text(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={"language": "python", "source_code": "print('\\udcbe')", "stdin": ""},
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["status"] == "completed"
    assert "\\udcbe" in payload["stdout"]


def test_create_execution_exposes_global_trace_context_for_python(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "python",
            "source_code": (
                "numbers = [5, 1, 3]\n"
                "\n"
                "def mutate():\n"
                "    global numbers\n"
                "    numbers[0], numbers[1] = numbers[1], numbers[0]\n"
                "\n"
                "mutate()\n"
                "print(numbers)\n"
            ),
            "stdin": "",
            "visualizationMode": "array-bars",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert any("numbers" in step["globals_snapshot"] for step in payload["steps"])
    assert any(step["call_stack"] for step in payload["steps"])
    assert payload["visualization"]["kind"] == "array-bars"


@pytest.mark.skipif(shutil.which("gcc") is None, reason="gcc가 없는 환경에서는 C 실행 테스트를 건너뜁니다.")
def test_create_execution_with_c_code_returns_trace_when_gdb_is_available(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "c",
            "source_code": (
                "#include <stdio.h>\n"
                "\n"
                "int main(void) {\n"
                "    int a = 2;\n"
                "    int b = 4;\n"
                "    printf(\"%d\\n\", a + b);\n"
                "    return 0;\n"
                "}\n"
            ),
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["language"] == "c"
    assert payload["status"] == "completed"
    assert payload["stdout"] == "6\n"
    assert payload["visualizationMode"] == "none"
    assert payload["visualization"] is None

    if shutil.which("gdb") is None:
        assert payload["step_count"] == 0
    else:
        assert payload["step_count"] >= 1
        assert any(step["function_name"] == "main" for step in payload["steps"])


@pytest.mark.skipif(
    shutil.which("gcc") is None or shutil.which("gdb") is None,
    reason="gcc/gdb가 없는 환경에서는 C global trace 테스트를 건너뜁니다.",
)
def test_create_execution_with_c_global_matrix_supports_dp_table_visualization(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "c",
            "source_code": (
                "#include <stdio.h>\n"
                "\n"
                "int matrix[2][2] = {{0, 0}, {0, 0}};\n"
                "\n"
                "int main(void) {\n"
                "    matrix[0][0] = 1;\n"
                "    matrix[0][1] = 2;\n"
                "    matrix[1][1] = 3;\n"
                "    printf(\"%d\\n\", matrix[1][1]);\n"
                "    return 0;\n"
                "}\n"
            ),
            "stdin": "",
            "visualizationMode": "dp-table",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert any("matrix" in step["globals_snapshot"] for step in payload["steps"])
    assert payload["visualizationMode"] == "dp-table"
    assert payload["visualization"]["kind"] == "dp-table"


@pytest.mark.skipif(
    shutil.which("javac") is None or shutil.which("java") is None or find_jdb_executable() is None,
    reason="javac/java가 없는 환경에서는 Java 실행 테스트를 건너뜁니다.",
)
def test_create_execution_with_java_scalar_code_returns_output_and_visualization(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "java",
            "source_code": (
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        int a = 2;\n"
                "        int b = 4;\n"
                "        System.out.println(a + b);\n"
                "    }\n"
                "}\n"
            ),
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["language"] == "java"
    assert payload["status"] == "completed"
    assert payload["stdout"] == "6\n"
    assert payload["visualizationMode"] in {"none", "array-cells"}
    if payload["visualizationMode"] == "array-cells":
        assert payload["visualization"]["kind"] == "array-cells"
    else:
        assert payload["visualization"] is None
    assert payload["step_count"] > 0


@pytest.mark.skipif(
    shutil.which("javac") is None or shutil.which("java") is None or find_jdb_executable() is None,
    reason="javac/java가 없는 환경에서는 Java 실행 테스트를 건너뜁니다.",
)
def test_create_execution_with_java_auto_array_uses_trace_visualization(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/executions",
        json={
            "language": "java",
            "source_code": (
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        int[] arr = {3, 1, 2};\n"
                "        for (int i = 0; i < arr.length; i++) {\n"
                "            System.out.println(arr[i]);\n"
                "        }\n"
                "    }\n"
                "}\n"
            ),
            "stdin": "",
            "visualizationMode": "auto",
        },
    )

    assert response.status_code == 201
    payload = response.json()["data"]
    assert payload["language"] == "java"
    assert payload["status"] == "completed"
    assert payload["stdout"] == "3\n1\n2\n"
    assert payload["step_count"] > 0
    assert payload["visualizationMode"] == "array-bars"
    assert payload["visualization"]["kind"] == "array-bars"
