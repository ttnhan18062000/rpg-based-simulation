"""Economy REST routes.

GET /api/v1/economy/health — per-region economy health snapshot.
Ticket: TCK-20260619-E33B-ALERTS-REST
"""
from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from src.api.dependencies import get_engine_manager
from src.api.presenters.economy import EconomyPresenter

router = APIRouter(prefix="/economy", tags=["Economy"])


@router.get(
    "/health",
    response_model=Dict[str, Any],
    summary="Current economy health per region",
    description=(
        "Returns the latest per-region Gini coefficient, transaction velocity (stub), "
        "and active alert (INFLATION_SPIRAL | GOLD_HOARDING | null) derived from the "
        "current authoritative state. Read-only — no state mutation."
    ),
)
async def get_economy_health() -> Dict[str, Any]:
    manager = get_engine_manager()
    state = manager.latest_state
    if state is None:
        raise HTTPException(status_code=503, detail="Engine not ready — no state available")
    return EconomyPresenter.present_health(state)
