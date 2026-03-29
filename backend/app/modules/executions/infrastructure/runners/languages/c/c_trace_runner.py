from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
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


def compile_c_source(source_path: Path, binary_path: Path, *, timeout_seconds: int) -> tuple[bool, str]:
    try:
        compile_result = subprocess.run(
            [
                "gcc",
                "-std=c11",
                "-O0",
                "-g",
                "-fvar-tracking",
                "-fvar-tracking-assignments",
                str(source_path),
                "-o",
                str(binary_path),
            ],
            capture_output=True,
            timeout=max(3, timeout_seconds),
            check=False,
        )
    except FileNotFoundError:
        return False, "gcc 컴파일러를 찾을 수 없습니다."
    except subprocess.TimeoutExpired:
        return False, "C 컴파일 시간이 제한을 초과했습니다."

    compile_stderr = to_safe_text(compile_result.stderr).strip()
    if compile_result.returncode != 0:
        return False, compile_stderr or "C 컴파일에 실패했습니다."
    return True, ""


def run_compiled_binary(
    binary_path: Path,
    *,
    stdin_text: str,
    timeout_seconds: int,
    max_stdout_chars: int,
) -> dict[str, object]:
    try:
        run_result = subprocess.run(
            [str(binary_path)],
            input=stdin_text.encode("utf-8"),
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "stdout": "",
            "stderr": "",
            "error_message": "코드 실행 시간이 제한을 초과했습니다.",
            "steps": [],
        }

    stdout_text, stdout_truncated = truncate_text(to_safe_text(run_result.stdout), max_stdout_chars)
    stderr_text = to_safe_text(run_result.stderr)
    if stdout_truncated:
        stderr_text = "\n".join(filter(None, [stderr_text, "stdout 출력이 제한 길이를 초과해 잘렸습니다."]))

    if run_result.returncode != 0:
        return {
            "status": "failed",
            "stdout": stdout_text,
            "stderr": stderr_text,
            "error_message": stderr_text.strip() or "프로그램이 비정상 종료되었습니다.",
            "steps": [],
        }

    return {
        "status": "completed",
        "stdout": stdout_text,
        "stderr": stderr_text,
        "error_message": None,
        "steps": [],
    }


def detect_candidate_lines(source_code: str) -> list[int]:
    candidate_lines: list[int] = []
    in_block_comment = False

    for line_number, raw_line in enumerate(source_code.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue

        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue

        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue

        if stripped.startswith("//") or stripped.startswith("#"):
            continue

        if stripped in {"{", "}", "};"}:
            continue

        candidate_lines.append(line_number)

    return candidate_lines


def detect_global_names(source_code: str) -> list[str]:
    global_names: list[str] = []
    buffer = ""
    brace_depth = 0
    in_block_comment = False

    for raw_line in source_code.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue

        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue

        if stripped.startswith("//") or stripped.startswith("#"):
            continue

        if brace_depth == 0:
            buffer = f"{buffer} {stripped}".strip()
            if ";" in stripped:
                statements = buffer.split(";")
                for statement in statements[:-1]:
                    _collect_global_names_from_statement(statement, global_names)
                buffer = statements[-1].strip()

        open_braces = stripped.count("{")
        close_braces = stripped.count("}")

        brace_depth = max(0, brace_depth + open_braces - close_braces)
        if brace_depth > 0:
            buffer = ""

    return global_names


def _collect_global_names_from_statement(statement: str, global_names: list[str]) -> None:
    stripped = statement.strip()
    if not stripped:
        return
    if "(" in stripped:
        return
    if stripped.startswith(("typedef ", "struct ", "enum ", "union ")):
        return

    declaration_parts = [part.strip() for part in stripped.split(",")]
    for part in declaration_parts:
        match = re.search(r"([A-Za-z_]\w*)\s*(?:\[[^\]]*\])*\s*(?:=\s*.+)?$", part)
        if match is None:
            continue
        candidate = match.group(1)
        if candidate not in global_names:
            global_names.append(candidate)


def build_gdb_script(
    *,
    source_path: Path,
    stdin_path: Path,
    stdout_path: Path,
    stderr_path: Path,
    result_path: Path,
    candidate_lines: list[int],
    global_names: list[str],
    max_trace_steps: int,
    max_stdout_chars: int,
) -> str:
    breakpoints_json = json.dumps(candidate_lines)
    global_names_json = json.dumps(global_names)
    return textwrap.dedent(
        f"""
        set pagination off
        set confirm off
        set breakpoint pending on
        set print repeats 20
        set print elements 20
        set print pretty off
        python
        import json
        import pathlib
        import re
        import gdb

        SOURCE_PATH = {json.dumps(str(source_path))}
        STDIN_PATH = {json.dumps(str(stdin_path))}
        STDOUT_PATH = {json.dumps(str(stdout_path))}
        STDERR_PATH = {json.dumps(str(stderr_path))}
        RESULT_PATH = {json.dumps(str(result_path))}
        MAX_TRACE_STEPS = {max_trace_steps}
        MAX_STDOUT_CHARS = {max_stdout_chars}
        BREAKPOINT_LINES = json.loads({json.dumps(breakpoints_json)})
        GLOBAL_NAMES = json.loads({json.dumps(global_names_json)})
        TRACE_STEPS = []
        TRACE_TRUNCATED = False
        SIGNAL_MESSAGE = None
        EXIT_CODE = None

        INT_PATTERN = re.compile(r"^-?\\d+$")
        FLOAT_PATTERN = re.compile(r"^-?(?:\\d+\\.\\d*|\\d*\\.\\d+)(?:[eE][+-]?\\d+)?$")


        def to_safe_text(value):
            if value is None:
                return None
            return value.encode("utf-8", errors="backslashreplace").decode("utf-8")


        def truncate_text(value, limit):
            if len(value) <= limit:
                return value, False
            return value[:limit], True


        def split_top_level_items(text):
            items = []
            current = []
            depth = 0
            in_string = False
            escape = False

            for char in text:
                if escape:
                    current.append(char)
                    escape = False
                    continue

                if char == "\\\\":
                    current.append(char)
                    escape = True
                    continue

                if char == '"':
                    current.append(char)
                    in_string = not in_string
                    continue

                if not in_string:
                    if char == "{{":
                        depth += 1
                    elif char == "}}":
                        depth = max(0, depth - 1)
                    elif char == "," and depth == 0:
                        items.append("".join(current).strip())
                        current = []
                        continue

                current.append(char)

            if current:
                items.append("".join(current).strip())
            return [item for item in items if item]


        def parse_value(text):
            value = text.strip()
            if not value:
                return ""

            if value.startswith('"') and value.endswith('"'):
                return to_safe_text(value[1:-1])

            if value.startswith("'") and value.endswith("'") and len(value) >= 2:
                return to_safe_text(value[1:-1])

            if INT_PATTERN.match(value):
                try:
                    return int(value)
                except ValueError:
                    return to_safe_text(value)

            if FLOAT_PATTERN.match(value):
                try:
                    return float(value)
                except ValueError:
                    return to_safe_text(value)

            if value.startswith("{{") and value.endswith("}}"):
                inner = value[1:-1].strip()
                items = split_top_level_items(inner)
                return [parse_value(item) for item in items[:20]]

            return to_safe_text(value)


        def parse_locals_output(text):
            locals_snapshot = {{}}
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith("No locals.") or line.startswith("No arguments."):
                    continue
                if " = " not in line:
                    continue
                name, value = line.split(" = ", 1)
                locals_snapshot[to_safe_text(name.strip())] = parse_value(value)
            return locals_snapshot


        def parse_print_output(text):
            normalized = text.strip()
            if not normalized or " = " not in normalized:
                return None
            _, value = normalized.split(" = ", 1)
            return parse_value(value)


        def read_stdout_snapshot():
            stdout_text = pathlib.Path(STDOUT_PATH).read_text(encoding="utf-8", errors="backslashreplace") if pathlib.Path(STDOUT_PATH).exists() else ""
            stdout_text, _ = truncate_text(stdout_text, MAX_STDOUT_CHARS)
            return to_safe_text(stdout_text)


        def read_locals_snapshot():
            locals_snapshot = {{}}
            try:
                args_text = gdb.execute("info args", to_string=True)
                locals_snapshot.update(parse_locals_output(args_text))
            except gdb.error:
                pass
            try:
                locals_text = gdb.execute("info locals", to_string=True)
                locals_snapshot.update(parse_locals_output(locals_text))
            except gdb.error:
                pass
            return locals_snapshot


        def read_globals_snapshot():
            globals_snapshot = {{}}
            for name in GLOBAL_NAMES:
                try:
                    printed = gdb.execute(f"print {{name}}", to_string=True)
                except gdb.error:
                    continue
                parsed_value = parse_print_output(printed)
                if parsed_value is None:
                    continue
                globals_snapshot[to_safe_text(name)] = parsed_value
            return globals_snapshot


        def read_call_stack():
            try:
                backtrace_text = gdb.execute("bt", to_string=True)
            except gdb.error:
                return []

            frames = []
            for raw_line in backtrace_text.splitlines():
                line = raw_line.strip()
                if not line.startswith("#"):
                    continue

                line_number = None
                line_match = re.search(r":(\\d+)(?:\\s|$)", line)
                if line_match is not None:
                    try:
                        line_number = int(line_match.group(1))
                    except ValueError:
                        line_number = None

                name_match = re.search(
                    r"#\\d+\\s+(?:0x[0-9a-fA-F]+\\s+in\\s+)?([A-Za-z_][\\w]*)",
                    line,
                )
                function_name = name_match.group(1) if name_match is not None else "<unknown>"
                frames.append(
                    {{
                        "function_name": to_safe_text(function_name),
                        "line_number": line_number,
                        "locals_snapshot": {{}},
                    }}
                )

            frames.reverse()
            return frames


        def build_step_metadata(locals_snapshot, globals_snapshot, call_stack):
            return {{
                "localsCount": len(locals_snapshot),
                "globalsCount": len(globals_snapshot),
                "callStackDepth": len(call_stack),
            }}


        def disable_all_breakpoints():
            for breakpoint in gdb.breakpoints() or []:
                breakpoint.enabled = False


        class SourceLineBreakpoint(gdb.Breakpoint):
            def stop(self):
                global TRACE_TRUNCATED
                if MAX_TRACE_STEPS > 0 and len(TRACE_STEPS) >= MAX_TRACE_STEPS:
                    TRACE_TRUNCATED = True
                    disable_all_breakpoints()
                    return False

                frame = gdb.selected_frame()
                sal = frame.find_sal()
                locals_snapshot = read_locals_snapshot()
                globals_snapshot = read_globals_snapshot()
                call_stack = read_call_stack()
                TRACE_STEPS.append(
                    {{
                        "line_number": sal.line or 0,
                        "event_type": "line",
                        "function_name": to_safe_text(frame.name() or "<unknown>"),
                        "locals_snapshot": locals_snapshot,
                        "globals_snapshot": globals_snapshot,
                        "stdout_snapshot": read_stdout_snapshot(),
                        "error_message": None,
                        "call_stack": call_stack,
                        "metadata": build_step_metadata(locals_snapshot, globals_snapshot, call_stack),
                    }}
                )
                return False


        def on_stop(event):
            global SIGNAL_MESSAGE
            if isinstance(event, gdb.SignalEvent):
                SIGNAL_MESSAGE = f"프로그램이 시그널 {{event.stop_signal}} 로 중단되었습니다."


        def on_exit(event):
            global EXIT_CODE
            EXIT_CODE = getattr(event, "exit_code", None)


        gdb.events.stop.connect(on_stop)
        gdb.events.exited.connect(on_exit)

        for line_number in BREAKPOINT_LINES:
            try:
                SourceLineBreakpoint(f"{{SOURCE_PATH}}:{{line_number}}", internal=True)
            except gdb.error:
                continue
        end
        run < {stdin_path} > {stdout_path} 2> {stderr_path}
        python
        import json
        import pathlib

        stdout_text = pathlib.Path(STDOUT_PATH).read_text(encoding="utf-8", errors="backslashreplace") if pathlib.Path(STDOUT_PATH).exists() else ""
        stderr_text = pathlib.Path(STDERR_PATH).read_text(encoding="utf-8", errors="backslashreplace") if pathlib.Path(STDERR_PATH).exists() else ""

        stdout_text, stdout_truncated = truncate_text(stdout_text, MAX_STDOUT_CHARS)
        status = "completed"
        error_message = None

        if SIGNAL_MESSAGE:
            status = "failed"
            error_message = SIGNAL_MESSAGE
            stderr_text = "\\n".join(filter(None, [stderr_text, SIGNAL_MESSAGE]))
        elif EXIT_CODE not in (None, 0):
            status = "failed"
            error_message = f"프로그램이 종료 코드 {{EXIT_CODE}} 로 종료되었습니다."
            stderr_text = "\\n".join(filter(None, [stderr_text, error_message]))

        if stdout_truncated:
            stderr_text = "\\n".join(filter(None, [stderr_text, "stdout 출력이 제한 길이를 초과해 잘렸습니다."]))

        if TRACE_TRUNCATED:
            stderr_text = "\\n".join(filter(None, [stderr_text, "trace 단계 수가 제한을 초과해 일부만 저장했습니다."]))

        payload = {{
            "status": status,
            "stdout": to_safe_text(stdout_text),
            "stderr": to_safe_text(stderr_text),
            "error_message": to_safe_text(error_message),
            "steps": TRACE_STEPS,
        }}
        pathlib.Path(RESULT_PATH).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        end
        quit
        """
    ).strip()


def run_gdb_trace(
    *,
    binary_path: Path,
    source_path: Path,
    stdin_text: str,
    timeout_seconds: int,
    max_trace_steps: int,
    max_stdout_chars: int,
) -> dict[str, object]:
    try:
        gdb_version = subprocess.run(
            ["gdb", "--version"],
            capture_output=True,
            timeout=5,
            check=False,
        )
    except FileNotFoundError:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": "gdb 디버거를 찾을 수 없습니다.",
            "error_message": "gdb 디버거를 찾을 수 없습니다.",
            "steps": [],
        }

    if gdb_version.returncode != 0:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": "gdb 디버거 초기화에 실패했습니다.",
            "error_message": "gdb 디버거 초기화에 실패했습니다.",
            "steps": [],
        }

    with tempfile.TemporaryDirectory(prefix="codeviz_c_trace_") as trace_dir:
        trace_path = Path(trace_dir)
        stdin_path = trace_path / "stdin.txt"
        stdout_path = trace_path / "stdout.txt"
        stderr_path = trace_path / "stderr.txt"
        result_path = trace_path / "result.json"
        script_path = trace_path / "trace.gdb"
        source_text = source_path.read_text(encoding="utf-8")

        stdin_path.write_text(stdin_text, encoding="utf-8")
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        script_path.write_text(
            build_gdb_script(
                source_path=source_path,
                stdin_path=stdin_path,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                result_path=result_path,
                candidate_lines=detect_candidate_lines(source_text),
                global_names=detect_global_names(source_text),
                max_trace_steps=max_trace_steps,
                max_stdout_chars=max_stdout_chars,
            ),
            encoding="utf-8",
        )

        try:
            completed = subprocess.run(
                [
                    "gdb",
                    "--quiet",
                    "--nx",
                    "--batch",
                    "--command",
                    str(script_path),
                    str(binary_path),
                ],
                capture_output=True,
                timeout=timeout_seconds + 5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "stdout": "",
                "stderr": "",
                "error_message": "코드 실행 시간이 제한을 초과했습니다.",
                "steps": [],
            }

        if result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
            gdb_stderr = to_safe_text(completed.stderr).strip()
            if gdb_stderr and "warning:" not in gdb_stderr.lower():
                payload["stderr"] = "\n".join(filter(None, [str(payload.get("stderr", "")), gdb_stderr]))
                if payload.get("status") == "completed":
                    payload["status"] = "failed"
                    payload["error_message"] = gdb_stderr
            return payload

        message = to_safe_text(completed.stderr).strip() or "gdb trace 결과를 생성하지 못했습니다."
        return {
            "status": "failed",
            "stdout": "",
            "stderr": message,
            "error_message": message,
            "steps": [],
        }


def main() -> None:
    timeout_seconds = int(os.environ.get("CODEVIZ_TIMEOUT_SECONDS", "5"))
    max_trace_steps = int(os.environ.get("CODEVIZ_MAX_TRACE_STEPS", "0"))
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

        compiled, compile_message = compile_c_source(
            source_path,
            binary_path,
            timeout_seconds=timeout_seconds,
        )
        if not compiled:
            status = "timeout" if "제한을 초과" in compile_message else "failed"
            emit_payload(
                {
                    "status": status,
                    "stdout": "",
                    "stderr": "" if status == "timeout" else compile_message,
                    "error_message": compile_message,
                    "steps": [],
                }
            )
            return

        traced_payload = run_gdb_trace(
            binary_path=binary_path,
            source_path=source_path,
            stdin_text=stdin_text,
            timeout_seconds=timeout_seconds,
            max_trace_steps=max_trace_steps,
            max_stdout_chars=max_stdout_chars,
        )

        fallback_needed = traced_payload["status"] == "failed" and (
            "gdb" in str(traced_payload.get("error_message", "")).lower()
            or "ptrace" in str(traced_payload.get("stderr", "")).lower()
            or "operation not permitted" in str(traced_payload.get("stderr", "")).lower()
        )

        if fallback_needed:
            emit_payload(
                run_compiled_binary(
                    binary_path,
                    stdin_text=stdin_text,
                    timeout_seconds=timeout_seconds,
                    max_stdout_chars=max_stdout_chars,
                )
            )
            return

        emit_payload(traced_payload)


if __name__ == "__main__":
    main()
