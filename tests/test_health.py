"""Health endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import quote_service
from app.config import settings


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == settings.version
    assert body["environment"] == settings.environment


def test_health_reports_catalogue_size(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body["catalog_size"] == quote_service.catalog_size()
    assert body["catalog_size"] > 0


def test_health_uptime_is_non_negative(client: TestClient) -> None:
    body = client.get("/health").json()

    assert body["uptime_seconds"] >= 0
