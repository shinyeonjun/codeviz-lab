from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db_session
from app.modules.auth.application.services.auth_service import AuthService
from app.modules.auth.application.services.workspace_activity_service import WorkspaceActivityService
from app.modules.auth.domain.context import AuthContext
from app.modules.auth.infrastructure.persistence.repository import AuthRepository
from app.modules.exams.infrastructure.persistence.repository import ExamAttemptRepository
from app.modules.executions.infrastructure.persistence.repository import SqlAlchemyExecutionRepository


def get_auth_repository(session: Session = Depends(get_db_session)) -> AuthRepository:
    return AuthRepository(session=session)


def get_auth_service(repository: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(repository=repository)


def get_workspace_activity_service(
    session: Session = Depends(get_db_session),
) -> WorkspaceActivityService:
    return WorkspaceActivityService(
        execution_repository=SqlAlchemyExecutionRepository(session=session),
        exam_attempt_repository=ExamAttemptRepository(session=session),
    )


def get_optional_auth_context(
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthContext | None:
    session_token = request.cookies.get(settings.auth_cookie_name)
    return service.get_auth_context(session_token)
