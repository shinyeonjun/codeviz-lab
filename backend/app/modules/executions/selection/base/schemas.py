from dataclasses import dataclass, field


@dataclass(slots=True)
class VisualizationSelectionContext:
    requested_mode: str
    source_code: str
    language: str


@dataclass(slots=True)
class VisualizationSelectionResult:
    selected_mode: str
    reason: str = ""
    confidence: float | None = None
    alternatives: list[str] = field(default_factory=list)
