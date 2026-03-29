from collections.abc import Iterable

from app.modules.executions.visualizations.base.template import ExecutionVisualizationTemplate


class ExecutionVisualizationRegistry:
    def __init__(self, *, templates: Iterable[ExecutionVisualizationTemplate]) -> None:
        self._templates = {template.visualization_mode: template for template in templates}

    @property
    def supported_modes(self) -> set[str]:
        return set(self._templates.keys())

    def get(self, visualization_mode: str) -> ExecutionVisualizationTemplate | None:
        return self._templates.get(visualization_mode) or self._templates.get("none")
