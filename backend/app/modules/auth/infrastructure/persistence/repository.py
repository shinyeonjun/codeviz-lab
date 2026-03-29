from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.infrastructure.persistence.models import AuthSession, User
from app.modules.workspaces.infrastructure.persistence.models import Workspace


class AuthRepository:
    def __init__(self, *, session: Session) -> None:
        self._session = session

    def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        statement = (
            select(AuthSession)
            .options(joinedload(AuthSession.user), joinedload(AuthSession.workspace))
            .where(AuthSession.token_hash == token_hash)
        )
        auth_session = self._session.execute(statement).scalar_one_or_none()
        if auth_session is None:
            return None
        expires_at = auth_session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            self._session.delete(auth_session)
            self._session.commit()
            return None
        return auth_session

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self._session.execute(statement).scalar_one_or_none()

    def get_user_workspaces(self, user_id: str) -> list[Workspace]:
        statement = (
            select(Workspace)
            .where(Workspace.owner_user_id == user_id)
            .order_by(Workspace.created_at.asc())
        )
        return list(self._session.execute(statement).scalars().all())

    def get_workspace_by_id(self, workspace_id: str) -> Workspace | None:
        statement = select(Workspace).where(Workspace.id == workspace_id)
        return self._session.execute(statement).scalar_one_or_none()

    def create_guest_session(self, *, token_hash: str, ttl_days: int) -> AuthSession:
        workspace = Workspace(
            id=str(uuid4()),
            title="게스트 작업공간",
            is_guest=True,
            owner_user_id=None,
        )
        auth_session = AuthSession(
            id=str(uuid4()),
            token_hash=token_hash,
            user_id=None,
            workspace_id=workspace.id,
            expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
            workspace=workspace,
        )
        self._session.add(workspace)
        self._session.add(auth_session)
        self._session.commit()
        self._session.refresh(auth_session)
        return auth_session

    def create_user(self, *, email: str, password_hash: str, name: str) -> User:
        user = User(
            id=str(uuid4()),
            email=email.lower(),
            password_hash=password_hash,
            name=name,
        )
        self._session.add(user)
        self._session.flush()
        return user

    def create_workspace(self, *, owner_user_id: str | None, title: str, is_guest: bool) -> Workspace:
        workspace = Workspace(
            id=str(uuid4()),
            owner_user_id=owner_user_id,
            title=title,
            is_guest=is_guest,
        )
        self._session.add(workspace)
        self._session.flush()
        return workspace

    def create_session(
        self,
        *,
        token_hash: str,
        user_id: str | None,
        workspace_id: str,
        ttl_days: int,
    ) -> AuthSession:
        auth_session = AuthSession(
            id=str(uuid4()),
            token_hash=token_hash,
            user_id=user_id,
            workspace_id=workspace_id,
            expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
        )
        self._session.add(auth_session)
        self._session.commit()
        self._session.expire_all()
        return self.get_session_by_token_hash(token_hash)  # type: ignore[return-value]

    def attach_guest_session_to_user(
        self,
        *,
        auth_session: AuthSession,
        user: User,
        workspace_title: str,
        ttl_days: int,
    ) -> AuthSession:
        workspace = auth_session.workspace
        workspace.owner_user_id = user.id
        workspace.is_guest = False
        workspace.title = workspace_title
        auth_session.user_id = user.id
        auth_session.expires_at = datetime.now(UTC) + timedelta(days=ttl_days)
        self._session.commit()
        self._session.expire_all()
        return self.get_session_by_token_hash(auth_session.token_hash)  # type: ignore[return-value]

    def replace_session_user(
        self,
        *,
        auth_session: AuthSession,
        user_id: str,
        workspace_id: str,
        ttl_days: int,
    ) -> AuthSession:
        auth_session.user_id = user_id
        auth_session.workspace_id = workspace_id
        auth_session.expires_at = datetime.now(UTC) + timedelta(days=ttl_days)
        self._session.commit()
        self._session.expire_all()
        return self.get_session_by_token_hash(auth_session.token_hash)  # type: ignore[return-value]

    def switch_workspace(self, *, auth_session: AuthSession, workspace_id: str) -> AuthSession:
        auth_session.workspace_id = workspace_id
        self._session.commit()
        self._session.expire_all()
        return self.get_session_by_token_hash(auth_session.token_hash)  # type: ignore[return-value]

    def delete_session(self, auth_session: AuthSession) -> None:
        self._session.delete(auth_session)
        self._session.commit()
