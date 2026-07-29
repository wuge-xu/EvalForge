from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from evalforge.api.middleware.request_context import RequestContextMiddleware
from evalforge.api.router import api_router
from evalforge.core.config import Settings, get_settings
from evalforge.core.logging import configure_logging, get_logger

logger = get_logger("evalforge.lifecycle")


@asynccontextmanager
async def application_lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    application.state.ready = True
    logger.info("application_ready")

    try:
        yield
    finally:
        application.state.ready = False
        logger.info("application_stopped")


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    configure_logging(app_settings.log_level)

    application = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        debug=app_settings.debug,
        description="RAG and Agent evaluation, experiment tracking, and regression platform",
        lifespan=application_lifespan,
    )

    application.state.settings = app_settings
    application.state.ready = False

    application.add_middleware(RequestContextMiddleware)
    application.include_router(api_router)

    return application


app = create_app()
