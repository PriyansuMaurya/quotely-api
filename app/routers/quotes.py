"""Quote endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app import quote_service
from app.config import settings
from app.models import Quote, QuoteList

router = APIRouter(prefix="/quotes", tags=["quotes"])

AuthorQuery = Annotated[
    str | None,
    Query(
        description="Restrict results to a single author. Matching is case-insensitive and exact.",
        examples=["Nelson Mandela"],
    ),
]


@router.get(
    "/random",
    response_model=Quote,
    summary="Get a random quote",
    response_description="A single randomly selected quote.",
    responses={
        404: {
            "description": "No quotes exist for the requested author.",
            "content": {
                "application/json": {"example": {"detail": "No quotes found for author 'Nobody'"}}
            },
        }
    },
)
def read_random_quote(author: AuthorQuery = None) -> Quote:
    """Return one random quote, optionally from a specific author.

    Without a filter the quote is drawn from Quotely's public random API; with a
    filter it is drawn from the loaded catalogue. An unknown author is a 404,
    because there is no quote to return.
    """
    quote = quote_service.random_quote(author)
    if quote is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No quotes found for author {author!r}",
        )
    return quote


@router.get(
    "",
    response_model=QuoteList,
    summary="List quotes",
    response_description="A page of quotes matching the filters.",
)
def read_quotes(
    author: AuthorQuery = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=settings.max_page_size,
            description=f"Maximum quotes to return (1-{settings.max_page_size}).",
        ),
    ] = settings.default_page_size,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of matching quotes to skip."),
    ] = 0,
) -> QuoteList:
    """List quotes ordered by author, then text, with optional filtering and pagination.

    An author that matches nothing returns an empty page rather than a 404: the
    collection exists, it simply has no members for that filter.
    """
    items, total = quote_service.list_quotes(author, limit=limit, offset=offset)
    return QuoteList(items=items, total=total, limit=limit, offset=offset)
