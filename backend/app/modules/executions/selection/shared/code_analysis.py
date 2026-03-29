from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field


SUPPORTED_ANALYSIS_LANGUAGES = {"python", "c"}


@dataclass(slots=True)
class CodeAnalysisSnapshot:
    language: str
    summary_lines: list[str]
    suggested_mode: str | None = None
    detected_structures: list[str] = field(default_factory=list)


def analyze_source_code(
    *,
    language: str,
    source_code: str,
    supported_modes: set[str],
) -> CodeAnalysisSnapshot:
    if language == "python":
        return _analyze_python_source(source_code=source_code, supported_modes=supported_modes)
    if language == "c":
        return _analyze_c_source(source_code=source_code, supported_modes=supported_modes)

    return CodeAnalysisSnapshot(
        language=language,
        summary_lines=["정적 분석을 지원하지 않는 언어입니다. 원본 코드만 참고해 판단하세요."],
    )


def _analyze_python_source(
    *,
    source_code: str,
    supported_modes: set[str],
) -> CodeAnalysisSnapshot:
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return CodeAnalysisSnapshot(
            language="python",
            summary_lines=["구문 분석에 실패했습니다. 원본 코드만 참고해 판단하세요."],
        )

    function_names: list[str] = []
    recursive_functions: list[str] = []
    for_count = 0
    while_count = 0
    numeric_list_targets: set[str] = set()
    list_targets: set[str] = set()
    matrix_targets: set[str] = set()
    dict_targets: set[str] = set()
    stack_candidates: Counter[str] = Counter()
    queue_candidates: Counter[str] = Counter()
    sort_candidates: Counter[str] = Counter()
    tree_cues = 0
    graph_cues = 0
    matrix_updates = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
            if any(
                isinstance(child, ast.Call)
                and isinstance(child.func, ast.Name)
                and child.func.id == node.name
                for child in ast.walk(node)
            ):
                recursive_functions.append(node.name)
        elif isinstance(node, ast.For):
            for_count += 1
        elif isinstance(node, ast.While):
            while_count += 1
        elif isinstance(node, ast.Assign):
            target_names = [target.id for target in node.targets if isinstance(target, ast.Name)]
            if isinstance(node.value, ast.List):
                for target_name in target_names:
                    list_targets.add(target_name)
                    if _is_numeric_sequence(node.value):
                        numeric_list_targets.add(target_name)
                    if any(isinstance(item, ast.List) for item in node.value.elts):
                        matrix_targets.add(target_name)
            if isinstance(node.value, ast.Dict):
                for target_name in target_names:
                    dict_targets.add(target_name)
                tree_cues += _count_tree_dict_cues(node.value)
                graph_cues += _count_graph_dict_cues(node.value)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                target_name = node.func.value.id
                if node.func.attr == "append":
                    stack_candidates[target_name] += 1
                    queue_candidates[target_name] += 1
                elif node.func.attr == "pop":
                    stack_candidates[target_name] += 1
                    if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                        queue_candidates[target_name] += 2
                elif node.func.attr == "popleft":
                    queue_candidates[target_name] += 2
                elif node.func.attr == "sort":
                    sort_candidates[target_name] += 2
            if node.func.attr in {"left", "right"}:
                tree_cues += 1
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Subscript):
                matrix_updates += 1
            elif _contains_tree_attribute(node):
                tree_cues += 1

    summary_lines = [
        f"함수 {len(function_names)}개, for {for_count}개, while {while_count}개",
    ]
    detected_structures: list[str] = []

    if recursive_functions:
        summary_lines.append(f"재귀 함수 후보: {', '.join(sorted(set(recursive_functions)))}")
        detected_structures.append("recursion")
    if numeric_list_targets:
        summary_lines.append(f"숫자 배열 후보: {', '.join(sorted(numeric_list_targets))}")
        detected_structures.append("numeric-array")
    elif list_targets:
        summary_lines.append(f"리스트 후보: {', '.join(sorted(list_targets))}")
        detected_structures.append("list")
    if matrix_targets or matrix_updates:
        matrix_names = ", ".join(sorted(matrix_targets)) if matrix_targets else "미확정"
        summary_lines.append(f"2차원 표 후보: {matrix_names}, 이중 인덱싱 {matrix_updates}건")
        detected_structures.append("matrix")
    if dict_targets:
        summary_lines.append(f"dict 후보: {', '.join(sorted(dict_targets))}")
        detected_structures.append("dict")

    stack_hints = [name for name, count in stack_candidates.items() if count >= 2]
    queue_hints = [name for name, count in queue_candidates.items() if count >= 2]
    sort_hints = [name for name, count in sort_candidates.items() if count >= 1]

    if sort_hints:
        summary_lines.append(f"정렬/재배치 패턴 후보: {', '.join(sorted(sort_hints))}")
        detected_structures.append("sorting")
    if stack_hints:
        summary_lines.append(f"LIFO 패턴 후보: {', '.join(sorted(stack_hints))}")
        detected_structures.append("stack")
    if queue_hints:
        summary_lines.append(f"FIFO 패턴 후보: {', '.join(sorted(queue_hints))}")
        detected_structures.append("queue")
    if tree_cues:
        summary_lines.append(f"트리 단서 {tree_cues}건 감지")
        detected_structures.append("tree")
    if graph_cues:
        summary_lines.append(f"그래프 단서 {graph_cues}건 감지")
        detected_structures.append("graph")

    summary_lines.append("템플릿은 알고리즘 이름보다 상태 변화가 가장 잘 드러나는 구조를 우선 선택")
    suggested_mode = _detect_python_mode(tree=tree, supported_modes=supported_modes)
    return CodeAnalysisSnapshot(
        language="python",
        summary_lines=summary_lines,
        suggested_mode=suggested_mode,
        detected_structures=sorted(set(detected_structures)),
    )


def _analyze_c_source(
    *,
    source_code: str,
    supported_modes: set[str],
) -> CodeAnalysisSnapshot:
    sanitized = _strip_c_comments(source_code)
    function_names = _find_c_function_names(sanitized)
    for_count = len(re.findall(r"\bfor\s*\(", sanitized))
    while_count = len(re.findall(r"\bwhile\s*\(", sanitized))
    array_names = _find_c_array_names(sanitized)
    matrix_names = _find_c_matrix_names(sanitized)
    queue_cues = _find_named_cues(sanitized, {"queue", "front", "rear", "dequeue", "enqueue"})
    stack_cues = _find_named_cues(sanitized, {"stack", "top", "push", "pop"})
    graph_cues = _find_named_cues(sanitized, {"graph", "adj", "visited", "neighbor"})
    tree_cues = _find_named_cues(sanitized, {"left", "right", "node", "root"})
    recursive_functions = [name for name in function_names if re.search(rf"\b{name}\s*\(", _function_body(sanitized, name))]
    has_struct = bool(re.search(r"\bstruct\b", sanitized))
    has_printf = "printf" in sanitized

    summary_lines = [f"함수 {len(function_names)}개, for {for_count}개, while {while_count}개"]
    detected_structures: list[str] = []

    if function_names:
        summary_lines.append(f"함수 후보: {', '.join(function_names)}")
    if recursive_functions:
        summary_lines.append(f"재귀 함수 후보: {', '.join(sorted(set(recursive_functions)))}")
        detected_structures.append("recursion")
    if array_names:
        summary_lines.append(f"배열 후보: {', '.join(array_names)}")
        detected_structures.append("array")
    if matrix_names:
        summary_lines.append(f"2차원 배열 후보: {', '.join(matrix_names)}")
        detected_structures.append("matrix")
    if stack_cues:
        summary_lines.append(f"스택 단서: {', '.join(stack_cues)}")
        detected_structures.append("stack")
    if queue_cues:
        summary_lines.append(f"큐 단서: {', '.join(queue_cues)}")
        detected_structures.append("queue")
    if graph_cues:
        summary_lines.append(f"그래프 단서: {', '.join(graph_cues)}")
        detected_structures.append("graph")
    if tree_cues or has_struct:
        tree_hint = ", ".join(tree_cues) if tree_cues else "struct 기반 노드 후보"
        summary_lines.append(f"트리 단서: {tree_hint}")
        detected_structures.append("tree")
    if has_printf:
        summary_lines.append("표준 출력 호출이 포함됨")
    summary_lines.append("포인터/구조체보다 배열과 제어 흐름이 먼저 드러나는 학습용 템플릿을 우선 선택")

    suggested_mode = _detect_c_mode(source_code=sanitized, supported_modes=supported_modes)
    return CodeAnalysisSnapshot(
        language="c",
        summary_lines=summary_lines,
        suggested_mode=suggested_mode,
        detected_structures=sorted(set(detected_structures)),
    )


def _detect_python_mode(*, tree: ast.AST, supported_modes: set[str]) -> str | None:
    return (
        _detect_python_graph_mode(tree, supported_modes)
        or _detect_python_dp_mode(tree)
        or _detect_python_call_stack_mode(tree)
        or _detect_python_queue_or_stack_mode(tree)
        or _detect_python_array_mode(tree)
    )


def _detect_python_graph_mode(tree: ast.AST, supported_modes: set[str]) -> str | None:
    graph_like_names: set[str] = set()
    has_queue_pattern = False
    has_stack_pattern = False
    has_visited_name = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            if _is_graph_like_dict(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        graph_like_names.add(target.id)
        elif isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            if any(isinstance(target, ast.Name) and target.id == "visited" for target in node.targets):
                has_visited_name = True
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "append" and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "queue":
                    has_queue_pattern = True
                if node.func.value.id == "stack":
                    has_stack_pattern = True
            if node.func.attr == "pop" and isinstance(node.func.value, ast.Name):
                if node.func.value.id == "queue":
                    has_queue_pattern = True
                if node.func.value.id == "stack":
                    has_stack_pattern = True

    if graph_like_names and has_queue_pattern and has_visited_name:
        return "graph-bfs-traversal" if "graph-bfs-traversal" in supported_modes else "graph-node-edge"
    if graph_like_names and has_stack_pattern:
        return "graph-dfs-traversal" if "graph-dfs-traversal" in supported_modes else "graph-node-edge"
    if graph_like_names:
        return "graph-node-edge"
    return None


def _detect_python_dp_mode(tree: ast.AST) -> str | None:
    has_nested_list_assignment = False
    has_two_dimensional_subscript = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            if any(isinstance(element, ast.List) for element in node.value.elts):
                has_nested_list_assignment = True
        if isinstance(node, ast.Subscript) and _is_two_dimensional_subscript(node):
            has_two_dimensional_subscript = True

    if has_nested_list_assignment and has_two_dimensional_subscript:
        return "dp-table"
    return None


def _detect_python_call_stack_mode(tree: ast.AST) -> str | None:
    function_names = {
        node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if len(function_names) >= 2:
        return "call-stack"
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in function_names:
            return "call-stack"
    return None


def _detect_python_queue_or_stack_mode(tree: ast.AST) -> str | None:
    enqueue_like = False
    dequeue_like = False
    push_like = False
    pop_like = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "append":
                if _looks_like_literal_list_container(node.func.value):
                    push_like = True
                    enqueue_like = True
            elif node.func.attr == "pop":
                if node.args and isinstance(node.args[0], ast.Constant) and node.args[0].value == 0:
                    dequeue_like = True
                else:
                    pop_like = True

    if enqueue_like and dequeue_like:
        return "queue-horizontal"
    if push_like and pop_like:
        return "stack-vertical"
    return None


def _detect_python_array_mode(tree: ast.AST) -> str | None:
    has_numeric_sequence = False
    has_sort_call = False
    has_subscript_assignment = False

    for node in ast.walk(tree):
        if isinstance(node, ast.List) and node.elts and all(
            isinstance(element, ast.Constant) and isinstance(element.value, (int, float))
            for element in node.elts
        ):
            has_numeric_sequence = True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "sort":
            has_sort_call = True
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Subscript) for target in node.targets):
            has_subscript_assignment = True

    if has_numeric_sequence and (has_sort_call or has_subscript_assignment):
        return "array-bars"
    if has_numeric_sequence:
        return "array-bars"
    return None


def _detect_c_mode(*, source_code: str, supported_modes: set[str]) -> str | None:
    if _looks_like_c_graph_bfs(source_code):
        return "graph-bfs-traversal" if "graph-bfs-traversal" in supported_modes else "graph-node-edge"
    if _looks_like_c_graph_dfs(source_code):
        return "graph-dfs-traversal" if "graph-dfs-traversal" in supported_modes else "graph-node-edge"
    if _looks_like_c_dp(source_code):
        return "dp-table"
    if _looks_like_c_call_stack(source_code):
        return "call-stack"
    if _looks_like_c_queue(source_code):
        return "queue-horizontal"
    if _looks_like_c_stack(source_code):
        return "stack-vertical"
    if _looks_like_c_numeric_array(source_code):
        return "array-bars"
    return None


def _looks_like_c_graph_bfs(source_code: str) -> bool:
    return (
        bool(re.search(r"\bvisited\b", source_code))
        and bool(re.search(r"\bqueue\b|\bfront\b|\brear\b", source_code))
        and bool(re.search(r"\bgraph\b|\badj\b|\bneighbor\b", source_code))
    )


def _looks_like_c_graph_dfs(source_code: str) -> bool:
    return bool(re.search(r"\bvisited\b", source_code)) and bool(
        re.search(r"\bstack\b|\bdfs\s*\(", source_code)
    ) and bool(re.search(r"\bgraph\b|\badj\b|\bneighbor\b", source_code))


def _looks_like_c_dp(source_code: str) -> bool:
    return bool(re.search(r"\w+\s*\[[^\]]*\]\s*\[[^\]]*\]", source_code))


def _looks_like_c_call_stack(source_code: str) -> bool:
    function_names = _find_c_function_names(source_code)
    return len(function_names) >= 2


def _looks_like_c_queue(source_code: str) -> bool:
    return bool(re.search(r"\bqueue\b|\bfront\b|\brear\b|\benqueue\b|\bdequeue\b", source_code))


def _looks_like_c_stack(source_code: str) -> bool:
    return bool(re.search(r"\bstack\b|\btop\b|\bpush\b|\bpop\b", source_code))


def _looks_like_c_numeric_array(source_code: str) -> bool:
    return bool(re.search(r"\b(?:int|long|short|float|double)\s+\w+\s*\[[^\]]*\]", source_code))


def _strip_c_comments(source_code: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", "", source_code, flags=re.S)
    return re.sub(r"//.*?$", "", without_block_comments, flags=re.M)


def _find_c_function_names(source_code: str) -> list[str]:
    pattern = re.compile(
        r"^\s*(?:static\s+)?(?:int|void|char|float|double|long|short|bool|size_t|struct\s+\w+|\w+\s*\*)\s+(\w+)\s*\([^;]*\)\s*\{",
        flags=re.M,
    )
    return pattern.findall(source_code)


def _find_c_array_names(source_code: str) -> list[str]:
    pattern = re.compile(r"\b(?:int|long|short|float|double|char)\s+(\w+)\s*\[[^\]]*\]")
    return sorted(set(pattern.findall(source_code)))


def _find_c_matrix_names(source_code: str) -> list[str]:
    pattern = re.compile(r"\b(?:int|long|short|float|double|char)\s+(\w+)\s*\[[^\]]*\]\s*\[[^\]]*\]")
    return sorted(set(pattern.findall(source_code)))


def _find_named_cues(source_code: str, names: set[str]) -> list[str]:
    found = [name for name in sorted(names) if re.search(rf"\b{name}\b", source_code)]
    return found


def _function_body(source_code: str, function_name: str) -> str:
    match = re.search(rf"\b{function_name}\s*\([^;]*\)\s*\{{", source_code)
    if not match:
        return ""
    return source_code[match.end() :]


def _is_numeric_sequence(node: ast.List) -> bool:
    return bool(node.elts) and all(
        isinstance(item, ast.Constant) and isinstance(item.value, (int, float))
        for item in node.elts
    )


def _count_tree_dict_cues(node: ast.Dict) -> int:
    score = 0
    keys = [
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    ]
    if {"left", "right"} & set(keys):
        score += 2
    if "value" in keys:
        score += 1
    return score


def _count_graph_dict_cues(node: ast.Dict) -> int:
    score = 0
    if any(isinstance(value, ast.List) for value in node.values):
        score += 1
    if len(node.keys) >= 2:
        score += 1
    return score


def _contains_tree_attribute(node: ast.Subscript) -> bool:
    value = node.value
    while isinstance(value, ast.Subscript):
        value = value.value
    if isinstance(value, ast.Attribute):
        return value.attr in {"left", "right"}
    return False


def _is_graph_like_dict(node: ast.Dict) -> bool:
    if not node.keys or not node.values:
        return False
    for key, value in zip(node.keys, node.values):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, (str, int)):
            return False
        if not isinstance(value, ast.List):
            return False
        if not all(isinstance(element, ast.Constant) for element in value.elts):
            return False
    return True


def _is_two_dimensional_subscript(node: ast.Subscript) -> bool:
    return isinstance(node.value, ast.Subscript)


def _looks_like_literal_list_container(node: ast.AST) -> bool:
    return isinstance(node, ast.Name)
