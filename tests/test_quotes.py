"""Quote endpoint tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import quote_service


def _random_url(prefix: str, author: str | None = None) -> str:
    url = f"{prefix}/quotes/random"
    return f"{url}?author={author}" if author else url


def test_random_quote_returns_complete_payload(client: TestClient, api_prefix: str) -> None:
    response = client.get(_random_url(api_prefix))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"text", "author", "quote"}
    assert body["text"].strip()
    assert body["author"].strip()
    assert body["quote"] == f'"{body["text"]}" - {body["author"]}'


def test_random_quote_matches_the_loaded_catalogue(client: TestClient, api_prefix: str) -> None:
    body = client.get(_random_url(api_prefix)).json()

    known = {(record.text, record.author) for record in quote_service.all_quotes()}
    assert (body["text"], body["author"]) in known


def test_random_quote_filtered_by_author(client: TestClient, api_prefix: str) -> None:
    author = "Nelson Mandela"
    response = client.get(_random_url(api_prefix, author))

    assert response.status_code == 200
    assert response.json()["author"] == author


def test_random_quote_author_filter_is_case_insensitive(client: TestClient, api_prefix: str) -> None:
    body = client.get(_random_url(api_prefix, "nelson mandela")).json()

    assert body["author"].casefold() == "nelson mandela"


def test_random_quote_unknown_author_is_404(client: TestClient, api_prefix: str) -> None:
    response = client.get(_random_url(api_prefix, "Definitely Not An Author"))

    assert response.status_code == 404
    # Native FastAPI shape, matching the documented schema.
    assert "Definitely Not An Author" in response.json()["detail"]


def test_list_quotes_defaults(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/quotes")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == quote_service.catalog_size()
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert len(body["items"]) == 20


def test_list_quotes_pagination_is_stable_and_disjoint(client: TestClient, api_prefix: str) -> None:
    first = client.get(f"{api_prefix}/quotes?limit=5&offset=0").json()
    second = client.get(f"{api_prefix}/quotes?limit=5&offset=5").json()

    first_keys = {(item["text"], item["author"]) for item in first["items"]}
    second_keys = {(item["text"], item["author"]) for item in second["items"]}

    assert len(first["items"]) == 5
    assert first["total"] == second["total"]
    assert first["items"][0] == client.get(f"{api_prefix}/quotes?limit=1&offset=0").json()["items"][0]
    assert first_keys.isdisjoint(second_keys)


def test_list_quotes_offset_past_end_returns_empty_page(client: TestClient, api_prefix: str) -> None:
    body = client.get(f"{api_prefix}/quotes?offset=100000").json()

    assert body["items"] == []
    assert body["total"] == quote_service.catalog_size()


def test_list_quotes_filtered_by_author(client: TestClient, api_prefix: str) -> None:
    body = client.get(f"{api_prefix}/quotes?author=Albert Einstein&limit=100").json()

    assert body["total"] > 0
    assert all(item["author"] == "Albert Einstein" for item in body["items"])


def test_list_quotes_unknown_author_returns_empty_page(client: TestClient, api_prefix: str) -> None:
    response = client.get(f"{api_prefix}/quotes?author=Nobody At All")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


@pytest.mark.parametrize(
    ("query", "reason"),
    [
        ("limit=0", "limit below minimum"),
        ("limit=101", "limit above maximum"),
        ("offset=-1", "negative offset"),
        ("limit=notanumber", "non-numeric limit"),
    ],
)
def test_list_quotes_rejects_invalid_pagination(
    client: TestClient, api_prefix: str, query: str, reason: str
) -> None:
    response = client.get(f"{api_prefix}/quotes?{query}")

    assert response.status_code == 422, reason
    # Native validation payload keeps the generated OpenAPI schema truthful.
    assert isinstance(response.json()["detail"], list)
