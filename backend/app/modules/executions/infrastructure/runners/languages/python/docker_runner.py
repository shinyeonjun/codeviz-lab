from __future__ import annotations

import subprocess
import uuid

from app.modules.executions.domain.trace import TraceExecutionCommand, TraceExecutionResult
from app.modules.executions.infrastructure.runners.shared import (
    decode_process_output,
    encode_runner_payload,
    parse_trace_result_payload,
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
            return TraceExecutionResult.unsupported_language(language=command.language)

        container_name = f"codeviz-runner-{uuid.uuid4().hex[:12]}"
        docker_command = self._build_command(container_name=container_name)
        try:
            payload = encode_runner_payload(source_code=command.source_code, stdin=command.stdin)
        except UnicodeEncodeError:
            return TraceExecutionResult.failure(
                language=command.language,
                message="소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
            )

        try:
            completed = subprocess.run(
                docker_command,
                input=payload,
                capture_output=True,
                timeout=self._timeout_seconds + 2,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self._force_remove_container(container_name)
            return TraceExecutionResult.timeout(language=command.language)

        stdout_text = decode_process_output(completed.stdout)
        stderr_text = decode_process_output(completed.stderr)

        if completed.returncode != 0:
            message = stderr_text.strip() or "Docker 실행에 실패했습니다."
            return TraceExecutionResult.failure(
                language=command.language,
                message=message,
            )

        return parse_trace_result_payload(
            language=command.language,
            stdout_text=stdout_text,
            stderr_text=stderr_text,
            invalid_payload_message="Docker 실행 결과를 해석하지 못했습니다.",
        )

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
