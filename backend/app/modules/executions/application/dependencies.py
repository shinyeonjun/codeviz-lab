from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.modules.executions.application.services.execution_service import ExecutionService
from app.modules.executions.domain.ports import (
    ExecutionRepositoryProtocol,
    ExecutionVisualizerProtocol,
    TraceRunnerProtocol,
)
from app.modules.executions.infrastructure.persistence.repository import SqlAlchemyExecutionRepository
from app.modules.executions.infrastructure.runners.language_dispatch_runner import (
    LanguageDispatchTraceRunner,
)
from app.modules.executions.infrastructure.runners.languages.c.docker_runner import (
    DockerCExecutionRunner,
)
from app.modules.executions.infrastructure.runners.languages.c.local_runner import (
    LocalCExecutionRunner,
)
from app.modules.executions.infrastructure.runners.languages.python.docker_runner import (
    DockerTraceRunner,
)
from app.modules.executions.infrastructure.runners.languages.python.local_runner import (
    LocalPythonTraceRunner,
)
from app.modules.executions.selection.base.interfaces import VisualizationSelectorProtocol
from app.modules.executions.selection.providers.local_selector import LocalVisualizationSelector
from app.modules.executions.selection.providers.manual_selector import ManualVisualizationSelector
from app.modules.executions.selection.providers.openai_selector import OpenAIVisualizationSelector
from app.modules.executions.selection.service import VisualizationSelectionService
from app.modules.executions.visualizations.base.registry import ExecutionVisualizationRegistry
from app.modules.executions.visualizations.base.service import ExecutionVisualizationService
from app.modules.executions.visualizations.templates.array_cells.template import (
    ArrayCellsExecutionTemplate,
)
from app.modules.executions.visualizations.templates.array_bars.template import (
    ArrayBarsExecutionTemplate,
)
from app.modules.executions.visualizations.templates.call_stack.template import (
    CallStackExecutionTemplate,
)
from app.modules.executions.visualizations.templates.dp_table.template import (
    DpTableExecutionTemplate,
)
from app.modules.executions.visualizations.templates.graph_node_edge.template import (
    GraphNodeEdgeExecutionTemplate,
)
from app.modules.executions.visualizations.templates.mode_aliases.template import (
    AliasExecutionTemplate,
)
from app.modules.executions.visualizations.templates.none.template import (
    NoVisualizationExecutionTemplate,
)
from app.modules.executions.visualizations.templates.palindrome_pointers.template import (
    PalindromePointersExecutionTemplate,
)
from app.modules.executions.visualizations.templates.queue_horizontal.template import (
    QueueHorizontalExecutionTemplate,
)
from app.modules.executions.visualizations.templates.stack_vertical.template import (
    StackVerticalExecutionTemplate,
)
from app.modules.executions.visualizations.templates.tree_binary.template import (
    TreeBinaryExecutionTemplate,
)


def build_execution_visualization_registry() -> ExecutionVisualizationRegistry:
    array_bars = ArrayBarsExecutionTemplate()
    array_cells = ArrayCellsExecutionTemplate()
    palindrome_pointers = PalindromePointersExecutionTemplate()
    stack_vertical = StackVerticalExecutionTemplate()
    queue_horizontal = QueueHorizontalExecutionTemplate()
    call_stack = CallStackExecutionTemplate()
    dp_table = DpTableExecutionTemplate()
    tree_binary = TreeBinaryExecutionTemplate()
    graph_node_edge = GraphNodeEdgeExecutionTemplate()

    alias_templates = [
        AliasExecutionTemplate(visualization_mode="array-selection-sort", builder=array_bars.build),
        AliasExecutionTemplate(visualization_mode="array-bubble-sort", builder=array_bars.build),
        AliasExecutionTemplate(visualization_mode="array-merge-process", builder=array_bars.build),
        AliasExecutionTemplate(visualization_mode="array-quick-partition", builder=array_bars.build),
        AliasExecutionTemplate(visualization_mode="array-heapify", builder=array_bars.build),
        AliasExecutionTemplate(visualization_mode="array-shell-sort", builder=array_bars.build),
        AliasExecutionTemplate(visualization_mode="binary-search-window", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="lower-bound-search", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="upper-bound-search", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="two-pointers-opposite", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="two-pointers-same-direction", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="sliding-window-fixed", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="sliding-window-variable", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="prefix-sum-array", builder=array_cells.build),
        AliasExecutionTemplate(visualization_mode="deque-both-ends", builder=queue_horizontal.build),
        AliasExecutionTemplate(visualization_mode="monotonic-stack", builder=stack_vertical.build),
        AliasExecutionTemplate(visualization_mode="stack-expression", builder=stack_vertical.build),
        AliasExecutionTemplate(visualization_mode="recursion-tree", builder=call_stack.build),
        AliasExecutionTemplate(visualization_mode="backtracking-tree", builder=call_stack.build),
        AliasExecutionTemplate(visualization_mode="divide-and-conquer", builder=call_stack.build),
        AliasExecutionTemplate(visualization_mode="memoized-recursion", builder=call_stack.build),
        AliasExecutionTemplate(visualization_mode="knapsack-table", builder=dp_table.build),
        AliasExecutionTemplate(visualization_mode="lcs-table", builder=dp_table.build),
        AliasExecutionTemplate(visualization_mode="edit-distance-table", builder=dp_table.build),
        AliasExecutionTemplate(visualization_mode="grid-dp", builder=dp_table.build),
        AliasExecutionTemplate(visualization_mode="tree-level-order", builder=tree_binary.build),
        AliasExecutionTemplate(visualization_mode="tree-bst-search", builder=tree_binary.build),
        AliasExecutionTemplate(visualization_mode="tree-bst-insert", builder=tree_binary.build),
        AliasExecutionTemplate(visualization_mode="graph-bfs-traversal", builder=graph_node_edge.build),
        AliasExecutionTemplate(visualization_mode="graph-dfs-traversal", builder=graph_node_edge.build),
        AliasExecutionTemplate(visualization_mode="graph-topological-sort", builder=graph_node_edge.build),
        AliasExecutionTemplate(visualization_mode="graph-connected-components", builder=graph_node_edge.build),
        AliasExecutionTemplate(visualization_mode="graph-cycle-detection", builder=graph_node_edge.build),
        AliasExecutionTemplate(visualization_mode="graph-bipartite-check", builder=graph_node_edge.build),
    ]

    return ExecutionVisualizationRegistry(
        templates=[
            NoVisualizationExecutionTemplate(),
            array_bars,
            array_cells,
            palindrome_pointers,
            stack_vertical,
            queue_horizontal,
            call_stack,
            dp_table,
            tree_binary,
            graph_node_edge,
            *alias_templates,
        ]
    )


def get_execution_repository(
    session: Session = Depends(get_db_session),
) -> ExecutionRepositoryProtocol:
    return SqlAlchemyExecutionRepository(session=session)


def get_trace_runner() -> TraceRunnerProtocol:
    if settings.runner_backend == "local":
        return LanguageDispatchTraceRunner(
            runners={
                "python": LocalPythonTraceRunner(
                    timeout_seconds=settings.runner_timeout_seconds,
                    max_trace_steps=settings.runner_max_trace_steps,
                    max_stdout_chars=settings.runner_max_stdout_chars,
                ),
                "c": LocalCExecutionRunner(
                    timeout_seconds=settings.runner_c_timeout_seconds,
                    max_trace_steps=settings.runner_max_trace_steps,
                    max_stdout_chars=settings.runner_max_stdout_chars,
                ),
            }
        )

    if settings.runner_backend == "docker":
        return LanguageDispatchTraceRunner(
            runners={
                "python": DockerTraceRunner(
                    timeout_seconds=settings.runner_timeout_seconds,
                    image=settings.runner_docker_image,
                    memory_limit=settings.runner_docker_memory_limit,
                    cpus=settings.runner_docker_cpus,
                    pids_limit=settings.runner_docker_pids_limit,
                    tmpfs_size=settings.runner_docker_tmpfs_size,
                    max_trace_steps=settings.runner_max_trace_steps,
                    max_stdout_chars=settings.runner_max_stdout_chars,
                ),
                "c": DockerCExecutionRunner(
                    timeout_seconds=settings.runner_c_timeout_seconds,
                    image=settings.runner_docker_c_image,
                    memory_limit=settings.runner_docker_memory_limit,
                    cpus=settings.runner_docker_cpus,
                    pids_limit=settings.runner_docker_pids_limit,
                    tmpfs_size=settings.runner_docker_tmpfs_size,
                    max_trace_steps=settings.runner_max_trace_steps,
                    max_stdout_chars=settings.runner_max_stdout_chars,
                ),
            }
        )

    raise HTTPException(status_code=500, detail="아직 지원하지 않는 실행기입니다.")


def get_execution_visualizer() -> ExecutionVisualizerProtocol:
    registry = build_execution_visualization_registry()
    return ExecutionVisualizationService(registry=registry)


def get_visualization_selector() -> VisualizationSelectorProtocol:
    selector_backend = getattr(settings, "visualization_selector_backend", "manual")
    supported_modes = build_execution_visualization_registry().supported_modes
    manual_selector = ManualVisualizationSelector(
        supported_modes=supported_modes,
        default_mode="none",
    )

    if selector_backend == "manual":
        return manual_selector
    if selector_backend == "openai":
        return OpenAIVisualizationSelector(
            supported_modes=supported_modes,
            fallback_selector=manual_selector,
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            api_url=settings.openai_api_url,
            timeout_seconds=settings.openai_timeout_seconds,
            max_output_tokens=settings.openai_max_output_tokens,
            reasoning_effort=settings.openai_reasoning_effort,
            text_verbosity=settings.openai_text_verbosity,
            project_id=settings.openai_project_id,
            organization_id=settings.openai_organization_id,
            default_mode="none",
        )
    if selector_backend == "local":
        return LocalVisualizationSelector()

    raise HTTPException(status_code=500, detail="아직 지원하지 않는 시각화 선택기입니다.")


def get_visualization_selection_service(
    selector: VisualizationSelectorProtocol = Depends(get_visualization_selector),
) -> VisualizationSelectionService:
    return VisualizationSelectionService(selector=selector)


def get_execution_service(
    repository: ExecutionRepositoryProtocol = Depends(get_execution_repository),
    runner: TraceRunnerProtocol = Depends(get_trace_runner),
    visualizer: ExecutionVisualizerProtocol = Depends(get_execution_visualizer),
    selection_service: VisualizationSelectionService = Depends(get_visualization_selection_service),
) -> ExecutionService:
    return ExecutionService(
        repository=repository,
        runner=runner,
        visualizer=visualizer,
        selection_service=selection_service,
    )
