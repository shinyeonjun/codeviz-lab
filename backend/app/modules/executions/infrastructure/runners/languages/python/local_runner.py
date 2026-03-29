from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.modules.executions.domain.trace import TraceExecutionCommand, TraceExecutionResult
from app.modules.executions.infrastructure.runners.shared import (
    decode_process_output,
)

RUNNER_SCRIPT_PATH = Path(__file__).with_name("sandbox_trace_runner.py")


class LocalPythonTraceRunner:
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
        if command.language != "python":
            return TraceExecutionResult.unsupported_language(language=command.language)

        with tempfile.TemporaryDirectory(prefix="codeviz_runner_") as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "user_code.py"
            result_path = temp_path / "result.json"

            try:
                source_path.write_text(command.source_code, encoding="utf-8")
            except UnicodeEncodeError:
                return TraceExecutionResult.failure(
                    language=command.language,
                    message="소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                )

            env = {
                **os.environ,
                "CODEVIZ_MAX_TRACE_STEPS": str(self._max_trace_steps),
                "CODEVIZ_MAX_STDOUT_CHARS": str(self._max_stdout_chars),
            }

            try:
                completed = subprocess.run(
                    [sys.executable, str(RUNNER_SCRIPT_PATH), str(source_path), str(result_path)],
                    input=json.dumps({"stdin": command.stdin}, ensure_ascii=False).encode("utf-8"),
                    capture_output=True,
                    timeout=self._timeout_seconds,
                    check=False,
                    env=env,
                )
            except subprocess.TimeoutExpired:
                return TraceExecutionResult.timeout(language=command.language)

            if not result_path.exists():
                message = decode_process_output(completed.stderr).strip() or "실행 결과를 생성하지 못했습니다."
                return TraceExecutionResult.failure(
                    language=command.language,
                    message=message,
                )

            payload = json.loads(result_path.read_text(encoding="utf-8"))
            completed_stderr = decode_process_output(completed.stderr).strip()
            return TraceExecutionResult.from_payload(
                language=command.language,
                payload=payload,
                stderr_override=completed_stderr or None,
            )
