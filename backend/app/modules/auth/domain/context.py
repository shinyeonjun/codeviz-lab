from dataclasses import dataclass

from app.modules.auth.infrastructure.persistence.models import AuthSession, User
from app.modules.workspaces.infrastructure.persistence.models import Workspace


@dataclass(slots=True)
class AuthContext:
    session: AuthSession
    workspace: Workspace
    user: User
