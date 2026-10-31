"""Regenerate ``data/quotes.json`` from the installed Quotely library.

The Quotely package exposes a single random quote through its public API, but the
REST surface of this service also needs to *list* and *filter* quotes, which
requires the whole catalogue. Quotely does not export that catalogue publicly:
``ALL_QUOTES`` lives in ``quotely.core`` outside of ``__all__``.

Rather than depend on a private symbol at request time, this script snapshots the
catalogue into a committed JSON file that the application reads eagerly at
start-up. Quotely therefore stays the runtime source of truth for
``/quotes/random`` (via its public ``get_random_quote``) while the snapshot backs
the list and filter endpoints.

Because the snapshot is derived data it can drift, so
``tests/test_snapshot.py`` re-reads the library and fails if the committed file
no longer matches. To refresh after a Quotely upgrade:

    uv run python -m scripts.sync_quotes
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# ``ALL_QUOTES`` is deliberately imported from ``quotely.core``: it is the only
# way to reach the full catalogue, and this module is the single place in the
# codebase allowed to know that. A future Quotely release that removes or renames
# it will fail here (and in the drift test) rather than degrade the API silently.
from quotely.core import ALL_QUOTES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = PROJECT_ROOT / "data" / "quotes.json"


def build_snapshot() -> list[dict[str, str]]:
    """Return the Quotely catalogue as a stable, sorted list of records."""
    records = [
        {"text": text, "author": author}
        for text, author in ALL_QUOTES
        if text.strip() and author.strip()
    ]
    records.sort(key=lambda record: (record["author"].casefold(), record["text"].casefold()))
    return records


def write_snapshot(path: Path = SNAPSHOT_PATH) -> int:
    """Write the snapshot to ``path`` and return the number of records written."""
    records = build_snapshot()
    payload: dict[str, Any] = {
        "$comment": (
            "Derived from quotely.core.ALL_QUOTES. Do not edit by hand; "
            "regenerate with `uv run python -m scripts.sync_quotes`."
        ),
        "source": "quotely",
        "quotes": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(records)


def main() -> int:
    count = write_snapshot()
    print(f"Wrote {count} quotes to {SNAPSHOT_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
