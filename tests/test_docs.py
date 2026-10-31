"""Documentation and index tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_swagger_ui_is_served(client: TestClient) -> None:
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "swagger" in response.text.lower()


def test_redoc_is_served(client: TestClient) -> None:
    response = client.get("/redoc")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema_documents_all_endpoints(client: TestClient, api_prefix: str) -> None:
    schema = client.get("/openapi.json").json()

    assert schema["info"]["title"]
    assert schema["info"]["version"]
    assert {
        "/",
        "/health",
        f"{api_prefix}/quotes",
        f"{api_prefix}/quotes/random",
    } <= set(schema["paths"])


def test_openapi_documents_the_query_parameters(client: TestClient, api_prefix: str) -> None:
    schema = client.get("/openapi.json").json()

    list_params = {p["name"] for p in schema["paths"][f"{api_prefix}/quotes"]["get"]["parameters"]}
    random_params = {
        p["name"] for p in schema["paths"][f"{api_prefix}/quotes/random"]["get"]["parameters"]
    }

    assert {"author", "limit", "offset"} == list_params
    assert random_params == {"author"}


def test_index_lists_documentation_and_endpoints(client: TestClient, api_prefix: str) -> None:
    body = client.get("/").json()

    assert body["documentation"]["swagger"] == "/docs"
    assert body["endpoints"]["random_quote"] == f"{api_prefix}/quotes/random"
    assert body["endpoints"]["health"] == "/health"
