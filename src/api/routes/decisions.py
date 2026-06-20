"""
src/api/routes/decisions.py
───────────────────────────────────────────────────────────────────────────────
Decision Explanation REST endpoints (Epic 2.2C).

Endpoints:
  GET /api/v1/observability/entities/{entity_id}/decisions
      ?run_id=<str>&tick=<int>
      → Single-tick ranked route list for one entity.

  GET /api/v1/observability/entities/{entity_id}/decisions/range
      ?run_id=<str>&from=<int>&to=<int>
      → Tick range (max 100 ticks) of route lists for one entity.

  GET /api/v1/observability/entities/{entity_id}/decisions/summary
      ?run_id=<str>
      → Route-kind selection histogram over all ticks for one entity.

Architecture constraints:
- No imports of AuthoritativeState, EntityState, AdventureRouteOption,
  RouteFamily, or any domain model type.
- No durable state mutation (no append_entry, rebuild calls).
- All responses pass through DecisionPresenter (no raw dicts returned).
"""
from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Query

from src.observability.reporting.history_query import sanitize_id
from src.observability.cognition.tick_index import DecisionTraceIndex
from src.api.presenters.decisions import DecisionPresenter

router = APIRouter(prefix="/observability", tags=["Decisions"])
logger = logging.getLogger(__name__)


def _get_index(run_id: str) -> DecisionTraceIndex:
    """
    Resolve run_dir from run_id and return a DecisionTraceIndex.

    Raises HTTPException 404 if the run directory or trace file is missing.
    """
    run_dir = os.path.join("data/runs", run_id)
    if not os.path.isdir(run_dir):
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    trace_path = os.path.join(run_dir, "decision_trace.jsonl")
    if not os.path.exists(trace_path):
        raise HTTPException(status_code=404, detail="no decision trace for this run")
    return DecisionTraceIndex(run_dir)


@router.get("/entities/{entity_id}/decisions")
async def get_entity_decisions(
    entity_id: int,
    run_id: str = Query(..., description="Run identifier"),
    tick: int = Query(..., ge=0, description="Tick number"),
):
    """
    Return the ranked list of scored route candidates for entity_id at a single tick.

    200 + empty routes list when tick is absent from the index.
    """
    try:
        run_id = sanitize_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    index = _get_index(run_id)
    entries = index.lookup(tick)
    return DecisionPresenter.present_tick_response(entity_id, tick, entries)


@router.get("/entities/{entity_id}/decisions/range")
async def get_entity_decisions_range(
    entity_id: int,
    run_id: str = Query(..., description="Run identifier"),
    from_tick: int = Query(..., alias="from", ge=0, description="Start tick (inclusive)"),
    to_tick: int = Query(..., alias="to", ge=0, description="End tick (inclusive)"),
):
    """
    Return scored route lists for entity_id across a tick range [from, to].

    Ticks with no data after entity filtering are omitted from the response.
    Range is capped at 100 ticks. Returns 400 when from > to or range > 100.
    """
    try:
        run_id = sanitize_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if to_tick < from_tick:
        raise HTTPException(status_code=400, detail="'to' must be >= 'from'")
    if to_tick - from_tick > 100:
        raise HTTPException(status_code=400, detail="Range cannot exceed 100 ticks")
    index = _get_index(run_id)
    all_entries = []
    for t in range(from_tick, to_tick + 1):
        all_entries.extend(index.lookup(t))
    return DecisionPresenter.present_range_response(entity_id, all_entries)


@router.get("/entities/{entity_id}/decisions/summary")
async def get_entity_decisions_summary(
    entity_id: int,
    run_id: str = Query(..., description="Run identifier"),
):
    """
    Return the route-kind selection histogram for entity_id across all ticks.

    Computes fraction of selected decisions per route_kind. Returns
    tick_count = number of ticks that had at least one entry for this entity.
    """
    try:
        run_id = sanitize_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    index = _get_index(run_id)
    # Ensure the in-memory index is populated before accessing _index
    index._load()
    route_kind_counts: dict[str, int] = {}
    total_selections: int = 0
    tick_count: int = 0
    for tick in list(index._index.keys()):
        entries = index.lookup(tick)
        for entry in entries:
            if entry.get("entity_id") != entity_id:
                continue
            tick_count += 1
            for route in entry.get("routes", []):
                if route.get("selected"):
                    kind = route.get("route_kind", "UNKNOWN")
                    route_kind_counts[kind] = route_kind_counts.get(kind, 0) + 1
                    total_selections += 1
    distribution: dict[str, float] = {}
    if total_selections > 0:
        distribution = {
            k: round(v / total_selections, 4)
            for k, v in route_kind_counts.items()
        }
    return DecisionPresenter.present_summary_response(entity_id, tick_count, distribution)
