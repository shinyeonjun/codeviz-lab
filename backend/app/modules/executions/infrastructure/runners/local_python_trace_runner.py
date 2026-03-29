from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.modules.executions.domain.trace import (
    TraceExecutionCommand,
    TraceExecutionResult,
    TraceStep,
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
            return TraceExecutionResult(
                status="failed",
                stdout="",
                stderr="",
                error_message=f"{command.language} 언어는 아직 지원하지 않습니다.",
                steps=[],
            )

        with tempfile.TemporaryDirectory(prefix="codeviz_runner_") as temp_dir:
            temp_path = Path(temp_dir)
            source_path = temp_path / "user_code.py"
            result_path = temp_path / "result.json"

            try:
                source_path.write_text(command.source_code, encoding="utf-8")
            except UnicodeEncodeError:
                return TraceExecutionResult(
                    status="failed",
                    stdout="",
                    stderr="소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                    error_message="소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                    steps=[],
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
                return TraceExecutionResult(
                    status="timeout",
                    stdout="",
                    stderr="",
                    error_message="코드 실행 시간이 제한을 초과했습니다.",
                    steps=[],
                )

            if not result_path.exists():
                message = self._decode_output(completed.stderr).strip() or "실행 결과를 생성하지 못했습니다."
                return TraceExecutionResult(
                    status="failed",
                    stdout="",
                    stderr=message,
                    error_message=message,
                    steps=[],
                )

            payload = json.loads(result_path.read_text(encoding="utf-8"))
            stderr_text = payload["stderr"]
            completed_stderr = self._decode_output(completed.stderr).strip()
            if completed_stderr:
                stderr_text = "\n".join(filter(None, [stderr_text, completed_stderr]))

            return TraceExecutionResult(
                status=payload["status"],
                stdout=payload["stdout"],
                stderr=stderr_text,
                error_message=payload["error_message"],
                steps=[TraceStep(**step) for step in payload["steps"]],
            )

    def _decode_output(self, output: bytes | str | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="backslashreplace")
        return output
