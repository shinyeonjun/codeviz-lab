from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def to_safe_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="backslashreplace")
    return value.encode("utf-8", errors="backslashreplace").decode("utf-8")


def truncate_text(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit], True


def emit_payload(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def main() -> None:
    timeout_seconds = int(os.environ.get("CODEVIZ_TIMEOUT_SECONDS", "5"))
    max_stdout_chars = int(os.environ.get("CODEVIZ_MAX_STDOUT_CHARS", "10000"))
    payload = json.loads(sys.stdin.read() or "{}")
    source_code = str(payload.get("source_code", ""))
    stdin_text = str(payload.get("stdin", ""))

    try:
        safe_source_code = source_code.encode("utf-8", errors="strict").decode("utf-8")
    except UnicodeEncodeError:
        emit_payload(
            {
                "status": "failed",
                "stdout": "",
                "stderr": "소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                "error_message": "소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                "steps": [],
            }
        )
        return

    with tempfile.TemporaryDirectory(prefix="codeviz_c_exec_") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / "main.c"
        binary_path = temp_path / "main.out"

        source_path.write_text(safe_source_code, encoding="utf-8")

        try:
            compile_result = subprocess.run(
                ["gcc", "-std=c11", "-O2", str(source_path), "-o", str(binary_path)],
                capture_output=True,
                timeout=max(3, timeout_seconds),
                check=False,
            )
        except FileNotFoundError:
            emit_payload(
                {
                    "status": "failed",
                    "stdout": "",
                    "stderr": "gcc 컴파일러를 찾을 수 없습니다.",
                    "error_message": "gcc 컴파일러를 찾을 수 없습니다.",
                    "steps": [],
                }
            )
            return
        except subprocess.TimeoutExpired:
            emit_payload(
                {
                    "status": "timeout",
                    "stdout": "",
                    "stderr": "",
                    "error_message": "C 컴파일 시간이 제한을 초과했습니다.",
                    "steps": [],
                }
            )
            return

        compile_stderr = to_safe_text(compile_result.stderr).strip()
        if compile_result.returncode != 0:
            emit_payload(
                {
                    "status": "failed",
                    "stdout": "",
                    "stderr": compile_stderr,
                    "error_message": compile_stderr or "C 컴파일에 실패했습니다.",
                    "steps": [],
                }
            )
            return

        try:
            run_result = subprocess.run(
                [str(binary_path)],
                input=stdin_text.encode("utf-8"),
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            emit_payload(
                {
                    "status": "timeout",
                    "stdout": "",
                    "stderr": "",
                    "error_message": "코드 실행 시간이 제한을 초과했습니다.",
                    "steps": [],
                }
            )
            return

        stdout_text, stdout_truncated = truncate_text(to_safe_text(run_result.stdout), max_stdout_chars)
        stderr_text = to_safe_text(run_result.stderr)
        if stdout_truncated:
            stderr_text = "\n".join(filter(None, [stderr_text, "stdout 출력이 제한 길이를 초과해 잘렸습니다."]))

        if run_result.returncode != 0:
            emit_payload(
                {
                    "status": "failed",
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "error_message": stderr_text.strip() or "프로그램이 비정상 종료되었습니다.",
                    "steps": [],
                }
            )
            return

        emit_payload(
            {
                "status": "completed",
                "stdout": stdout_text,
                "stderr": stderr_text,
                "error_message": None,
                "steps": [],
            }
        )


if __name__ == "__main__":
    main()
