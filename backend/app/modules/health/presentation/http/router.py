from fastapi import APIRouter, Depends

from app.common.responses import success_response
from app.modules.health.application.services.health_service import (
    HealthService,
    get_health_service,
)

router = APIRouter()


@router.get("/health")
def read_health(
    service: HealthService = Depends(get_health_service),
) -> dict[str, object]:
    payload = service.read_health()
    return success_response(payload.model_dump())
