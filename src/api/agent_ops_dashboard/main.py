"""Agent Ops Dashboard backend — standalone FastAPI app.

Read-only viewer over tickets/{inprogress,done,todos}/ and
agent-monitoring/{runs,events,tools}.jsonl. Not mounted on src/api/server.py
(the main simulation API) — a separate product/port, since this dashboard
never touches AuthoritativeState. No StaticFiles mount here (owned by the
sibling AGENTOPS-BUILD-SERVE ticket).
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query

from src.api.agent_ops_dashboard.ingest import DashboardCache
from src.api.agent_ops_dashboard.models import (
    HealthStatus,
    RunDetail,
    RunSummary,
    RunTimeline,
    TicketFacets,
    TicketsPage,
)

app = FastAPI(title="Agent Ops Dashboard API")

_cache = DashboardCache()


@app.get("/api/tickets", response_model=TicketsPage)
async def list_tickets(
    tier: Optional[str] = None,
    layer: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tag: Optional[List[str]] = Query(default=None),
    lifecycle: Optional[str] = None,
    q: Optional[str] = None,
    sort: str = "date_desc",
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TicketsPage:
    result = _cache.get_tickets(
        tier=tier,
        layer=layer,
        status=status,
        priority=priority,
        tags=tag,
        lifecycle=lifecycle,
        q=q,
        sort=sort,
        limit=limit,
        offset=offset,
    )
    return TicketsPage(
        items=list(result),
        total_count=result.total_count,
        facets=TicketFacets(**result.facets),
    )


@app.get("/api/runs", response_model=List[RunSummary])
async def list_runs(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
    workflow: Optional[str] = None,
    since: Optional[str] = None,
) -> List[RunSummary]:
    return _cache.get_runs(limit=limit, offset=offset, status=status, workflow=workflow, since=since)


@app.get("/api/runs/{run_id}", response_model=RunDetail)
async def get_run(run_id: str) -> RunDetail:
    detail = _cache.get_run(run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return detail


@app.get("/api/runs/{run_id}/timeline", response_model=RunTimeline)
async def get_run_timeline(run_id: str) -> RunTimeline:
    timeline = _cache.get_timeline(run_id)
    if timeline is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return timeline


@app.get("/api/health", response_model=HealthStatus)
async def get_health() -> HealthStatus:
    return _cache.get_health()
