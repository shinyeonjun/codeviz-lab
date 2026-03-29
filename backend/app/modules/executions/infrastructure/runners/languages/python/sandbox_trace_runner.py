import io
import json
import os
import sys
import tempfile
import traceback
import types
from contextlib import redirect_stdout


def to_json_safe_text(value):
    if value is None:
        return None
    return value.encode("utf-8", errors="backslashreplace").decode("utf-8")


def sanitize(value, depth=0):
    if depth >= 3:
        return to_json_safe_text(repr(value))
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return to_json_safe_text(value)
    if isinstance(value, list):
        return [sanitize(item, depth + 1) for item in value[:20]]
    if isinstance(value, tuple):
        return {"type": "tuple", "items": [sanitize(item, depth + 1) for item in value[:20]]}
    if isinstance(value, set):
        return {"type": "set", "items": [sanitize(item, depth + 1) for item in list(value)[:20]]}
    if isinstance(value, dict):
        limited_items = list(value.items())[:20]
        return {to_json_safe_text(str(key)): sanitize(item, depth + 1) for key, item in limited_items}
    return to_json_safe_text(repr(value))


def make_json_safe(value):
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return to_json_safe_text(value)
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {
            to_json_safe_text(str(key)): make_json_safe(item)
            for key, item in value.items()
        }
    return to_json_safe_text(repr(value))


class BoundedStdout(io.TextIOBase):
    def __init__(self, *, max_chars: int) -> None:
        self._max_chars = max_chars
        self._buffer = io.StringIO()
        self.truncated = False

    def write(self, data):
        if self.truncated:
            return len(data)

        remaining = self._max_chars - self._buffer.tell()
        if remaining <= 0:
            self.truncated = True
            return len(data)

        self._buffer.write(data[:remaining])
        if len(data) > remaining:
            self.truncated = True
        return len(data)

    def getvalue(self):
        return self._buffer.getvalue()


def build_visible_locals(frame):
    return {
        key: sanitize(value)
        for key, value in frame.f_locals.items()
        if not key.startswith("__")
    }


def build_visible_globals(frame):
    visible_globals = {}

    for key, value in frame.f_globals.items():
        if key.startswith("__"):
            continue
        if isinstance(value, (types.ModuleType, type)):
            continue
        if callable(value):
            continue
        visible_globals[key] = sanitize(value)

    return visible_globals


def build_call_stack(frame, source_path):
    call_stack = []
    current_frame = frame

    while current_frame is not None:
        if current_frame.f_code.co_filename == source_path:
            call_stack.append(
                {
                    "function_name": current_frame.f_code.co_name,
                    "line_number": current_frame.f_lineno,
                    "locals_snapshot": build_visible_locals(current_frame),
                }
            )
        current_frame = current_frame.f_back

    call_stack.reverse()
    return call_stack


def build_step_metadata(locals_snapshot, globals_snapshot, call_stack):
    return {
        "localsCount": len(locals_snapshot),
        "globalsCount": len(globals_snapshot),
        "callStackDepth": len(call_stack),
    }


def append_step(steps, line_number, event_type, frame, stdout_buffer, source_path, error_message=None):
    locals_snapshot = build_visible_locals(frame)
    globals_snapshot = build_visible_globals(frame)
    call_stack = build_call_stack(frame, source_path)
    steps.append(
        {
            "line_number": line_number,
            "event_type": event_type,
            "function_name": frame.f_code.co_name,
            "locals_snapshot": locals_snapshot,
            "globals_snapshot": globals_snapshot,
            "stdout_snapshot": to_json_safe_text(stdout_buffer.getvalue()),
            "error_message": to_json_safe_text(error_message),
            "call_stack": call_stack,
            "metadata": build_step_metadata(locals_snapshot, globals_snapshot, call_stack),
        }
    )


def build_limit_message(stdout_buffer, trace_truncated):
    messages = []
    if stdout_buffer.truncated:
        messages.append("stdout 출력이 제한 길이를 초과해 잘렸습니다.")
    if trace_truncated:
        messages.append("trace 단계 수가 제한을 초과해 일부만 저장했습니다.")
    return "\n".join(messages)


def emit_payload(payload, result_path=None):
    safe_payload = {
        "status": payload["status"],
        "stdout": to_json_safe_text(payload["stdout"]),
        "stderr": to_json_safe_text(payload["stderr"]),
        "error_message": to_json_safe_text(payload["error_message"]),
        "steps": make_json_safe(payload["steps"]),
    }
    if result_path is not None:
        with open(result_path, "w", encoding="utf-8") as output_file:
            json.dump(safe_payload, output_file, ensure_ascii=False)
        return
    sys.stdout.write(json.dumps(safe_payload, ensure_ascii=False))


def main():
    max_trace_steps = int(os.environ.get("CODEVIZ_MAX_TRACE_STEPS", "0"))
    max_stdout_chars = int(os.environ.get("CODEVIZ_MAX_STDOUT_CHARS", "10000"))
    payload = json.loads(sys.stdin.read() or "{}")
    source_code = payload.get("source_code", "")
    stdin_text = payload.get("stdin", "")
    source_path = None
    result_path = None

    if len(sys.argv) >= 3:
        source_path = sys.argv[1]
        result_path = sys.argv[2]
    else:
        temp_dir = tempfile.TemporaryDirectory(prefix="codeviz_exec_")
        source_path = os.path.join(temp_dir.name, "user_code.py")
        try:
            with open(source_path, "w", encoding="utf-8") as source_file:
                source_file.write(source_code)
        except UnicodeEncodeError:
            emit_payload(
                {
                    "status": "failed",
                    "stdout": "",
                    "stderr": "소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                    "error_message": "소스 코드에 잘못된 유니코드 문자가 포함되어 있습니다.",
                    "steps": [],
                },
                result_path=result_path,
            )
            return

    stdout_buffer = BoundedStdout(max_chars=max_stdout_chars)
    steps = []
    status = "completed"
    stderr_text = ""
    error_message = None
    pending_line = None
    trace_truncated = False

    globals_dict = {"__name__": "__main__", "__file__": source_path}
    original_stdin = sys.stdin

    def tracer(frame, event, arg):
        nonlocal pending_line, trace_truncated
        if frame.f_code.co_filename != source_path:
            return tracer

        if max_trace_steps > 0 and len(steps) >= max_trace_steps:
            trace_truncated = True
            sys.settrace(None)
            return None

        if event == "line":
            if pending_line is not None:
                append_step(steps, pending_line, "line", frame, stdout_buffer, source_path)
            pending_line = frame.f_lineno
        elif event == "return":
            if pending_line is not None:
                append_step(steps, pending_line, "return", frame, stdout_buffer, source_path)
                pending_line = None
        elif event == "exception":
            exception_type, exception_value, _ = arg
            line_number = pending_line if pending_line is not None else frame.f_lineno
            append_step(
                steps,
                line_number,
                "exception",
                frame,
                stdout_buffer,
                source_path,
                f"{exception_type.__name__}: {exception_value}",
            )
            pending_line = None
        return tracer

    try:
        sys.stdin = io.StringIO(stdin_text)
        with open(source_path, "r", encoding="utf-8") as source_file:
            compiled = compile(source_file.read(), source_path, "exec")
        sys.settrace(tracer)
        with redirect_stdout(stdout_buffer):
            exec(compiled, globals_dict, globals_dict)
    except Exception as exc:
        status = "failed"
        error_message = str(exc)
        stderr_text = "".join(traceback.format_exception(exc))
    finally:
        sys.settrace(None)
        sys.stdin = original_stdin

    limit_message = build_limit_message(stdout_buffer, trace_truncated)
    if limit_message:
        stderr_text = "\n".join(filter(None, [stderr_text, limit_message]))

    payload = {
        "status": status,
        "stdout": stdout_buffer.getvalue(),
        "stderr": stderr_text,
        "error_message": error_message,
        "steps": steps,
    }
    emit_payload(payload, result_path=result_path)


if __name__ == "__main__":
    main()
