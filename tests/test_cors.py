"""CORS tests.

The bundled SvelteKit frontend calls this API from a different origin, so these
assert the browser contract directly rather than assuming the middleware is wired
correctly.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings

ALLOWED = settings.cors_allowed_origins[0]
DISALLOWED = "https://evil.example.com"


def test_allowed_origin_receives_cors_header(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/quotes/random", headers={"Origin": ALLOWED})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED


def test_disallowed_origin_receives_no_cors_header(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/quotes/random", headers={"Origin": DISALLOWED})

    assert "access-control-allow-origin" not in response.headers


def test_preflight_is_answered_not_rejected(client: TestClient, api_prefix: str) -> None:
    """Without CORS the preflight hit the GET-only route and returned 405."""
    response = client.options(
        f"{api_prefix}/quotes/random",
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
    assert "GET" in response.headers["access-control-allow-methods"]


def test_request_id_is_exposed_to_browser_javascript(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/quotes/random", headers={"Origin": ALLOWED})

    exposed = response.headers.get("access-control-expose-headers", "")
    assert "X-Request-ID" in exposed.lower() or "x-request-id" in exposed.lower()


def test_health_is_reachable_cross_origin(client: TestClient) -> None:
    response = client.get("/health", headers={"Origin": ALLOWED})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ALLOWED
