"""Application factory and ASGI entry point.

Run locally with::

    uv run uvicorn app.main:app --reload

On Render::

    uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import quote_service
from app.config import settings
from app.errors import register_exception_handlers
from app.logging_config import configure_logging
from app.middleware.request_id import RequestIdMiddleware
from app.routers import health, quotes

configure_logging(settings.log_level)
logger = logging.getLogger("app.main")

DESCRIPTION = """
A small, production-shaped REST API over the
[Quotely](https://pypi.org/project/quotely/) quote library.

* **Random quotes** — one quote per call, optionally restricted to an author.
* **Filtered listing** — paginated quotes, filterable by author.
* **Health** — status, version, uptime and catalogue size.

Every response carries an `X-Request-ID` header, which also appears in the
structured request logs so a failure can be traced end to end.
"""

TAGS_METADATA = [
    {"name": "quotes", "description": "Retrieve random and filtered quotes."},
    {"name": "health", "description": "Service liveness and build information."},
    {"name": "meta", "description": "Service index and documentation links."},
]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Log the resolved configuration once the service is ready to serve."""
    logger.info(
        "service starting",
        extra={
            "version": settings.version,
            "environment": settings.environment,
            "catalog_size": quote_service.catalog_size(),
            "data_file": str(settings.data_file),
            # Logged because a wrong allowlist is invisible from the API side: the
            # browser just reports a failed request, with no clue that CORS is why.
            "cors_allowed_origins": list(settings.cors_allowed_origins),
        },
    )
    yield
    logger.info("service stopping")


def create_app() -> FastAPI:
    """Build the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={"name": "Quotely API"},
        license_info={"name": "MIT"},
    )

    app.add_middleware(RequestIdMiddleware)
    # Added last so CORS is the outermost layer: preflight OPTIONS requests are
    # answered before they can reach routing and 405 on a GET-only route.
    if settings.cors_allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_allowed_origins),
            allow_methods=["GET", "HEAD", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"],
            max_age=600,
        )
    register_exception_handlers(app)

    app.include_router(quotes.router, prefix=settings.api_prefix)
    app.include_router(health.router)

    @app.get("/", tags=["meta"], summary="Service index")
    def read_index() -> dict[str, object]:
        """Point callers at the documentation and the available endpoints."""
        return {
            "service": settings.app_name,
            "version": settings.version,
            "documentation": {
                "swagger": "/docs",
                "redoc": "/redoc",
                "openapi": "/openapi.json",
            },
            "endpoints": {
                "random_quote": f"{settings.api_prefix}/quotes/random",
                "list_quotes": f"{settings.api_prefix}/quotes",
                "health": "/health",
            },
        }

    return app


app = create_app()
