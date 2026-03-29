from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.domain.context import AuthContext
from app.modules.auth.infrastructure.persistence.repository import AuthRepository


def get_auth_repository(session: Session = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session=session)


def get_auth_service(repository: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(repository=repository)


def get_optional_auth_context(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthContext | None:
    session_token = request.cookies.get(settings.auth_cookie_name)
    return service.get_auth_context(session_token)


def get_required_auth_context(
    context: AuthContext | None = Depends(get_optional_auth_context),
) -> AuthContext:
    if context is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return context
