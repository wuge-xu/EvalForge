from typing import cast

from fastapi import Request

from evalforge.core.config import Settings


def get_app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def get_app_readiness(request: Request) -> bool:
    return bool(request.app.state.ready)
