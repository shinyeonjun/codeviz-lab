from __future__ import annotations

from app.core.config import settings
from app.modules.auth.domain.context import AuthContext
from app.modules.auth.domain.exceptions import InvalidCredentialsError, UserAlreadyExistsError
from app.modules.auth.domain.security import (
    generate_session_token,
    hash_password,
    hash_session_token,
    verify_password,
)
from app.modules.auth.infrastructure.persistence.models import AuthSession
from app.modules.auth.infrastructure.persistence.repository import AuthRepository
from app.modules.auth.presentation.http.schemas import (
    AuthSessionRead,
    AuthUserRead,
    LoginCreate,
    RegisterCreate,
)


class AuthService:
    def __init__(self, *, repository: AuthRepository) -> None:
        self._repository = repository

    def register(
        self,
        *,
        payload: RegisterCreate,
        session_token: str | None,
    ) -> tuple[AuthSessionRead, str]:
        if self._repository.get_user_by_email(payload.email) is not None:
            raise UserAlreadyExistsError(str(payload.email))

        user = self._repository.create_user(
            email=str(payload.email),
            password_hash=hash_password(payload.password),
            name=payload.name,
        )
        workspace = self._repository.create_workspace(
            owner_user_id=user.id,
            title=f"{payload.name}의 기본 공간",
            is_guest=False,
        )
        raw_token = session_token or generate_session_token()
        auth_session = self._repository.create_session(
            token_hash=hash_session_token(raw_token),
            user_id=user.id,
            workspace_id=workspace.id,
            ttl_days=settings.auth_session_ttl_days,
        )
        return self._build_state_from_session(auth_session), raw_token

    def login(
        self,
        *,
        payload: LoginCreate,
        session_token: str | None,
    ) -> tuple[AuthSessionRead, str]:
        user = self._repository.get_user_by_email(str(payload.email))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError()

        workspaces = self._repository.get_user_workspaces(user.id)
        if not workspaces:
            workspace = self._repository.create_workspace(
                owner_user_id=user.id,
                title=f"{user.name}의 기본 공간",
                is_guest=False,
            )
            workspaces = [workspace]

        existing_context = self.get_auth_context(session_token)
        if existing_context is not None:
            self._repository.delete_session(existing_context.session)

        raw_token = generate_session_token()
        auth_session = self._repository.create_session(
            token_hash=hash_session_token(raw_token),
            user_id=user.id,
            workspace_id=workspaces[0].id,
            ttl_days=settings.auth_session_ttl_days,
        )
        return self._build_state_from_session(auth_session), raw_token

    def logout(self, session_token: str | None) -> None:
        context = self.get_auth_context(session_token)
        if context is None:
            return
        self._repository.delete_session(context.session)

    def get_auth_context(self, session_token: str | None) -> AuthContext | None:
        if not session_token:
            return None
        auth_session = self._repository.get_session_by_token_hash(hash_session_token(session_token))
        if auth_session is None or auth_session.user is None:
            return None
        return AuthContext(
            session=auth_session,
            workspace=auth_session.workspace,
            user=auth_session.user,
        )

    def get_state(self, session_token: str | None) -> AuthSessionRead | None:
        context = self.get_auth_context(session_token)
        if context is None:
            return None
        return self._build_state(context)

    def _build_state_from_session(self, auth_session: AuthSession) -> AuthSessionRead:
        return self._build_state(
            AuthContext(
                session=auth_session,
                workspace=auth_session.workspace,
                user=auth_session.user,
            )
        )

    def _build_state(self, context: AuthContext) -> AuthSessionRead:
        return AuthSessionRead(
            is_authenticated=context.user is not None,
            user=self._to_user_read(context.user) if context.user is not None else None,
        )

    def _to_user_read(self, user) -> AuthUserRead:
        return AuthUserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
        )
