from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class VisualizationSelectionContext:
    requested_mode: str
    source_code: str
    language: str
    trace_result: Any | None = None


@dataclass(slots=True)
class VisualizationSelectionResult:
    selected_mode: str
    reason: str = ""
    confidence: float | None = None
    alternatives: list[str] = field(default_factory=list)
    summary: str = ""
    observations: list[str] = field(default_factory=list)
    learning_points: list[str] = field(default_factory=list)
