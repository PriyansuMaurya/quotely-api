"""Exception handling.

Handled client errors keep FastAPI's native ``{"detail": ...}`` body, because that
is the shape the generated OpenAPI schema documents — rewriting it would make the
published contract inaccurate. Only unhandled server errors, which have no
documented schema, are wrapped in an envelope that adds a stable error code and the
request id.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.middleware.request_id import REQUEST_ID_HEADER
from app.models import ErrorDetail, ErrorResponse

logger = logging.getLogger("app.errors")


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Return handled HTTP errors in FastAPI's native shape."""
    headers = dict(getattr(exc, "headers", None) or {})
    request_id = _request_id(request)
    if request_id:
        headers[REQUEST_ID_HEADER] = request_id
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Log the failure and return a traceable envelope without leaking internals."""
    request_id = _request_id(request)
    logger.exception(
        "unhandled exception",
        extra={"method": request.method, "path": request.url.path},
    )
    body = ErrorResponse(
        error=ErrorDetail(
            code="internal_error",
            message="An unexpected error occurred.",
            request_id=request_id,
        )
    )
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(status_code=500, content=body.model_dump(), headers=headers)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach the handlers to the application."""
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
