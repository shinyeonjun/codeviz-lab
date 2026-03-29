from dataclasses import dataclass

from app.modules.auth.infrastructure.persistence.models import AuthSession, User


@dataclass(slots=True)
class AuthContext:
    session: AuthSession
    user: User
