from __future__ import annotations

import json
import subprocess
import uuid

from app.modules.executions.domain.trace import (
    TraceExecutionCommand,
    TraceExecutionResult,
    TraceStep,
)


class DockerTraceRunner:
    def __init__(
        self,
        *,
        timeout_seconds: int,
        image: str,
        memory_limit: str,
        cpus: str,
        pids_limit: int,
        tmpfs_size: str,
        max_trace_steps: int,
        max_stdout_chars: int,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._image = image
        self._memory_limit = memory_limit
        self._cpus = cpus
        self._pids_limit = pids_limit
        self._tmpfs_size = tmpfs_size
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

        container_name = f"codeviz-runner-{uuid.uuid4().hex[:12]}"
        docker_command = self._build_command(container_name=container_name)
        try:
            payload = json.dumps(
                {
                    "source_code": command.source_code,
                    "stdin": command.stdin,
                },
                ensure_ascii=False,
            )
        except UnicodeEncodeError:
            return TraceExecutionResult(
                status="failed",
                stdout="",
                stderr="소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                error_message="소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                steps=[],
            )

        try:
            completed = subprocess.run(
                docker_command,
                input=payload.encode("utf-8"),
                capture_output=True,
                timeout=self._timeout_seconds + 2,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self._force_remove_container(container_name)
            return TraceExecutionResult(
                status="timeout",
                stdout="",
                stderr="",
                error_message="코드 실행 시간이 제한을 초과했습니다.",
                steps=[],
            )

        stdout_text = self._decode_output(completed.stdout)
        stderr_text = self._decode_output(completed.stderr)

        if completed.returncode != 0:
            message = stderr_text.strip() or "Docker 실행에 실패했습니다."
            return TraceExecutionResult(
                status="failed",
                stdout="",
                stderr=message,
                error_message=message,
                steps=[],
            )

        try:
            result_payload = json.loads(stdout_text)
        except json.JSONDecodeError:
            message = stderr_text.strip() or "Docker 실행 결과를 해석하지 못했습니다."
            return TraceExecutionResult(
                status="failed",
                stdout="",
                stderr=message,
                error_message=message,
                steps=[],
            )

        return TraceExecutionResult(
            status=result_payload["status"],
            stdout=result_payload["stdout"],
            stderr=result_payload["stderr"],
            error_message=result_payload["error_message"],
            steps=[TraceStep(**step) for step in result_payload["steps"]],
        )

    def _decode_output(self, output: bytes | str | None) -> str:
        if output is None:
            return ""
        if isinstance(output, bytes):
            return output.decode("utf-8", errors="backslashreplace")
        return output

    def _build_command(self, *, container_name: str) -> list[str]:
        return [
            "docker",
            "run",
            "--rm",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(self._pids_limit),
            "--memory",
            self._memory_limit,
            "--cpus",
            self._cpus,
            "--tmpfs",
            f"/tmp:rw,noexec,nosuid,size={self._tmpfs_size}",
            "--init",
            "-e",
            f"CODEVIZ_TIMEOUT_SECONDS={self._timeout_seconds}",
            "-e",
            f"CODEVIZ_MAX_TRACE_STEPS={self._max_trace_steps}",
            "-e",
            f"CODEVIZ_MAX_STDOUT_CHARS={self._max_stdout_chars}",
            "-i",
            self._image,
        ]

    def _force_remove_container(self, container_name: str) -> None:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            text=True,
            check=False,
        )
