"""Typed Pydantic response models for the Agent Ops Dashboard backend.

These are the only shapes routes in main.py ever return. Internal ingest.py
parsing structures (raw dicts from tickets/**/*.md or agent-monitoring/*.jsonl)
are converted to these before crossing the route boundary — never returned
directly, and never `.model_dump()`'d into a `response_model=dict` route
(the pattern src/api/routes/history.py uses and this module deliberately does
not mirror).
"""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RunMatchSummary(BaseModel):
    run_id: str
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    final_status: str


class TicketSummary(BaseModel):
    ticket_id: str
    title: str
    tier: Optional[str] = None
    ticket_type: Optional[str] = None
    priority: Optional[str] = None
    layer: str
    status: str
    workflow_status: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    date: str
    lifecycle_state: str
    matching_runs: List[RunMatchSummary] = Field(default_factory=list)


class TicketFacets(BaseModel):
    tiers: List[str]
    layers: List[str]
    statuses: List[str]
    priorities: List[str]
    tags: List[str]


class TicketsPage(BaseModel):
    items: List[TicketSummary]
    total_count: int
    facets: TicketFacets


class RawToolCall(BaseModel):
    tool: str
    input_summary: str
    status: str
    duration_ms: Optional[int] = None
    ts: str


class FileTouch(BaseModel):
    path: str
    tool: str
    ts: str


class TimelineEntry(BaseModel):
    seq: int
    phase: Optional[str] = None
    agent: Optional[str] = None
    status: str
    summary: str
    ts: str
    tool_call_count: Optional[int] = None
    cost_proxy_score: Optional[float] = None
    reason_code: Optional[str] = None
    tool_calls: List[RawToolCall] = Field(default_factory=list)


class RunSummary(BaseModel):
    run_id: str
    workflow: str
    tier: str
    final_status: str
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    duration_s: Optional[int] = None
    agent_count: int
    is_inferred_active: bool
    inferred_start_ts: Optional[str] = None


class RunDetail(RunSummary):
    ticket_title: Optional[str] = None
    ticket_lifecycle_state: Optional[str] = None


class RunTimeline(BaseModel):
    run_id: str
    is_live: bool
    entries: List[TimelineEntry]
    live_tail: List[RawToolCall] = Field(default_factory=list)
    files_touched: List[FileTouch] = Field(default_factory=list)


class HealthStatus(BaseModel):
    status: str
    cache_last_rebuilt_ts: Optional[str] = None
    cache_source_mtimes: Dict[str, float]
    unparsed_lines: Dict[str, int]
