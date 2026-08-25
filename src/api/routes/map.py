"""Map REST route.

GET /api/v1/map -- RLE-encoded terrain grid.
Ticket: TCK-20260821-REST-MAP-STATIC-STATS
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_engine_manager
from src.api.presenters.state_presenter import StatePresenter

router = APIRouter(tags=["Map"])


@router.get(
    "/map",
    response_model=Dict[str, Any],
    summary="RLE-encoded terrain grid",
    description="Returns {width, height, grid} -- RLE-encoded terrain. Read-only -- no state mutation.",
)
async def get_map() -> Dict[str, Any]:
    manager = get_engine_manager()
    state = manager.latest_state
    if state is None:
        raise HTTPException(status_code=503, detail="Engine not ready — no state available")
    return StatePresenter.present_map(state)
