"""Shared test fixtures."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


@pytest.fixture(scope="session")
def client() -> Iterator[TestClient]:
    """A client bound to the real application instance."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def api_prefix() -> str:
    """The configured API prefix, so tests follow the config rather than hardcoding it."""
    return settings.api_prefix
