from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.common.responses import success_response
from app.core.config import settings
from app.modules.auth.application.dependencies import get_auth_service, get_required_auth_context
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.domain.context import AuthContext
from app.modules.executions.application.dependencies import get_execution_service
from app.modules.executions.application.services.execution_service import ExecutionService
from app.modules.executions.domain.exceptions import ExecutionInputLimitError
from app.modules.executions.domain.exceptions import ExecutionNotFoundError
from app.modules.executions.presentation.http.schemas import ExecutionCreate
from app.modules.executions.presentation.websocket.manager import execution_stream_manager

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_execution(
    payload: ExecutionCreate,
    service: ExecutionService = Depends(get_execution_service),
    auth_context: AuthContext = Depends(get_required_auth_context),
) -> dict[str, object]:
    try:
        execution = service.create_execution(
            payload,
            workspace_id=auth_context.workspace.id,
        )
    except ExecutionInputLimitError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    await execution_stream_manager.broadcast(
        execution.run_id,
        {"type": "execution.completed", "data": execution.model_dump(mode="json", by_alias=True)},
    )
    return success_response(execution.model_dump(mode="json", by_alias=True))


@router.get("/{run_id}")
def read_execution(
    run_id: str,
    _: AuthContext = Depends(get_required_auth_context),
    service: ExecutionService = Depends(get_execution_service),
) -> dict[str, object]:
    try:
        execution = service.get_execution(run_id)
    except ExecutionNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return success_response(execution.model_dump(mode="json", by_alias=True))


@router.websocket("/{run_id}/stream")
async def stream_execution(
    websocket: WebSocket,
    run_id: str,
    auth_service: AuthService = Depends(get_auth_service),
    service: ExecutionService = Depends(get_execution_service),
) -> None:
    session_token = websocket.cookies.get(settings.auth_cookie_name)
    auth_context = auth_service.get_auth_context(session_token)
    if auth_context is None or auth_context.user is None:
        await websocket.close(code=4401, reason="로그인이 필요합니다.")
        return

    await execution_stream_manager.connect(run_id, websocket)
    try:
        try:
            execution = service.get_execution(run_id)
            await websocket.send_json(
                {"type": "execution.snapshot", "data": execution.model_dump(mode="json", by_alias=True)}
            )
        except ExecutionNotFoundError:
            await websocket.send_json({"type": "execution.not_found", "run_id": run_id})

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        execution_stream_manager.disconnect(run_id, websocket)
