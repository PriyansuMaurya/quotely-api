"""Application configuration.

Settings are read from the environment so the same image runs unchanged locally
and on Render. Only the standard library is used here: the service has no need
for a settings framework, and every extra dependency is one more thing Render has
to install on a cold build.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from app import __version__

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_FILE = PROJECT_ROOT / "data" / "quotes.json"


@dataclass(frozen=True, slots=True)
class Settings:
    """Immutable runtime configuration."""

    app_name: str
    version: str
    environment: str
    log_level: str
    data_file: Path
    default_page_size: int
    max_page_size: int
    api_prefix: str = "/api/v1"


def _int_from_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def load_settings() -> Settings:
    """Build settings from the current environment."""
    return Settings(
        app_name=os.getenv("APP_NAME", "Quotely API"),
        version=__version__,
        environment=os.getenv("ENVIRONMENT", "development"),
        log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        data_file=Path(os.getenv("QUOTES_DATA_FILE", str(DEFAULT_DATA_FILE))),
        default_page_size=_int_from_env("DEFAULT_PAGE_SIZE", 20),
        max_page_size=_int_from_env("MAX_PAGE_SIZE", 100),
    )


settings = load_settings()
