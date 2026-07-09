from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class ReadinessResponse(BaseModel):
    status: str  # "ready" | "not_ready"
    checks: dict[str, str]  # per-dependency: "ok" | "error"

