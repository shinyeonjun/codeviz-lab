from __future__ import annotations

from app.modules.executions.domain.trace import TraceExecutionCommand, TraceExecutionResult


class LanguageDispatchTraceRunner:
    def __init__(self, *, runners: dict[str, object]) -> None:
        self._runners = runners

    def run(self, command: TraceExecutionCommand) -> TraceExecutionResult:
        runner = self._runners.get(command.language)
        if runner is None:
            return TraceExecutionResult.unsupported_language(language=command.language)
        return runner.run(command)
