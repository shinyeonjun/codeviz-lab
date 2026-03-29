from __future__ import annotations

import json

from app.modules.executions.domain.trace import TraceExecutionResult


def decode_process_output(output: bytes | str | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="backslashreplace")
    return output


def encode_runner_payload(*, source_code: str, stdin: str) -> bytes:
    return json.dumps(
        {
            "source_code": source_code,
            "stdin": stdin,
        },
        ensure_ascii=False,
    ).encode("utf-8")


def parse_trace_result_payload(
    *,
    language: str,
    stdout_text: str,
    stderr_text: str = "",
    invalid_payload_message: str,
) -> TraceExecutionResult:
    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError:
        return TraceExecutionResult.failure(
            language=language,
            message=invalid_payload_message,
            stderr=stderr_text.strip() or invalid_payload_message,
        )

    if not isinstance(payload, dict):
        return TraceExecutionResult.failure(
            language=language,
            message=invalid_payload_message,
            stderr=stderr_text.strip() or invalid_payload_message,
        )

    return TraceExecutionResult.from_payload(
        language=language,
        payload=payload,
        stderr_override=stderr_text.strip() or None,
    )
