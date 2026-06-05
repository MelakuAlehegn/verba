from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.health import HealthResponse
from app.services.health_service import get_health_response

router = APIRouter()


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    settings = get_settings()
    return get_health_response(settings)
