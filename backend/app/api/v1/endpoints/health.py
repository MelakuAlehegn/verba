from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.schemas.health import HealthResponse, ReadinessResponse
from app.services.health_service import get_health_response
from app.services.readiness_service import get_readiness

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    """Liveness: the process is up (no dependency checks)."""
    settings = get_settings()
    return get_health_response(settings)


@router.get("/readyz", response_model=ReadinessResponse, tags=["health"])
def readiness_check(response: Response) -> ReadinessResponse:
    """Readiness: dependencies reachable. 503 if any check fails."""
    ready, checks = get_readiness()
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="ready" if ready else "not_ready", checks=checks)
