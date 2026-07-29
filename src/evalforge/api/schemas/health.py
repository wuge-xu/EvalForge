from typing import Literal

from pydantic import BaseModel

from evalforge.core.config import Environment


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
    environment: Environment


class LivenessResponse(BaseModel):
    status: Literal["alive"]
    service: str
    version: str


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    service: str
    version: str
