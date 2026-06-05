from app.core.config import Settings
from app.crud.health import read_health_snapshot
from app.schemas.health import HealthResponse


def get_health_response(settings: Settings) -> HealthResponse:
    health_snapshot = read_health_snapshot(settings)
    return HealthResponse(**health_snapshot)

