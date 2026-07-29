import re
from time import perf_counter
from typing import cast
from uuid import uuid4

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from evalforge.core.logging import (
    get_logger,
    reset_request_id,
    set_request_id,
)

_REQUEST_ID_HEADER = b"x-request-id"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")

logger = get_logger("evalforge.http")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = self._resolve_request_id(scope)
        token = set_request_id(request_id)
        started_at = perf_counter()
        status_code = 500

        logger.info(
            "request_started",
            extra={
                "http_method": scope["method"],
                "http_path": scope["path"],
            },
        )

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code

            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = list(message.get("headers", []))
                headers = [
                    (key, value) for key, value in headers if key.lower() != _REQUEST_ID_HEADER
                ]
                headers.append((_REQUEST_ID_HEADER, request_id.encode("ascii")))
                message = {**message, "headers": headers}

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "http_method": scope["method"],
                    "http_path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        3,
                    ),
                },
            )
            raise
        else:
            logger.info(
                "request_completed",
                extra={
                    "http_method": scope["method"],
                    "http_path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        3,
                    ),
                },
            )
        finally:
            reset_request_id(token)

    @staticmethod
    def _resolve_request_id(scope: Scope) -> str:
        headers = cast(
            list[tuple[bytes, bytes]],
            scope.get("headers", []),
        )

        for key, value in headers:
            if key.lower() != _REQUEST_ID_HEADER:
                continue

            candidate = value.decode("ascii", errors="ignore")
            if _VALID_REQUEST_ID.fullmatch(candidate):
                return candidate

        return uuid4().hex
