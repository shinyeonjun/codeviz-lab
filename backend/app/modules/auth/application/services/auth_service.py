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
from app.modules.auth.infrastructure.persistence.models import AuthSession, User
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
        self._delete_existing_session(session_token)
        return self._issue_session_for_user(user=user)

    def login(
        self,
        *,
        payload: LoginCreate,
        session_token: str | None,
    ) -> tuple[AuthSessionRead, str]:
        user = self._repository.get_user_by_email(str(payload.email))
        if user is None or not verify_password(payload.password, user.password_hash):
            raise InvalidCredentialsError()

        self._delete_existing_session(session_token)
        return self._issue_session_for_user(user=user)

    def logout(self, session_token: str | None) -> None:
        self._delete_existing_session(session_token)

    def get_auth_context(self, session_token: str | None) -> AuthContext | None:
        if not session_token:
            return None
        auth_session = self._repository.get_session_by_token_hash(hash_session_token(session_token))
        if auth_session is None or auth_session.user is None:
            return None
        return self._build_context_from_session(auth_session)

    def get_state(self, session_token: str | None) -> AuthSessionRead | None:
        context = self.get_auth_context(session_token)
        if context is None:
            return None
        return self._build_state(context)

    def _issue_session_for_user(self, *, user: User) -> tuple[AuthSessionRead, str]:
        raw_token = generate_session_token()
        auth_session = self._repository.create_session(
            token_hash=hash_session_token(raw_token),
            user_id=user.id,
            ttl_days=settings.auth_session_ttl_days,
        )
        return self._build_state(self._build_context_from_session(auth_session)), raw_token

    def _delete_existing_session(self, session_token: str | None) -> None:
        context = self.get_auth_context(session_token)
        if context is None:
            return
        self._repository.delete_session(context.session)

    def _build_context_from_session(self, auth_session: AuthSession) -> AuthContext:
        return AuthContext(
            session=auth_session,
            user=auth_session.user,
        )

    def _build_state(self, context: AuthContext) -> AuthSessionRead:
        return AuthSessionRead(
            is_authenticated=True,
            user=self._to_user_read(context.user),
        )

    def _to_user_read(self, user: User) -> AuthUserRead:
        return AuthUserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at,
        )
