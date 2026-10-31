"""Health endpoint.

There is deliberately no separate readiness probe: the only dependency is an
in-process quote catalogue loaded at start-up, so a process that is running has
already either loaded it or refused to boot. The response reports the catalogue
size so a bad deploy is visible in one request.
"""

from __future__ import annotations

import time

from fastapi import APIRouter

from app import quote_service
from app.config import settings
from app.models import Health

router = APIRouter(tags=["health"])

_STARTED_AT = time.monotonic()


@router.get(
    "/health",
    response_model=Health,
    summary="Service health",
    response_description="Current status, version and catalogue size.",
)
def read_health() -> Health:
    """Report service health for load balancers and Render's health check."""
    return Health(
        status="ok",
        version=settings.version,
        environment=settings.environment,
        uptime_seconds=round(time.monotonic() - _STARTED_AT, 2),
        catalog_size=quote_service.catalog_size(),
    )
