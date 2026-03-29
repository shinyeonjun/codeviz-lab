from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceExecutionCommand:
    language: str
    source_code: str
    stdin: str


@dataclass(slots=True)
class TraceStep:
    line_number: int
    event_type: str
    function_name: str
    locals_snapshot: dict[str, Any]
    stdout_snapshot: str
    error_message: str | None = None


@dataclass(slots=True)
class TraceExecutionResult:
    status: str
    stdout: str
    stderr: str
    error_message: str | None
    steps: list[TraceStep] = field(default_factory=list)
