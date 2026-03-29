from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.common.responses import success_response
from app.modules.auth.application.dependencies import get_optional_auth_context
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
    auth_context: AuthContext | None = Depends(get_optional_auth_context),
) -> dict[str, object]:
    try:
        execution = service.create_execution(
            payload,
            workspace_id=auth_context.workspace.id if auth_context is not None else None,
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
    service: ExecutionService = Depends(get_execution_service),
) -> None:
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
