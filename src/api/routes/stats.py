"""Stats REST route.

GET /api/v1/stats -- live simulation counters.
Ticket: TCK-20260821-REST-MAP-STATIC-STATS
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_engine_manager
from src.api.presenters.state_presenter import StatePresenter

router = APIRouter(tags=["Stats"])


@router.get(
    "/stats",
    response_model=Dict[str, Any],
    summary="Live simulation counters",
    description=(
        "Returns {tick, world_day, alive_count, total_spawned, total_deaths, running, paused}. "
        "Read-only -- no state mutation."
    ),
)
async def get_stats() -> Dict[str, Any]:
    manager = get_engine_manager()
    state = manager.latest_state
    if state is None:
        raise HTTPException(status_code=503, detail="Engine not ready — no state available")
    return StatePresenter.present_stats(
        state,
        total_spawned=manager.total_spawned,
        total_deaths=manager.total_deaths,
        running=manager.is_running,
        paused=manager.is_paused,
    )
