from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import get_settings

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str


@router.get("/healthz", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name)

