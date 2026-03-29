from subprocess import CompletedProcess, TimeoutExpired

from app.modules.executions.entities import TraceExecutionCommand
from app.modules.executions.infrastructure.runners.languages.c.docker_runner import (
    DockerCExecutionRunner,
)
from app.modules.executions.runners.docker_trace_runner import DockerTraceRunner


def test_docker_runner_builds_hardened_docker_command(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"status":"completed","stdout":"1\\n","stderr":"","error_message":null,"steps":[]}',
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", fake_run)

    runner = DockerTraceRunner(
        timeout_seconds=3,
        image="codeviz-python-sandbox:latest",
        memory_limit="256m",
        cpus="0.5",
        pids_limit=64,
        tmpfs_size="64m",
        max_trace_steps=500,
        max_stdout_chars=10000,
    )

    result = runner.run(
        TraceExecutionCommand(language="python", source_code="print(1)", stdin="")
    )

    assert result.status == "completed"
    command = captured["command"]
    assert "--network" in command and "none" in command
    assert "--read-only" in command
    assert "--cap-drop" in command and "ALL" in command
    assert "--security-opt" in command and "no-new-privileges" in command
    assert "--pids-limit" in command and "64" in command
    assert "--memory" in command and "256m" in command
    assert "--cpus" in command and "0.5" in command
    assert "--tmpfs" in command
    assert captured["kwargs"]["input"] != ""


def test_docker_runner_force_removes_container_on_timeout(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:2] == ["docker", "rm"]:
            return CompletedProcess(args=command, returncode=0, stdout="", stderr="")
        raise TimeoutExpired(cmd=command, timeout=5)

    monkeypatch.setattr("subprocess.run", fake_run)

    runner = DockerTraceRunner(
        timeout_seconds=3,
        image="codeviz-python-sandbox:latest",
        memory_limit="256m",
        cpus="0.5",
        pids_limit=64,
        tmpfs_size="64m",
        max_trace_steps=500,
        max_stdout_chars=10000,
    )

    result = runner.run(
        TraceExecutionCommand(language="python", source_code="while True:\n    pass", stdin="")
    )

    assert result.status == "timeout"
    assert any(command[:3] == ["docker", "rm", "-f"] for command in calls)


def test_c_docker_runner_uses_executable_tmpfs(monkeypatch):
    captured = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        return CompletedProcess(
            args=command,
            returncode=0,
            stdout=b'{"status":"completed","stdout":"6\\n","stderr":"","error_message":null,"steps":[]}',
            stderr=b"",
        )

    monkeypatch.setattr("subprocess.run", fake_run)

    runner = DockerCExecutionRunner(
        timeout_seconds=3,
        image="codeviz-c-sandbox:latest",
        memory_limit="256m",
        cpus="0.5",
        pids_limit=64,
        tmpfs_size="64m",
        max_trace_steps=500,
        max_stdout_chars=10000,
    )

    result = runner.run(
        TraceExecutionCommand(
            language="c",
            source_code='#include <stdio.h>\nint main(void){ printf("6\\n"); return 0; }\n',
            stdin="",
        )
    )

    assert result.status == "completed"
    tmpfs_index = captured["command"].index("--tmpfs") + 1
    assert "exec" in captured["command"][tmpfs_index]
