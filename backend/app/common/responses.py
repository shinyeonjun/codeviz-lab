from typing import Any


def success_response(data: Any, *, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    response: dict[str, Any] = {"status": "success", "data": data}
    if meta is not None:
        response["meta"] = meta
    return response

