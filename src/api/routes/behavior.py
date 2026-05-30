from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.observability.warehouse.adapters import LocalWarehouseAdapter
from src.observability.reporting.history_query import sanitize_id

router = APIRouter(prefix="/behavior", tags=["Behavior"])
adapter = LocalWarehouseAdapter()

class ErrorResponse(BaseModel):
    detail: str

@router.get(
    "/events",
    response_model=List[dict],
    summary="Get behavior events",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_behavior_events(
    run_id: str,
    entity_id: Optional[str] = Query(default=None, description="Filter by entity ID"),
    category: Optional[str] = Query(default=None, description="Filter by behavior category"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    try:
        run_id = sanitize_id(run_id)
        if entity_id:
            entity_id = sanitize_id(entity_id)
        if category:
            category = sanitize_id(category)
        
        filters = {"run_id": run_id, "limit": limit, "offset": offset}
        if entity_id:
            filters["entity_id"] = entity_id
        if category:
            filters["category"] = category
            
        events = adapter.query_behavior_events(filters)
        return [e.model_dump() for e in events]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/entities/{entity_id}/timeline",
    response_model=List[dict],
    summary="Get behavior timeline for an entity",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_entity_behavior_timeline(
    entity_id: str,
    run_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    try:
        run_id = sanitize_id(run_id)
        entity_id = sanitize_id(entity_id)
        
        filters = {"run_id": run_id, "entity_id": entity_id, "limit": limit, "offset": offset}
        events = adapter.query_behavior_events(filters)
        return [e.model_dump() for e in events]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/entities/{entity_id}/episodes",
    response_model=List[dict],
    summary="Get behavior episodes for an entity",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_entity_behavior_episodes(
    entity_id: str,
    run_id: str,
    category: Optional[str] = Query(default=None, description="Filter by category"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    try:
        run_id = sanitize_id(run_id)
        entity_id = sanitize_id(entity_id)
        if category:
            category = sanitize_id(category)
            
        filters = {"run_id": run_id, "entity_id": entity_id, "limit": limit, "offset": offset}
        if category:
            filters["category"] = category
            
        episodes = adapter.query_behavior_episodes(filters)
        return [ep.model_dump() for ep in episodes]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/runs/{run_id}/scorecard",
    response_model=dict,
    summary="Get run behavior scorecard",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_run_behavior_scorecard(run_id: str):
    try:
        run_id = sanitize_id(run_id)
        scorecards = adapter.query_run_behavior_scorecards({"run_id": run_id})
        if not scorecards:
            # Degrade gracefully returning empty dictionary / 404 behavior structure
            return {}
        return scorecards[0].model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/runs/{run_id}/insights",
    response_model=List[dict],
    summary="Get run behavior insights",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_run_behavior_insights(run_id: str):
    try:
        run_id = sanitize_id(run_id)
        insights = adapter.query_behavior_insights({"run_id": run_id})
        return [i.model_dump() for i in insights]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/runs/{run_id}/cohorts",
    response_model=List[dict],
    summary="Get run cohorts report",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def get_run_cohorts(run_id: str):
    try:
        run_id = sanitize_id(run_id)
        cohorts = adapter.query_cohort_behavior_reports({"run_id": run_id})
        return [c.model_dump() for c in cohorts]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/compare",
    response_model=dict,
    summary="Compare behavior between run and baseline",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}}
)
async def compare_run_behavior(
    run_id: str = Query(..., description="Variant run ID"),
    baseline_run_id: str = Query(..., description="Baseline run ID")
):
    try:
        run_id = sanitize_id(run_id)
        baseline_run_id = sanitize_id(baseline_run_id)
        
        comparisons = adapter.query_run_behavior_comparisons({"run_id": run_id})
        if not comparisons:
            return {}
        return comparisons[0].model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
