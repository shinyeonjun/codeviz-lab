from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.modules.executions.domain.trace import TraceExecutionCommand, TraceExecutionResult
from app.modules.executions.infrastructure.runners.shared import (
    decode_process_output,
    encode_runner_payload,
    parse_trace_result_payload,
)

RUNNER_SCRIPT_PATH = Path(__file__).with_name("c_trace_runner.py")


class LocalCExecutionRunner:
    def __init__(
        self,
        *,
        timeout_seconds: int,
        max_trace_steps: int,
        max_stdout_chars: int,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._max_trace_steps = max_trace_steps
        self._max_stdout_chars = max_stdout_chars

    def run(self, command: TraceExecutionCommand) -> TraceExecutionResult:
        if command.language != "c":
            return TraceExecutionResult.unsupported_language(language=command.language)

        try:
            completed = subprocess.run(
                [sys.executable, str(RUNNER_SCRIPT_PATH)],
                input=encode_runner_payload(source_code=command.source_code, stdin=command.stdin),
                capture_output=True,
                timeout=self._timeout_seconds + 3,
                check=False,
                env={
                    **os.environ,
                    "CODEVIZ_TIMEOUT_SECONDS": str(self._timeout_seconds),
                    "CODEVIZ_MAX_TRACE_STEPS": str(self._max_trace_steps),
                    "CODEVIZ_MAX_STDOUT_CHARS": str(self._max_stdout_chars),
                },
            )
        except subprocess.TimeoutExpired:
            return TraceExecutionResult.timeout(language=command.language)

        stdout_text = decode_process_output(completed.stdout)
        stderr_text = decode_process_output(completed.stderr)

        if completed.returncode != 0:
            message = stderr_text.strip() or "C 실행 결과를 생성하지 못했습니다."
            return TraceExecutionResult.failure(
                language=command.language,
                message=message,
            )

        return parse_trace_result_payload(
            language=command.language,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            invalid_payload_message="C 실행 결과를 해석하지 못했습니다.",
        )
