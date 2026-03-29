from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.auth.infrastructure.persistence.models import AuthSession, User


class AuthRepository:
    def __init__(self, *, session: Session) -> None:
        self._session = session

    def get_session_by_token_hash(self, token_hash: str) -> AuthSession | None:
        statement = (
            select(AuthSession)
            .options(joinedload(AuthSession.user))
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

    def create_session(
        self,
        *,
        token_hash: str,
        user_id: str,
        ttl_days: int,
    ) -> AuthSession:
        auth_session = AuthSession(
            id=str(uuid4()),
            token_hash=token_hash,
            user_id=user_id,
            expires_at=datetime.now(UTC) + timedelta(days=ttl_days),
        )
        self._session.add(auth_session)
        self._session.commit()
        self._session.expire_all()
        return self.get_session_by_token_hash(token_hash)  # type: ignore[return-value]

    def delete_session(self, auth_session: AuthSession) -> None:
        self._session.delete(auth_session)
        self._session.commit()
