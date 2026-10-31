"""Error handling and request correlation tests."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import register_exception_handlers
from app.main import app as real_app
from app.middleware.request_id import REQUEST_ID_HEADER


def test_response_carries_request_id(client: TestClient) -> None:
    response = client.get("/health")

    assert response.headers[REQUEST_ID_HEADER]
    assert len(response.headers[REQUEST_ID_HEADER]) == 16


def test_supplied_request_id_is_echoed(client: TestClient) -> None:
    supplied = "trace-abc-123"
    response = client.get("/health", headers={REQUEST_ID_HEADER: supplied})

    assert response.headers[REQUEST_ID_HEADER] == supplied


def test_unsafe_request_id_is_replaced(client: TestClient) -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "bad value\nwith newline"})

    returned = response.headers[REQUEST_ID_HEADER]
    assert returned != "bad value\nwith newline"
    assert "\n" not in returned


def test_unknown_route_uses_native_detail_shape(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/quotes/nope")

    assert response.status_code == 404
    assert set(response.json()) == {"detail"}


def test_unhandled_error_returns_envelope_with_request_id() -> None:
    app = _app_with_failing_route()
    supplied = "crash-trace-42"

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom", headers={REQUEST_ID_HEADER: supplied})

    assert response.status_code == 500
    assert response.headers[REQUEST_ID_HEADER] == supplied
    body = response.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["request_id"] == supplied
    # Internals must not leak to the caller.
    assert "secret" not in response.text.lower()


def _app_with_failing_route() -> FastAPI:
    """A copy of the real app plus one endpoint that always raises."""
    app = FastAPI()
    app.add_middleware(_middleware_class())
    register_exception_handlers(app)

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    return app


def _middleware_class() -> type:
    from app.middleware.request_id import RequestIdMiddleware

    return RequestIdMiddleware


def test_real_app_still_serves_after_error_handlers_registered() -> None:
    """Guard against handler registration breaking normal traffic."""
    with TestClient(real_app) as client:
        assert client.get("/health").status_code == 200
