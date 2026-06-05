from app.core.config import Settings


def read_health_snapshot(settings: Settings) -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
    }

