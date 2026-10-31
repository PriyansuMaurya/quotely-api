"""Quote catalogue access.

The catalogue is loaded once, at import time, into an immutable tuple. Loading
eagerly means a missing or malformed ``data/quotes.json`` fails the process at
start-up — which Render reports as a failed deploy — instead of surfacing as a 500
on a user's first request.

Two data sources coexist by design:

* ``get_random_quote`` from the public Quotely API backs ``/quotes/random`` when no
  author filter is supplied.
* The committed snapshot in ``data/quotes.json`` backs the list and filter
  endpoints, which Quotely's public API cannot serve.

``tests/test_snapshot.py`` asserts the two agree, so the pair cannot drift
silently.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from quotely import get_random_quote

from app.config import settings
from app.models import Quote


class CatalogError(RuntimeError):
    """Raised when the quote snapshot is missing, unreadable or malformed."""


@dataclass(frozen=True, slots=True)
class QuoteRecord:
    """An immutable catalogue entry."""

    text: str
    author: str

    def to_model(self) -> Quote:
        return Quote.from_parts(self.text, self.author)


def _read_snapshot(path: Path) -> tuple[QuoteRecord, ...]:
    """Parse and validate the snapshot file."""
    if not path.is_file():
        raise CatalogError(
            f"Quote snapshot not found at {path}. "
            "Generate it with `uv run python -m scripts.sync_quotes`."
        )

    try:
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CatalogError(f"Quote snapshot at {path} is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("quotes"), list):
        raise CatalogError(f"Quote snapshot at {path} must be an object with a 'quotes' list.")

    records: list[QuoteRecord] = []
    for index, entry in enumerate(payload["quotes"]):
        if not isinstance(entry, dict):
            raise CatalogError(f"Quote snapshot entry {index} is not an object.")
        text = entry.get("text")
        author = entry.get("author")
        if not isinstance(text, str) or not text.strip():
            raise CatalogError(f"Quote snapshot entry {index} has no usable 'text'.")
        if not isinstance(author, str) or not author.strip():
            raise CatalogError(f"Quote snapshot entry {index} has no usable 'author'.")
        records.append(QuoteRecord(text=text, author=author))

    if not records:
        raise CatalogError(f"Quote snapshot at {path} contains no quotes.")

    return tuple(records)


def _author_key(value: str) -> str:
    """Normalise an author name for case-insensitive comparison."""
    return value.strip().casefold()


CATALOG: tuple[QuoteRecord, ...] = _read_snapshot(settings.data_file)


def catalog_size() -> int:
    """Return the number of quotes held in memory."""
    return len(CATALOG)


def all_quotes() -> tuple[QuoteRecord, ...]:
    """Return the full catalogue."""
    return CATALOG


def quotes_by_author(author: str) -> tuple[QuoteRecord, ...]:
    """Return quotes whose author matches exactly, ignoring case."""
    wanted = _author_key(author)
    return tuple(record for record in CATALOG if _author_key(record.author) == wanted)


def list_quotes(
    author: str | None = None,
    *,
    limit: int,
    offset: int,
) -> tuple[list[Quote], int]:
    """Return a page of quotes plus the unpaginated match count.

    An unknown author yields an empty page rather than an error: a filtered
    collection that legitimately has no members is a 200 with no items.
    """
    pool = quotes_by_author(author) if author is not None else CATALOG
    total = len(pool)
    page = pool[offset : offset + limit]
    return [record.to_model() for record in page], total


def random_quote(author: str | None = None) -> Quote | None:
    """Return a random quote, optionally restricted to one author.

    Without a filter this defers to Quotely's public API, keeping the library the
    runtime source of truth for the random endpoint. With a filter it samples the
    catalogue, since Quotely offers no filtered access. Returns ``None`` when a
    filter matches nothing, which the router turns into a 404.
    """
    if author is None:
        library_quote = get_random_quote()
        # Quotely exposes the author as `.name`; the body is the str() rendering.
        return Quote.from_parts(str(library_quote).strip(), library_quote.name.strip())

    matches = quotes_by_author(author)
    if not matches:
        return None
    return random.choice(matches).to_model()
