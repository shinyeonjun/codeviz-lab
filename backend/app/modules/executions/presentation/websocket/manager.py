from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class ExecutionStreamManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[run_id].add(websocket)

    def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        self._connections[run_id].discard(websocket)
        if not self._connections[run_id]:
            self._connections.pop(run_id, None)

    async def broadcast(self, run_id: str, payload: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []
        for websocket in self._connections.get(run_id, set()):
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(run_id, websocket)


execution_stream_manager = ExecutionStreamManager()
