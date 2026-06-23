from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


CLASS_PATTERN = re.compile(r"\b(?:public\s+)?class\s+([A-Za-z_]\w*)\b")
PUBLIC_CLASS_PATTERN = re.compile(r"\bpublic\s+class\s+([A-Za-z_]\w*)\b")
PROMPT_PATTERN = re.compile(r"(?:^|\n)(?:>|[A-Za-z_][\w-]*\[\d+\])\s$")
BREAKPOINT_PATTERN = re.compile(
    r'Breakpoint hit: "thread=[^"]+",\s+([A-Za-z_][\w$.]*)\(\), line=(\d+)'
)
WHERE_FRAME_PATTERN = re.compile(r"\[(\d+)\]\s+([A-Za-z_][\w$.]*)\s+\(([^:()]+):(\d+)\)")
LOCAL_VALUE_PATTERN = re.compile(r"^\s*([A-Za-z_]\w*)\s+=\s+(.+)$")
ARRAY_INSTANCE_PATTERN = re.compile(r"instance of .*\[[^\]]*\]")
JAVA_DECLARATION_TYPES = "int|long|short|float|double|boolean|char|String"
JAVA_COMMON_JDB_PATHS = (
    r"C:\Program Files\Java",
    r"C:\Program Files\Eclipse Adoptium",
    r"C:\Program Files\Microsoft\jdk",
    r"C:\Program Files\Android\openjdk",
)
NONDETERMINISTIC_TRACE_PATTERNS = (
    re.compile(r"\bMath\.random\s*\("),
    re.compile(r"\bnew\s+Random\s*\("),
    re.compile(r"\bRandom\s+\w+"),
    re.compile(r"\bSystem\.currentTimeMillis\s*\("),
    re.compile(r"\bSystem\.nanoTime\s*\("),
    re.compile(r"\bInstant\.now\s*\("),
    re.compile(r"\bLocalDate(?:Time)?\.now\s*\("),
    re.compile(r"\bUUID\.randomUUID\s*\("),
)


def to_safe_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="backslashreplace").replace("\r\n", "\n")
    return value.encode("utf-8", errors="backslashreplace").decode("utf-8").replace("\r\n", "\n")


def truncate_text(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit], True


def emit_payload(payload: dict[str, object]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def detect_main_class_name(source_code: str) -> str | None:
    public_match = PUBLIC_CLASS_PATTERN.search(source_code)
    if public_match is not None:
        return public_match.group(1)

    class_match = CLASS_PATTERN.search(source_code)
    if class_match is not None:
        return class_match.group(1)

    return None


def compile_java_source(source_path: Path, *, timeout_seconds: int) -> tuple[bool, str]:
    try:
        compile_result = subprocess.run(
            ["javac", "-g", "-encoding", "UTF-8", str(source_path)],
            cwd=source_path.parent,
            capture_output=True,
            timeout=max(3, timeout_seconds),
            check=False,
        )
    except FileNotFoundError:
        return False, "javac 컴파일러를 찾을 수 없습니다."
    except subprocess.TimeoutExpired:
        return False, "Java 컴파일 시간이 제한을 초과했습니다."

    compile_stderr = to_safe_text(compile_result.stderr).strip()
    if compile_result.returncode != 0:
        return False, compile_stderr or "Java 컴파일에 실패했습니다."
    return True, ""


def find_jdb_executable() -> str | None:
    configured_path = os.environ.get("CODEVIZ_JDB_PATH")
    if configured_path and Path(configured_path).exists():
        return configured_path

    discovered_path = shutil.which("jdb")
    if discovered_path:
        return discovered_path

    java_home = os.environ.get("JAVA_HOME")
    if java_home:
        java_home_path = Path(java_home) / "bin" / _jdb_filename()
        if java_home_path.exists():
            return str(java_home_path)

    javac_path = shutil.which("javac")
    if javac_path:
        sibling_path = Path(javac_path).with_name(_jdb_filename())
        if sibling_path.exists():
            return str(sibling_path)

    if os.name == "nt":
        for base_path in JAVA_COMMON_JDB_PATHS:
            base = Path(base_path)
            if not base.exists():
                continue
            candidates = sorted(base.glob("**/bin/jdb.exe"), reverse=True)
            if candidates:
                return str(candidates[0])

    return None


def _jdb_filename() -> str:
    return "jdb.exe" if os.name == "nt" else "jdb"


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
        if stripped.startswith(("//", "package ", "import ", "@")):
            continue
        if stripped in {"{", "}", "};"}:
            continue
        if re.match(r"(?:public\s+)?class\s+\w+", stripped):
            continue
        if re.search(r"\b(?:if|for|while|switch|return)\b", stripped) or ";" in stripped:
            candidate_lines.append(line_number)

    return candidate_lines


def detect_java_variable_names(source_code: str) -> tuple[set[str], set[str]]:
    sanitized = _strip_java_comments(source_code)
    array_names: set[str] = set()
    scalar_names: set[str] = set()

    array_patterns = [
        re.compile(rf"\b(?:{JAVA_DECLARATION_TYPES})\s*(?:\[\s*\])+\s+([A-Za-z_]\w*)"),
        re.compile(rf"\b(?:{JAVA_DECLARATION_TYPES})\s+([A-Za-z_]\w*)\s*(?:\[\s*\])+"),
    ]
    for pattern in array_patterns:
        array_names.update(pattern.findall(sanitized))
    array_names.discard("args")

    scalar_pattern = re.compile(
        rf"\b(?:{JAVA_DECLARATION_TYPES})\s+([A-Za-z_]\w*)\s*(?==|;|,|\))"
    )
    for name in scalar_pattern.findall(sanitized):
        if name not in array_names and name != "args":
            scalar_names.add(name)

    return array_names, scalar_names


def should_skip_trace_for_consistency(source_code: str) -> bool:
    sanitized = _strip_java_comments(source_code)
    return any(pattern.search(sanitized) is not None for pattern in NONDETERMINISTIC_TRACE_PATTERNS)


def _strip_java_comments(source_code: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", "", source_code, flags=re.S)
    return re.sub(r"//.*?$", "", without_block_comments, flags=re.M)


def run_java_class(
    *,
    working_dir: Path,
    main_class_name: str,
    stdin_text: str,
    timeout_seconds: int,
    max_stdout_chars: int,
) -> dict[str, object]:
    try:
        run_result = subprocess.run(
            [
                "java",
                "-Dfile.encoding=UTF-8",
                "-Xmx128m",
                "-cp",
                str(working_dir),
                main_class_name,
            ],
            input=stdin_text.encode("utf-8"),
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return {
            "status": "failed",
            "stdout": "",
            "stderr": "java 실행 파일을 찾을 수 없습니다.",
            "error_message": "java 실행 파일을 찾을 수 없습니다.",
            "steps": [],
        }
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


class JdbBuffer:
    def __init__(self, process: subprocess.Popen[str]) -> None:
        self._process = process
        self._chunks: list[str] = []
        self._cursor = 0
        self._lock = threading.Lock()
        self._reader = threading.Thread(target=self._read_stdout, daemon=True)
        self._reader.start()

    def _read_stdout(self) -> None:
        if self._process.stdout is None:
            return
        while True:
            chunk = self._process.stdout.read(1)
            if chunk == "":
                return
            with self._lock:
                self._chunks.append(chunk)

    def read_until_prompt(self, *, timeout_seconds: float) -> str:
        return self._read_until(
            lambda chunk: PROMPT_PATTERN.search(chunk) is not None,
            timeout_seconds=timeout_seconds,
        )

    def read_until_break_or_exit(self, *, timeout_seconds: float) -> str:
        return self._read_until(
            lambda chunk: (
                "Breakpoint hit:" in chunk
                or "The application exited" in chunk
                or "The application has been disconnected" in chunk
                or "VM has been disconnected" in chunk
            ),
            timeout_seconds=timeout_seconds,
        )

    def _read_until(self, predicate, *, timeout_seconds: float) -> str:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            chunk = self._pending_chunk()
            if predicate(chunk):
                return self.flush()
            if self._process.poll() is not None:
                return self.flush()
            time.sleep(0.03)
        return self.flush()

    def _pending_chunk(self) -> str:
        with self._lock:
            return "".join(self._chunks)[self._cursor :]

    def flush(self) -> str:
        with self._lock:
            text = "".join(self._chunks)
            chunk = text[self._cursor :]
            self._cursor = len(text)
            return chunk


def run_jdb_trace(
    *,
    working_dir: Path,
    main_class_name: str,
    source_code: str,
    timeout_seconds: int,
    max_trace_steps: int,
) -> tuple[list[dict[str, object]], str | None]:
    if source_code.strip() == "":
        return [], None

    jdb_path = find_jdb_executable()
    if jdb_path is None:
        return [], "jdb 디버거를 찾을 수 없어 Java trace를 생략했습니다."

    candidate_lines = detect_candidate_lines(source_code)
    if not candidate_lines:
        return [], None

    array_names, _ = detect_java_variable_names(source_code)
    command_timeout = max(3, timeout_seconds)

    for attempt_index in range(2):
        trace_steps: list[dict[str, object]] = []
        try:
            process = subprocess.Popen(
                [jdb_path, "-classpath", str(working_dir), main_class_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="backslashreplace",
                bufsize=0,
            )
        except OSError as error:
            return [], f"jdb 디버거 실행에 실패했습니다: {error}"

        buffer = JdbBuffer(process)

        def send(command: str) -> None:
            if process.stdin is None:
                return
            process.stdin.write(f"{command}\n")
            process.stdin.flush()

        try:
            buffer.read_until_prompt(timeout_seconds=command_timeout)
            for line_number in candidate_lines:
                send(f"stop at {main_class_name}:{line_number}")
                buffer.read_until_prompt(timeout_seconds=command_timeout)

            send("run")
            event_chunk = buffer.read_until_break_or_exit(timeout_seconds=timeout_seconds + 3)

            while "Breakpoint hit:" in event_chunk:
                if max_trace_steps > 0 and len(trace_steps) >= max_trace_steps:
                    break

                step = _build_jdb_step(
                    event_chunk=event_chunk,
                    send=send,
                    buffer=buffer,
                    array_names=array_names,
                    timeout_seconds=command_timeout,
                )
                if step is not None:
                    trace_steps.append(step)

                send("cont")
                event_chunk = buffer.read_until_break_or_exit(timeout_seconds=timeout_seconds + 3)

        finally:
            if process.poll() is None:
                try:
                    send("quit")
                    process.wait(timeout=2)
                except (OSError, subprocess.TimeoutExpired):
                    process.kill()

        if trace_steps or attempt_index == 1:
            return trace_steps, None
        time.sleep(0.1)

    return [], None


def _build_jdb_step(
    *,
    event_chunk: str,
    send,
    buffer: JdbBuffer,
    array_names: set[str],
    timeout_seconds: float,
) -> dict[str, object] | None:
    breakpoint_match = BREAKPOINT_PATTERN.search(event_chunk)
    if breakpoint_match is None:
        return None

    function_name = breakpoint_match.group(1).split(".")[-1]
    line_number = int(breakpoint_match.group(2))

    send("locals")
    locals_chunk = buffer.read_until_prompt(timeout_seconds=timeout_seconds)
    locals_snapshot, array_refs = _parse_jdb_locals(locals_chunk)

    for array_name in sorted(array_names | array_refs):
        if array_name not in array_refs:
            continue
        array_value = _read_jdb_array(
            variable_name=array_name,
            send=send,
            buffer=buffer,
            timeout_seconds=timeout_seconds,
        )
        if array_value is not None:
            locals_snapshot[array_name] = array_value

    send("where")
    where_chunk = buffer.read_until_prompt(timeout_seconds=timeout_seconds)
    call_stack = _parse_jdb_where(where_chunk)

    return {
        "line_number": line_number,
        "event_type": "line",
        "function_name": function_name,
        "locals_snapshot": locals_snapshot,
        "globals_snapshot": {},
        "stdout_snapshot": "",
        "error_message": None,
        "call_stack": call_stack,
        "metadata": {
            "localsCount": len(locals_snapshot),
            "globalsCount": 0,
            "callStackDepth": len(call_stack),
            "debugger": "jdb",
        },
    }


def _parse_jdb_locals(text: str) -> tuple[dict[str, object], set[str]]:
    locals_snapshot: dict[str, object] = {}
    array_refs: set[str] = set()

    for raw_line in text.splitlines():
        line = _strip_jdb_prompt(raw_line)
        match = LOCAL_VALUE_PATTERN.match(line)
        if match is None:
            continue
        name, value_text = match.group(1), match.group(2).strip()
        if name == "args":
            continue
        if ARRAY_INSTANCE_PATTERN.search(value_text):
            array_refs.add(name)
            continue
        parsed_value = _parse_java_scalar(value_text)
        if parsed_value is not None:
            locals_snapshot[name] = parsed_value

    return locals_snapshot, array_refs


def _read_jdb_array(
    *,
    variable_name: str,
    send,
    buffer: JdbBuffer,
    timeout_seconds: float,
) -> object | None:
    send(f"dump {variable_name}")
    dump_chunk = buffer.read_until_prompt(timeout_seconds=timeout_seconds)
    value = _parse_jdb_dump_array(dump_chunk)
    if value is not None and not _is_array_reference_list(value):
        return value

    send(f"print {variable_name}.length")
    length_chunk = buffer.read_until_prompt(timeout_seconds=timeout_seconds)
    length = _parse_jdb_printed_int(length_chunk)
    if length is None:
        return value

    rows: list[object] = []
    for index in range(min(length, 20)):
        send(f"dump {variable_name}[{index}]")
        row_chunk = buffer.read_until_prompt(timeout_seconds=timeout_seconds)
        row_value = _parse_jdb_dump_array(row_chunk)
        if row_value is None:
            return value
        rows.append(row_value)
    return rows


def _parse_jdb_where(text: str) -> list[dict[str, object]]:
    frames: list[dict[str, object]] = []
    for raw_line in text.splitlines():
        line = _strip_jdb_prompt(raw_line)
        match = WHERE_FRAME_PATTERN.search(line)
        if match is None:
            continue
        frames.append(
            {
                "function_name": match.group(2).split(".")[-1],
                "line_number": int(match.group(4)),
                "locals_snapshot": {},
            }
        )
    frames.reverse()
    return frames


def _parse_jdb_dump_array(text: str) -> object | None:
    match = re.search(r"=\s*\{(?P<body>.*?)\}", text, flags=re.S)
    if match is None:
        return None
    body = match.group("body").strip()
    if not body:
        return []
    values: list[object] = []
    for item in _split_top_level_items(body):
        if item.startswith("instance of "):
            values.append(item)
        else:
            values.append(_parse_java_scalar(item.strip()))
    return values


def _parse_jdb_printed_int(text: str) -> int | None:
    match = re.search(r"=\s*(-?\d+)", text)
    if match is None:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _parse_java_scalar(value_text: str) -> object | None:
    value = value_text.strip().rstrip(";")
    if not value or value == "null":
        return None
    if value in {"true", "false"}:
        return value == "true"
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            return value
    if re.fullmatch(r"-?(?:\d+\.\d*|\d*\.\d+)(?:[eE][+-]?\d+)?", value):
        try:
            return float(value)
        except ValueError:
            return value
    if value.startswith("instance of "):
        return None
    return value


def _split_top_level_items(text: str) -> list[str]:
    return [item.strip() for item in text.replace("\n", " ").split(",") if item.strip()]


def _strip_jdb_prompt(line: str) -> str:
    return re.sub(r"^\s*(?:>|[A-Za-z_][\w-]*\[\d+\])\s*", "", line).strip()


def _is_array_reference_list(value: object) -> bool:
    return isinstance(value, list) and any(
        isinstance(item, str) and item.startswith("instance of ") for item in value
    )


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

    main_class_name = detect_main_class_name(safe_source_code)
    if main_class_name is None:
        emit_payload(
            {
                "status": "failed",
                "stdout": "",
                "stderr": "Java 코드는 main 메서드를 가진 class를 포함해야 합니다.",
                "error_message": "Java 코드는 main 메서드를 가진 class를 포함해야 합니다.",
                "steps": [],
            }
        )
        return

    with tempfile.TemporaryDirectory(prefix="codeviz_java_exec_") as temp_dir:
        temp_path = Path(temp_dir)
        source_path = temp_path / f"{main_class_name}.java"
        source_path.write_text(safe_source_code, encoding="utf-8")

        compiled, compile_message = compile_java_source(
            source_path,
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

        run_payload = run_java_class(
            working_dir=temp_path,
            main_class_name=main_class_name,
            stdin_text=stdin_text,
            timeout_seconds=timeout_seconds,
            max_stdout_chars=max_stdout_chars,
        )
        if run_payload["status"] != "completed":
            emit_payload(run_payload)
            return

        trace_steps: list[dict[str, object]] = []
        trace_warning: str | None = None
        if stdin_text:
            trace_warning = "stdin을 사용하는 Java 코드는 현재 실행 결과만 수집하고 trace는 생략합니다."
        elif should_skip_trace_for_consistency(safe_source_code):
            trace_warning = (
                "난수/시간처럼 실행마다 값이 달라질 수 있는 Java 코드는 "
                "stdout과 trace 불일치를 막기 위해 trace를 생략합니다."
            )
        else:
            trace_steps, trace_warning = run_jdb_trace(
                working_dir=temp_path,
                main_class_name=main_class_name,
                source_code=safe_source_code,
                timeout_seconds=timeout_seconds,
                max_trace_steps=max_trace_steps,
            )

        run_payload["steps"] = trace_steps
        if trace_warning and not trace_steps:
            run_payload["stderr"] = "\n".join(filter(None, [str(run_payload.get("stderr", "")), trace_warning]))
        emit_payload(run_payload)


if __name__ == "__main__":
    main()
