from __future__ import annotations

from app.core.config import settings
from app.modules.auth.domain.context import AuthContext
from app.modules.auth.domain.exceptions import (
    AuthenticationRequiredError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
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
    WorkspaceCreate,
    WorkspaceRead,
)


class AuthService:
    def __init__(self, *, repository: AuthRepository) -> None:
        self._repository = repository

    def ensure_guest_session(self, session_token: str | None) -> tuple[AuthSessionRead, str | None]:
        context = self.get_auth_context(session_token)
        if context is not None:
            return self._build_state(context), None

        raw_token = generate_session_token()
        auth_session = self._repository.create_guest_session(
            token_hash=hash_session_token(raw_token),
            ttl_days=settings.auth_session_ttl_days,
        )
        return self._build_state_from_session(auth_session), raw_token

    def register(
        self,
        *,
        payload: RegisterCreate,
        session_token: str | None,
    ) -> tuple[AuthSessionRead, str]:
        if self._repository.get_user_by_email(payload.email) is not None:
            raise UserAlreadyExistsError(str(payload.email))

        hashed_password = hash_password(payload.password)
        user = self._repository.create_user(
            email=str(payload.email),
            password_hash=hashed_password,
            name=payload.name,
        )

        existing_context = self.get_auth_context(session_token)
        workspace_title = f"{payload.name}의 작업공간"

        if existing_context is not None and existing_context.user is None:
            auth_session = self._repository.attach_guest_session_to_user(
                auth_session=existing_context.session,
                user=user,
                workspace_title=workspace_title,
                ttl_days=settings.auth_session_ttl_days,
            )
            return self._build_state_from_session(auth_session), session_token or generate_session_token()

        workspace = self._repository.create_workspace(
            owner_user_id=user.id,
            title=workspace_title,
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
                title=f"{user.name}의 작업공간",
                is_guest=False,
            )
            workspaces = [workspace]

        existing_context = self.get_auth_context(session_token)
        if existing_context is not None:
            auth_session = self._repository.replace_session_user(
                auth_session=existing_context.session,
                user_id=user.id,
                workspace_id=workspaces[0].id,
                ttl_days=settings.auth_session_ttl_days,
            )
            return self._build_state_from_session(auth_session), session_token or generate_session_token()

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
        if auth_session is None:
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

    def list_workspaces(self, *, context: AuthContext) -> list[WorkspaceRead]:
        if context.user is None:
            return [self._to_workspace_read(context.workspace)]

        return [
            self._to_workspace_read(workspace)
            for workspace in self._repository.get_user_workspaces(context.user.id)
        ]

    def create_workspace(self, *, context: AuthContext, payload: WorkspaceCreate) -> AuthSessionRead:
        if context.user is None:
            raise AuthenticationRequiredError()

        workspace = self._repository.create_workspace(
            owner_user_id=context.user.id,
            title=payload.title,
            is_guest=False,
        )
        auth_session = self._repository.switch_workspace(
            auth_session=context.session,
            workspace_id=workspace.id,
        )
        return self._build_state_from_session(auth_session)

    def select_workspace(self, *, context: AuthContext, workspace_id: str) -> AuthSessionRead:
        if context.user is None:
            if context.workspace.id != workspace_id:
                raise AuthenticationRequiredError()
            return self._build_state(context)

        allowed_workspace = next(
            (workspace for workspace in self._repository.get_user_workspaces(context.user.id) if workspace.id == workspace_id),
            None,
        )
        if allowed_workspace is None:
            raise AuthenticationRequiredError()

        auth_session = self._repository.switch_workspace(
            auth_session=context.session,
            workspace_id=workspace_id,
        )
        return self._build_state_from_session(auth_session)

    def _build_state_from_session(self, auth_session: AuthSession) -> AuthSessionRead:
        return self._build_state(
            AuthContext(
                session=auth_session,
                workspace=auth_session.workspace,
                user=auth_session.user,
            )
        )

    def _build_state(self, context: AuthContext) -> AuthSessionRead:
        if context.user is None:
            workspaces = [self._to_workspace_read(context.workspace)]
        else:
            workspaces = [
                self._to_workspace_read(workspace)
                for workspace in self._repository.get_user_workspaces(context.user.id)
            ]

        return AuthSessionRead(
            is_authenticated=context.user is not None,
            is_guest=context.user is None,
            user=self._to_user_read(context.user) if context.user is not None else None,
            current_workspace=self._to_workspace_read(context.workspace),
            workspaces=workspaces,
        )

    def _to_workspace_read(self, workspace) -> WorkspaceRead:
        return WorkspaceRead(
            id=workspace.id,
            title=workspace.title,
            is_guest=workspace.is_guest,
            created_at=workspace.created_at,
        )

    def _to_user_read(self, user) -> AuthUserRead:
        return AuthUserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
        )
