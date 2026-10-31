"""Pydantic schemas describing the public API contract.

These models double as the OpenAPI documentation served at ``/docs``, so every
field carries a description and the responses carry concrete examples.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Quote(BaseModel):
    """A single quote with its attribution."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
                "quote": '"The only way to do great work is to love what you do." - Steve Jobs',
            }
        }
    )

    text: str = Field(description="The quote body, without surrounding quotation marks.")
    author: str = Field(description="Attributed author, or 'Unknown' where the source is anonymous.")
    quote: str = Field(description="Convenience rendering of the quote and author in one string.")

    @classmethod
    def from_parts(cls, text: str, author: str) -> Quote:
        """Build a quote from its parts, deriving the combined rendering."""
        return cls(text=text, author=author, quote=f'"{text}" - {author}')


class QuoteList(BaseModel):
    """A page of quotes."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "text": "It always seems impossible until it's done.",
                        "author": "Nelson Mandela",
                        "quote": '"It always seems impossible until it\'s done." - Nelson Mandela',
                    }
                ],
                "total": 508,
                "limit": 20,
                "offset": 0,
            }
        }
    )

    items: list[Quote] = Field(description="Quotes on this page, ordered by author then text.")
    total: int = Field(description="Total quotes matching the query, ignoring pagination.")
    limit: int = Field(description="Maximum number of items requested for this page.")
    offset: int = Field(description="Number of matching quotes skipped before this page.")


class Health(BaseModel):
    """Service health and build information."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
                "version": "1.0.0",
                "environment": "production",
                "uptime_seconds": 132.4,
                "catalog_size": 508,
            }
        }
    )

    status: str = Field(description="'ok' when the service is ready to serve requests.")
    version: str = Field(description="Deployed application version.")
    environment: str = Field(description="Deployment environment name.")
    uptime_seconds: float = Field(description="Seconds since this process started.")
    catalog_size: int = Field(description="Number of quotes loaded into memory at start-up.")


class ErrorDetail(BaseModel):
    """Machine-readable error payload used for unexpected failures."""

    code: str = Field(description="Stable, machine-readable error code.")
    message: str = Field(description="Human-readable explanation, safe to display.")
    request_id: str | None = Field(
        default=None,
        description="Identifier echoed in the X-Request-ID header and request logs.",
    )


class ErrorResponse(BaseModel):
    """Envelope returned for unhandled server errors."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": {
                    "code": "internal_error",
                    "message": "An unexpected error occurred.",
                    "request_id": "4f8c1a2b9d7e4c6a",
                }
            }
        }
    )

    error: ErrorDetail
