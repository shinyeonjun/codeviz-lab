from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceExecutionCommand:
    language: str
    source_code: str
    stdin: str


@dataclass(slots=True)
class TraceFrame:
    function_name: str
    line_number: int | None = None
    locals_snapshot: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TraceFrame":
        function_name = str(
            payload.get("function_name")
            or payload.get("functionName")
            or payload.get("name")
            or "<unknown>"
        )
        line_number = payload.get("line_number", payload.get("lineNumber"))
        if not isinstance(line_number, int):
            line_number = None
        locals_snapshot = payload.get("locals_snapshot", payload.get("localsSnapshot", {}))
        if not isinstance(locals_snapshot, dict):
            locals_snapshot = {}
        return cls(
            function_name=function_name,
            line_number=line_number,
            locals_snapshot=locals_snapshot,
        )


@dataclass(slots=True)
class TraceStepIR:
    line_number: int
    event_type: str
    function_name: str
    locals_snapshot: dict[str, Any]
    stdout_snapshot: str
    error_message: str | None = None
    call_stack: list[TraceFrame] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "TraceStepIR":
        line_number = payload.get("line_number", payload.get("lineNumber", 0))
        if not isinstance(line_number, int):
            line_number = 0

        event_type = payload.get("event_type", payload.get("eventType", "line"))
        function_name = payload.get("function_name", payload.get("functionName", "<module>"))
        locals_snapshot = payload.get("locals_snapshot", payload.get("localsSnapshot", {}))
        stdout_snapshot = payload.get("stdout_snapshot", payload.get("stdoutSnapshot", ""))
        error_message = payload.get("error_message", payload.get("errorMessage"))
        call_stack_payload = payload.get("call_stack", payload.get("callStack", []))
        metadata = payload.get("metadata", {})

        if not isinstance(event_type, str):
            event_type = "line"
        if not isinstance(function_name, str):
            function_name = "<module>"
        if not isinstance(locals_snapshot, dict):
            locals_snapshot = {}
        if not isinstance(stdout_snapshot, str):
            stdout_snapshot = str(stdout_snapshot)
        if error_message is not None and not isinstance(error_message, str):
            error_message = str(error_message)
        if not isinstance(metadata, dict):
            metadata = {}

        call_stack: list[TraceFrame] = []
        if isinstance(call_stack_payload, list):
            for frame in call_stack_payload:
                if isinstance(frame, dict):
                    call_stack.append(TraceFrame.from_payload(frame))

        return cls(
            line_number=line_number,
            event_type=event_type,
            function_name=function_name,
            locals_snapshot=locals_snapshot,
            stdout_snapshot=stdout_snapshot,
            error_message=error_message,
            call_stack=call_stack,
            metadata=metadata,
        )


@dataclass(slots=True)
class TraceExecutionSummary:
    total_steps: int = 0
    function_names: list[str] = field(default_factory=list)
    has_stdout: bool = False
    has_errors: bool = False

    @classmethod
    def from_steps(
        cls,
        steps: list[TraceStepIR],
        *,
        stdout: str,
        stderr: str,
        error_message: str | None,
    ) -> "TraceExecutionSummary":
        function_names = sorted({step.function_name for step in steps if step.function_name})
        has_step_errors = any(step.error_message for step in steps)
        return cls(
            total_steps=len(steps),
            function_names=function_names,
            has_stdout=bool(stdout),
            has_errors=bool(stderr or error_message or has_step_errors),
        )


@dataclass(slots=True)
class TraceExecutionIR:
    language: str
    status: str
    stdout: str
    stderr: str
    error_message: str | None
    steps: list[TraceStepIR] = field(default_factory=list)
    summary: TraceExecutionSummary | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.summary is None:
            self.summary = TraceExecutionSummary.from_steps(
                self.steps,
                stdout=self.stdout,
                stderr=self.stderr,
                error_message=self.error_message,
            )

    @classmethod
    def from_payload(
        cls,
        *,
        language: str,
        payload: dict[str, Any],
        stderr_override: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "TraceExecutionIR":
        steps_payload = payload.get("steps", [])
        steps: list[TraceStepIR] = []
        if isinstance(steps_payload, list):
            for step_payload in steps_payload:
                if isinstance(step_payload, dict):
                    steps.append(TraceStepIR.from_payload(step_payload))

        stderr = payload.get("stderr", "")
        if not isinstance(stderr, str):
            stderr = str(stderr)
        if stderr_override:
            stderr = "\n".join(filter(None, [stderr, stderr_override]))

        stdout = payload.get("stdout", "")
        if not isinstance(stdout, str):
            stdout = str(stdout)

        error_message = payload.get("error_message", payload.get("errorMessage"))
        if error_message is not None and not isinstance(error_message, str):
            error_message = str(error_message)

        status = payload.get("status", "failed")
        if not isinstance(status, str):
            status = "failed"

        return cls(
            language=language,
            status=status,
            stdout=stdout,
            stderr=stderr,
            error_message=error_message,
            steps=steps,
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        *,
        language: str,
        message: str,
        stderr: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "TraceExecutionIR":
        return cls(
            language=language,
            status="failed",
            stdout="",
            stderr=stderr or message,
            error_message=message,
            steps=[],
            metadata=metadata or {},
        )

    @classmethod
    def timeout(
        cls,
        *,
        language: str,
        message: str = "코드 실행 시간이 제한을 초과했습니다.",
        metadata: dict[str, Any] | None = None,
    ) -> "TraceExecutionIR":
        return cls(
            language=language,
            status="timeout",
            stdout="",
            stderr="",
            error_message=message,
            steps=[],
            metadata=metadata or {},
        )

    @classmethod
    def unsupported_language(cls, *, language: str) -> "TraceExecutionIR":
        return cls.failure(
            language=language,
            message=f"{language} 언어는 아직 지원하지 않습니다.",
        )
