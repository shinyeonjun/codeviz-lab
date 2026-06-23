import asyncio
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.modules.executions.presentation.http import router as execution_router


pytestmark = pytest.mark.no_db


class FakeStreamManager:
    def __init__(self) -> None:
        self.connected: list[str] = []
        self.disconnected: list[str] = []

    async def connect(self, run_id, websocket):
        self.connected.append(run_id)

    def disconnect(self, run_id, websocket):
        self.disconnected.append(run_id)


class FakeWebSocket:
    cookies = {"codeviz_session": "session-token"}

    async def close(self, *, code, reason):
        self.close_code = code
        self.close_reason = reason


class FakeAuthService:
    def get_auth_context(self, session_token):
        return SimpleNamespace(user=SimpleNamespace(id="user-1"))


class FailingExecutionService:
    def get_execution(self, run_id, *, user_id):
        raise RuntimeError("snapshot failed")


def test_optional_openai_settings_strip_blank_values():
    settings = Settings(
        database_url="postgresql+psycopg://codeviz:codeviz@127.0.0.1:55433/codeviz",
        openai_api_key=" ",
        openai_project_id="",
        openai_organization_id="\t",
    )

    assert settings.openai_api_key is None
    assert settings.openai_project_id is None
    assert settings.openai_organization_id is None


def test_execution_stream_disconnects_when_snapshot_fails(monkeypatch):
    manager = FakeStreamManager()
    monkeypatch.setattr(execution_router, "execution_stream_manager", manager)

    with pytest.raises(RuntimeError):
        asyncio.run(
            execution_router.stream_execution(
                FakeWebSocket(),
                "run-1",
                auth_service=FakeAuthService(),
                service=FailingExecutionService(),
            )
        )

    assert manager.connected == ["run-1"]
    assert manager.disconnected == ["run-1"]
