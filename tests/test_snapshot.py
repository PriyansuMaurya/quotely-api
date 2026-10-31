"""Catalogue snapshot tests.

The service reads list and filter results from ``data/quotes.json`` while
``/quotes/random`` goes through Quotely's public API. These tests are what keep
those two sources from drifting apart.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import quote_service
from app.config import settings
from app.quote_service import CatalogError, _read_snapshot
from scripts.sync_quotes import SNAPSHOT_PATH, build_snapshot


def test_snapshot_matches_installed_quotely() -> None:
    """The committed snapshot must equal the data in the installed Quotely package.

    ``ALL_QUOTES`` is imported from ``quotely.core`` deliberately: it is the only
    way to see the full catalogue, and this is the second of only two places in
    the codebase that is allowed to depend on it. A Quotely release that moves or
    removes the symbol fails here loudly instead of shipping inconsistent quotes.
    """
    from quotely.core import ALL_QUOTES

    library = {
        (text.strip(), author.strip())
        for text, author in ALL_QUOTES
        if text.strip() and author.strip()
    }
    snapshot = {(record["text"], record["author"]) for record in build_snapshot()}

    assert snapshot == library
    assert len(snapshot) == len(library)


def test_committed_file_matches_generated_snapshot() -> None:
    """The file on disk must be exactly what the generator produces."""
    on_disk = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))

    assert on_disk["quotes"] == build_snapshot()


def test_snapshot_has_no_empty_fields() -> None:
    for record in build_snapshot():
        assert record["text"].strip(), "empty quote text"
        assert record["author"].strip(), "empty author"


def test_snapshot_is_sorted_for_stable_diffs() -> None:
    records = build_snapshot()
    keys = [(r["author"].casefold(), r["text"].casefold()) for r in records]

    assert keys == sorted(keys)


def test_catalogue_is_loaded_from_the_configured_file() -> None:
    assert settings.data_file == SNAPSHOT_PATH
    assert quote_service.catalog_size() == len(build_snapshot())
    assert quote_service.all_quotes()


def test_author_lookup_is_case_insensitive() -> None:
    lower = quote_service.quotes_by_author("albert einstein")
    proper = quote_service.quotes_by_author("Albert Einstein")

    assert lower == proper
    assert len(proper) > 0


def test_author_lookup_trims_surrounding_whitespace() -> None:
    assert quote_service.quotes_by_author("  Albert Einstein  ") == quote_service.quotes_by_author(
        "Albert Einstein"
    )


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        ("", "not valid JSON"),
        ("[]", "must be an object"),
        ('{"quotes": "nope"}', "must be an object"),
        ('{"quotes": []}', "contains no quotes"),
        ('{"quotes": [{"author": "X"}]}', "no usable 'text'"),
        ('{"quotes": [{"text": "Y"}]}', "no usable 'author'"),
        ('{"quotes": ["nope"]}', "is not an object"),
    ],
)
def test_invalid_snapshots_fail_loudly(tmp_path: Path, content: str, expected: str) -> None:
    path = tmp_path / "quotes.json"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(CatalogError, match=expected):
        _read_snapshot(path)


def test_missing_snapshot_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(CatalogError, match="not found"):
        _read_snapshot(tmp_path / "absent.json")
