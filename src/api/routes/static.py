"""Static REST route.

GET /api/v1/static -- static world objects (buildings, resource nodes, treasure chests, regions).
Ticket: TCK-20260821-REST-MAP-STATIC-STATS
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_engine_manager
from src.api.presenters.state_presenter import StatePresenter

router = APIRouter(tags=["Static"])


@router.get(
    "/static",
    response_model=Dict[str, Any],
    summary="Static world objects",
    description=(
        "Returns {buildings, resource_nodes, treasure_chests, regions}. "
        "Read-only -- no state mutation."
    ),
)
async def get_static() -> Dict[str, Any]:
    manager = get_engine_manager()
    state = manager.latest_state
    if state is None:
        raise HTTPException(status_code=503, detail="Engine not ready — no state available")
    return StatePresenter.present_static(state)
