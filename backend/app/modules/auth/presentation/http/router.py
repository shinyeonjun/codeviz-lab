from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response

from app.common.responses import success_response
from app.core.config import settings
from app.modules.auth.application.dependencies import (
    get_auth_service,
    get_optional_auth_context,
    get_workspace_activity_service,
)
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.workspace_activity_service import WorkspaceActivityService
from app.modules.auth.domain.context import AuthContext
from app.modules.auth.domain.exceptions import (
    AuthenticationRequiredError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.modules.auth.presentation.http.schemas import (
    LoginCreate,
    RegisterCreate,
    WorkspaceCreate,
    WorkspaceSelectCreate,
)

router = APIRouter()


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        max_age=settings.auth_session_ttl_days * 24 * 60 * 60,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_cookie_name,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
    )


@router.post("/guest/ensure")
def ensure_guest_session(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    state, token = service.ensure_guest_session(request.cookies.get(settings.auth_cookie_name))
    response = JSONResponse(content=success_response(state.model_dump(mode="json", by_alias=True)))
    if token is not None:
        _set_session_cookie(response, token)
    return response


@router.get("/me")
def read_auth_me(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> dict[str, object]:
    state = service.get_state(request.cookies.get(settings.auth_cookie_name))
    if state is None:
        return success_response(None)
    return success_response(state.model_dump(mode="json", by_alias=True))


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(
    payload: RegisterCreate,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    try:
        state, token = service.register(
            payload=payload,
            session_token=request.cookies.get(settings.auth_cookie_name),
        )
    except UserAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    response = JSONResponse(
        content=success_response(state.model_dump(mode="json", by_alias=True)),
        status_code=status.HTTP_201_CREATED,
    )
    _set_session_cookie(response, token)
    return response


@router.post("/login")
def login_user(
    payload: LoginCreate,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    try:
        state, token = service.login(
            payload=payload,
            session_token=request.cookies.get(settings.auth_cookie_name),
        )
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error

    response = JSONResponse(content=success_response(state.model_dump(mode="json", by_alias=True)))
    _set_session_cookie(response, token)
    return response


@router.post("/logout")
def logout_user(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    service.logout(request.cookies.get(settings.auth_cookie_name))
    response = JSONResponse(content=success_response(True))
    _clear_session_cookie(response)
    return response


@router.get("/workspaces")
def read_workspaces(
    context: AuthContext | None = Depends(get_optional_auth_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, object]:
    if context is None:
        raise HTTPException(status_code=401, detail="세션이 없습니다.")
    return success_response(
        [workspace.model_dump(mode="json", by_alias=True) for workspace in service.list_workspaces(context=context)]
    )


@router.get("/activity")
def read_workspace_activity(
    context: AuthContext | None = Depends(get_optional_auth_context),
    service: WorkspaceActivityService = Depends(get_workspace_activity_service),
) -> dict[str, object]:
    if context is None:
        raise HTTPException(status_code=401, detail="세션이 없습니다.")
    activity = service.read_activity(context=context)
    return success_response(activity.model_dump(mode="json", by_alias=True))


@router.post("/workspaces", status_code=status.HTTP_201_CREATED)
def create_workspace(
    payload: WorkspaceCreate,
    context: AuthContext | None = Depends(get_optional_auth_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, object]:
    if context is None:
        raise HTTPException(status_code=401, detail="세션이 없습니다.")
    try:
        state = service.create_workspace(context=context, payload=payload)
    except AuthenticationRequiredError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return success_response(state.model_dump(mode="json", by_alias=True))


@router.post("/workspaces/select")
def select_workspace(
    payload: WorkspaceSelectCreate,
    context: AuthContext | None = Depends(get_optional_auth_context),
    service: AuthService = Depends(get_auth_service),
) -> dict[str, object]:
    if context is None:
        raise HTTPException(status_code=401, detail="세션이 없습니다.")
    try:
        state = service.select_workspace(context=context, workspace_id=payload.workspace_id)
    except AuthenticationRequiredError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return success_response(state.model_dump(mode="json", by_alias=True))
