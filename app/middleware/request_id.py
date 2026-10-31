"""Request correlation middleware.

Every request gets a request id, echoed back in the ``X-Request-ID`` header and
attached to its log line, so a report of "this call failed" can be traced to
exactly one request. A caller-supplied id is honoured when it looks like an
identifier, and replaced otherwise so that arbitrary header content cannot be
injected into the log stream.
"""

from __future__ import annotations

import logging
import re
import secrets
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.logging_config import request_id_ctx

REQUEST_ID_HEADER = "X-Request-ID"
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

logger = logging.getLogger("app.request")


def _resolve_request_id(candidate: str | None) -> str:
    if candidate and _SAFE_REQUEST_ID.fullmatch(candidate):
        return candidate
    return secrets.token_hex(8)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign a request id, time the request, and emit one access log line."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = _resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        request.state.request_id = request_id
        token = request_id_ctx.set(request_id)
        started = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            logger.exception(
                "request failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise
        finally:
            request_id_ctx.reset(token)

        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
