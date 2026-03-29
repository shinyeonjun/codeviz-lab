from app.core.config import settings
from app.modules.health.presentation.http.schemas import HealthPayload


class HealthService:
    def read_health(self) -> HealthPayload:
        return HealthPayload(
            name=settings.app_name,
            version=settings.app_version,
            status="ok",
        )


def get_health_service() -> HealthService:
    return HealthService()
