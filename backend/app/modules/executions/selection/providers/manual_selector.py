import ast

from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.base.schemas import (
    VisualizationSelectionContext,
    VisualizationSelectionResult,
)


class ManualVisualizationSelector(VisualizationSelectorProtocol):
    def __init__(self, *, supported_modes: set[str], default_mode: str = "none") -> None:
        self._supported_modes = supported_modes
        self._default_mode = default_mode

    def select(self, context: VisualizationSelectionContext) -> VisualizationSelectionResult:
        if context.requested_mode == "auto":
            selected_mode = self._select_auto_mode(context)
            reason = "수동 선택기 휴리스틱으로 시각화 모드를 결정했습니다."
            confidence = 0.35 if selected_mode != self._default_mode else 0.0
            if selected_mode == self._default_mode:
                reason = "자동 선택기 휴리스틱에서 적합한 모드를 찾지 못해 기본 시각화 모드를 사용합니다."
            return VisualizationSelectionResult(
                selected_mode=selected_mode,
                reason=reason,
                confidence=confidence,
                alternatives=sorted(mode for mode in self._supported_modes if mode != selected_mode),
            )

        selected_mode = (
            context.requested_mode
            if context.requested_mode in self._supported_modes
            else self._default_mode
        )
        reason = "요청된 시각화 모드를 그대로 사용합니다."
        if selected_mode != context.requested_mode:
            reason = "지원하지 않는 시각화 모드라 기본 모드로 대체합니다."

        alternatives = sorted(mode for mode in self._supported_modes if mode != selected_mode)
        return VisualizationSelectionResult(
            selected_mode=selected_mode,
            reason=reason,
            confidence=1.0,
            alternatives=alternatives,
        )

    def _select_auto_mode(self, context: VisualizationSelectionContext) -> str:
        if context.language != "python":
            return self._default_mode

        source = context.source_code
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._default_mode

        detected_mode = (
            self._detect_graph_mode(tree)
            or self._detect_dp_mode(tree)
            or self._detect_call_stack_mode(tree)
            or self._detect_queue_or_stack_mode(tree)
            or self._detect_array_mode(tree)
        )
        if detected_mode and detected_mode in self._supported_modes:
            return detected_mode
        return self._default_mode

    def _detect_graph_mode(self, tree: ast.AST) -> str | None:
        graph_like_names: set[str] = set()
        has_queue_pattern = False
        has_stack_pattern = False
        has_visited_name = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                if self._is_graph_like_dict(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            graph_like_names.add(target.id)
            elif isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
                if any(isinstance(target, ast.Name) and target.id == "visited" for target in node.targets):
                    has_visited_name = True
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "append" and isinstance(node.func.value, ast.Name):
                    container_name = node.func.value.id
                    if container_name == "queue":
                        has_queue_pattern = True
                    if container_name == "stack":
                        has_stack_pattern = True
                if node.func.attr == "pop" and isinstance(node.func.value, ast.Name):
                    container_name = node.func.value.id
                    if container_name == "queue":
                        has_queue_pattern = True
                    if container_name == "stack":
                        has_stack_pattern = True

        if graph_like_names and has_queue_pattern and has_visited_name:
            return "graph-bfs-traversal" if "graph-bfs-traversal" in self._supported_modes else "graph-node-edge"
        if graph_like_names and has_stack_pattern:
            return "graph-dfs-traversal" if "graph-dfs-traversal" in self._supported_modes else "graph-node-edge"
        if graph_like_names:
            return "graph-node-edge"
        return None

    def _detect_dp_mode(self, tree: ast.AST) -> str | None:
        has_nested_list_assignment = False
        has_two_dimensional_subscript = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
                if any(isinstance(element, ast.List) for element in node.value.elts):
                    has_nested_list_assignment = True
            if isinstance(node, ast.Subscript) and self._is_two_dimensional_subscript(node):
                has_two_dimensional_subscript = True

        if has_nested_list_assignment and has_two_dimensional_subscript:
            return "dp-table"
        return None

    def _detect_call_stack_mode(self, tree: ast.AST) -> str | None:
        function_names = {
            node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        if len(function_names) >= 2:
            return "call-stack"
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in function_names:
                return "call-stack"
        return None

    def _detect_queue_or_stack_mode(self, tree: ast.AST) -> str | None:
        enqueue_like = False
        dequeue_like = False
        push_like = False
        pop_like = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "append":
                    if self._looks_like_literal_list_container(node.func.value):
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

    def _detect_array_mode(self, tree: ast.AST) -> str | None:
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
            if isinstance(node, ast.Assign):
                if any(isinstance(target, ast.Subscript) for target in node.targets):
                    has_subscript_assignment = True

        if has_numeric_sequence and (has_sort_call or has_subscript_assignment):
            return "array-bars"
        if has_numeric_sequence:
            return "array-bars"
        return None

    @staticmethod
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

    @staticmethod
    def _is_two_dimensional_subscript(node: ast.Subscript) -> bool:
        return isinstance(node.value, ast.Subscript)

    @staticmethod
    def _looks_like_literal_list_container(node: ast.AST) -> bool:
        return isinstance(node, ast.Name)
