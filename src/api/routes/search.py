from __future__ import annotations
import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.observability.warehouse.factory import get_warehouse_adapter
from src.observability.reporting.history_query import sanitize_id

# Initialize Router
router = APIRouter(prefix="/observability/search", tags=["Search"])

# System Logger
logger = logging.getLogger("api.observability.search")

class ErrorResponse(BaseModel):
    detail: str


@router.get(
    "/runs",
    response_model=List[dict],
    summary="Query historical runs",
    description="Query run records from the active warehouse based on scenario name and status filters.",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def search_runs(
    scenario_name: Optional[str] = Query(default=None, description="Filter by scenario name"),
    status: Optional[str] = Query(default=None, description="Filter by run status"),
    sort: Optional[str] = Query(default=None, description="Sort order: health_score_asc, health_score_desc"),
    limit: int = Query(default=50, ge=1, le=100, description="Limit result count"),
    offset: int = Query(default=0, ge=0, description="Offset result count")
):
    try:
        adapter = get_warehouse_adapter()
        filters = {
            "limit": limit,
            "offset": offset
        }
        if scenario_name:
            filters["scenario_name"] = scenario_name
        if status:
            filters["status"] = status
        if sort:
            filters["sort"] = sort

        results = adapter.query_runs(filters)
        
        # Audit Logging
        logger.info(
            "Search runs: scenario_name=%s status=%s sort=%s limit=%d result_count=%d",
            scenario_name or "ALL",
            status or "ALL",
            sort or "DEFAULT",
            limit,
            len(results)
        )
        return [r.model_dump() for r in results]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed search runs query: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to query historical runs: {e}")


@router.get(
    "/events",
    response_model=List[dict],
    summary="Query simulation events",
    description="Query simulation events from the active warehouse. Supports filters for entity, tick bounds, and severity.",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def search_events(
    run_id: str = Query(..., description="Mandatory run identifier to target"),
    entity_id: Optional[str] = Query(default=None, description="Filter by specific entity"),
    tick_start: Optional[int] = Query(default=None, ge=0, description="Start tick filter"),
    tick_end: Optional[int] = Query(default=None, ge=0, description="End tick filter"),
    severity: Optional[str] = Query(default=None, description="Filter by severity level"),
    limit: int = Query(default=50, ge=1, le=100, description="Limit result count"),
    offset: int = Query(default=0, ge=0, description="Offset result count")
):
    try:
        # Enforce validation to prevent path traversal
        run_id = sanitize_id(run_id)
        if tick_start is not None and tick_end is not None and tick_start > tick_end:
            raise ValueError("tick_start cannot be greater than tick_end")

        adapter = get_warehouse_adapter()
        filters = {
            "run_id": run_id,
            "limit": limit,
            "offset": offset
        }
        if entity_id:
            filters["entity_id"] = entity_id
        if tick_start is not None:
            filters["tick_start"] = tick_start
        if tick_end is not None:
            filters["tick_end"] = tick_end
        if severity:
            filters["severity"] = severity

        results = adapter.query_events(filters)

        # Audit Logging
        logger.info(
            "Search events: run_id=%s entity_id_present=%s tick_range=%s severity=%s limit=%d result_count=%d",
            run_id,
            str(entity_id is not None),
            f"{tick_start or 0}-{tick_end or 'inf'}",
            severity or "ALL",
            limit,
            len(results)
        )
        return [r.model_dump() for r in results]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed search events query: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to query simulation events: {e}")


@router.get(
    "/anomalies",
    response_model=List[dict],
    summary="Query detected anomalies",
    description="Query anomalies from the active warehouse.",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def search_anomalies(
    run_id: str = Query(..., description="Run identifier"),
    rule_id: Optional[str] = Query(default=None, description="Filter by specific rules"),
    limit: int = Query(default=50, ge=1, le=100, description="Limit result count"),
    offset: int = Query(default=0, ge=0, description="Offset result count")
):
    try:
        run_id = sanitize_id(run_id)
        
        adapter = get_warehouse_adapter()
        filters = {
            "run_id": run_id,
            "limit": limit,
            "offset": offset
        }
        if rule_id:
            filters["rule_id"] = rule_id

        results = adapter.query_anomalies(filters)

        # Audit Logging
        logger.info(
            "Search anomalies: run_id=%s rule_id=%s limit=%d result_count=%d",
            run_id,
            rule_id or "ALL",
            limit,
            len(results)
        )
        return [r.model_dump() for r in results]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed search anomalies query: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to query anomalies: {e}")


@router.get(
    "/entity-timeline",
    response_model=List[dict],
    summary="Aggregate entity timeline",
    description="Aggregates and chronologically sorts all events and anomalies for a given entity_id across a run_id.",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_entity_timeline(
    run_id: str = Query(..., description="Run identifier"),
    entity_id: str = Query(..., description="Entity identifier")
):
    try:
        run_id = sanitize_id(run_id)
        entity_id = sanitize_id(entity_id)

        adapter = get_warehouse_adapter()
        
        # 1. Query matching events
        event_filters = {
            "run_id": run_id,
            "entity_id": entity_id,
            "limit": 1000,
            "offset": 0
        }
        events = adapter.query_events(event_filters)

        # 2. Query all anomalies for run and filter locally by checking presence of entity_id
        anomaly_filters = {
            "run_id": run_id,
            "limit": 1000,
            "offset": 0
        }
        anomalies = adapter.query_anomalies(anomaly_filters)
        
        filtered_anomalies = []
        for anomaly in anomalies:
            is_affected = False
            try:
                evidence = json.loads(anomaly.evidence_json)
                if "entity_id" in evidence and str(evidence["entity_id"]) == str(entity_id):
                    is_affected = True
                elif "actor_id" in evidence and str(evidence["actor_id"]) == str(entity_id):
                    is_affected = True
                elif any(str(v) == str(entity_id) for v in evidence.values() if isinstance(v, (str, int))):
                    is_affected = True
            except Exception:
                pass

            if not is_affected and entity_id in anomaly.message:
                is_affected = True
            
            if is_affected:
                filtered_anomalies.append(anomaly)

        # 3. Combine and sort
        timeline = []
        for ev in events:
            timeline.append({
                "type": "event",
                "tick": ev.tick,
                "event_type": ev.event_type,
                "event_category": ev.event_category,
                "severity": ev.severity,
                "message": ev.message,
                "timestamp": ev.created_at,
                "details": json.loads(ev.payload_json) if ev.payload_json else {}
            })

        for an in filtered_anomalies:
            timeline.append({
                "type": "anomaly",
                "tick": an.tick_start,
                "tick_end": an.tick_end,
                "rule_id": an.rule_id,
                "severity": an.severity,
                "message": an.message,
                "timestamp": None,
                "details": json.loads(an.evidence_json) if an.evidence_json else {}
            })

        timeline.sort(key=lambda x: x["tick"])

        # Audit Logging
        logger.info(
            "Search entity-timeline: run_id=%s entity_id=%s events_count=%d anomalies_count=%d total=%d",
            run_id,
            entity_id,
            len(events),
            len(filtered_anomalies),
            len(timeline)
        )
        return timeline
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed entity-timeline query: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to aggregate entity timeline: {e}")


@router.get(
    "/metric-trend",
    response_model=List[dict],
    summary="Retrieve run metric trends",
    description="Returns performance/simulation metric windows timeseries trend metrics for a given run.",
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_metric_trend(
    run_id: str = Query(..., description="Run identifier"),
    limit: int = Query(default=100, ge=1, le=500, description="Limit metric trend data points"),
    offset: int = Query(default=0, ge=0, description="Offset result count")
):
    try:
        run_id = sanitize_id(run_id)

        adapter = get_warehouse_adapter()
        filters = {
            "run_id": run_id,
            "limit": limit,
            "offset": offset
        }
        results = adapter.query_metric_windows(filters)

        # Audit Logging
        logger.info(
            "Search metric-trend: run_id=%s limit=%d result_count=%d",
            run_id,
            limit,
            len(results)
        )
        return [r.model_dump() for r in results]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed metric-trend query: %s", str(e))
        raise HTTPException(status_code=500, detail=f"Failed to query metric trends: {e}")
