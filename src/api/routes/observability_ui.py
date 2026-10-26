"""Observability dashboard page and its two redirects.

GET /api/v1/observability/ui serves the single-page dashboard from `src/api/static_pages/observability_ui.html`;
/observability/ui and /api/v1/observability/live/ui redirect to it. Browsers cannot set headers on a page load, so
the three routes accept the API key as a header or a query parameter (TCK-20260823-HTTP-API-KEY-AUTH, Decision 3).
"""
from __future__ import annotations

from functools import cache
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from src.api.admission_control import require_admission_header_or_query
from src.api.auth import require_api_key_header_or_query

router = APIRouter()

_PAGE = Path(__file__).resolve().parent.parent / "static_pages" / "observability_ui.html"
_PAGE_AUTH = [Depends(require_api_key_header_or_query), Depends(require_admission_header_or_query)]


@cache
def _page_bytes() -> bytes:
    """The dashboard page, read from disk once; the bytes are served unchanged."""
    return _PAGE.read_bytes()


@router.get("/api/v1/observability/ui", response_class=HTMLResponse, dependencies=_PAGE_AUTH)
async def get_observability_ui() -> HTMLResponse:  # noqa: D103  # a docstring would become the OpenAPI description, which is pinned
    return HTMLResponse(content=_page_bytes(), status_code=200)


@router.get("/observability/ui", dependencies=_PAGE_AUTH)
async def redirect_ui() -> RedirectResponse:  # noqa: D103  # a docstring would become the OpenAPI description, which is pinned
    return RedirectResponse(url="/api/v1/observability/ui")


@router.get("/api/v1/observability/live/ui", dependencies=_PAGE_AUTH)
async def redirect_live_ui() -> RedirectResponse:  # noqa: D103  # a docstring would become the OpenAPI description, which is pinned
    return RedirectResponse(url="/api/v1/observability/ui")
