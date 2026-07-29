from typing import Annotated, Literal

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from evalforge.api.dependencies import (
    get_app_readiness,
    get_app_settings,
)
from evalforge.api.schemas.health import (
    HealthResponse,
    LivenessResponse,
    ReadinessResponse,
)
from evalforge.core.config import Settings

router = APIRouter(tags=["system"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Check API health",
)
def get_health(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Check process liveness",
)
def get_liveness(
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> LivenessResponse:
    return LivenessResponse(
        status="alive",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "model": ReadinessResponse,
            "description": "Application is not ready to receive traffic",
        },
    },
    summary="Check application readiness",
)
def get_readiness(
    settings: Annotated[Settings, Depends(get_app_settings)],
    is_ready: Annotated[bool, Depends(get_app_readiness)],
) -> ReadinessResponse | JSONResponse:
    readiness_status: Literal["ready", "not_ready"] = "ready" if is_ready else "not_ready"
    response = ReadinessResponse(
        status=readiness_status,
        service=settings.app_name,
        version=settings.app_version,
    )

    if is_ready:
        return response

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=response.model_dump(mode="json"),
    )
