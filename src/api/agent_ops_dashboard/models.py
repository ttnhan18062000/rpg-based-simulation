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
    provider: Optional[str] = None
    execution_id: Optional[str] = None
    ticket_id: Optional[str] = None
    identity_provenance: str = "legacy"


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


# --- Agent-monitoring statistics (TCK-20260718-AGENTOPS-STATS-API) ---
# Field-for-field mirror of tools/agent-monitoring/generate_retro.py::compute_retro_metrics()'s
# return dict — that function is the single source of truth for these numbers (also consumed
# unchanged by the CLI retro report); these models only give its output a typed API-boundary
# shape, never recompute anything.


class RunSummaryStats(BaseModel):
    total: int
    done_count: int
    gate_fail_count: int
    avg_duration_min: int
    avg_agents: float
    total_agent_calls: int


class SubsystemTagStats(BaseModel):
    runs: int
    done: int
    gate_fails: int


class SkillTagStats(BaseModel):
    runs: int
    gate_hits: Optional[int] = None


class TierDistributionStats(BaseModel):
    count: int
    scoped: int
    done: int


class SpendProxyStats(BaseModel):
    events_scored: int
    total: float
    avg: float


class SummaryQualityStats(BaseModel):
    empty_summaries_current: int
    legacy_event_count: int
    long_summaries: int


class SlowRunEntry(BaseModel):
    run_id: str
    duration_s: Optional[int] = None
    final_status: str


class DurationOutlierEntry(BaseModel):
    run_id: str
    tier: str
    duration_s: int
    median: float
    ratio: float


class CostProxyOutlierEntry(BaseModel):
    run_id: str
    seq: Optional[int] = None
    phase: str
    agent: str
    cost_proxy_score: float
    median: float
    ratio: float


class OutlierStats(BaseModel):
    duration_s: List[DurationOutlierEntry]
    cost_proxy_score: List[CostProxyOutlierEntry]


# --- Skill Usage (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD) ---
# Field-for-field mirror of tools/agent-monitoring/generate_retro.py::build_skill_usage_section()'s
# return dict, wired into compute_retro_metrics()'s own `skill_usage` key (see that function's
# `tools` parameter) — the raw per-skill *invocation* counts the CLI retro report already renders
# under its own "## Skill Usage" heading, now reaching the dashboard JSON API for the first time.


class SkillUsageSection(BaseModel):
    total_skill_invocations: int
    unparseable: int
    per_skill: Dict[str, int]
    per_skill_per_run: Dict[str, Dict[str, int]]
    derivation: str


# --- KGMCP Cache Efficiency (TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-
# DASHBOARD) ---
# Field-for-field mirror of tools/agent-monitoring/generate_retro.py::
# compute_kgmcp_cache_efficiency_metrics()'s return dict — per-ticket/per-agent Level 1/Level 2
# KGMCP retrieval-cache hit/write counts, reuse rate, repeated-refetch and dead-write detection,
# real-usage coverage, and a rule-based verdict/explanation summarizing all four signals.


class KgmcpCacheTicketStats(BaseModel):
    hit: int
    write: int
    reuse_rate: Optional[float] = None


class KgmcpRepeatedRefetchEntry(BaseModel):
    cache_level: Optional[str] = None
    run_id: Optional[str] = None
    ticket_id: str
    agent: str
    gap_s: float
    prior_run_id: Optional[str] = None
    prior_event_type: Optional[str] = None


class KgmcpDeadWriteEntry(BaseModel):
    cache_level: Optional[str] = None
    run_id: Optional[str] = None
    ticket_id: str
    agent: str
    ts: Optional[float] = None


class KgmcpCoverageStats(BaseModel):
    search_calls_total: int
    cache_events_total: int
    coverage_rate: Optional[float] = None


class KgmcpCacheEfficiencyStats(BaseModel):
    total_hits: int
    total_writes: int
    overall_reuse_rate: Optional[float] = None
    per_ticket: Dict[str, KgmcpCacheTicketStats]
    per_agent: Dict[str, KgmcpCacheTicketStats]
    repeated_refetch_window_seconds: int
    repeated_refetches: List[KgmcpRepeatedRefetchEntry]
    dead_writes: List[KgmcpDeadWriteEntry]
    dead_write_count: int
    coverage: KgmcpCoverageStats
    verdict: str
    verdict_explanation: str
    stale_attribution_count: int
    derivation: str


class AgentMonitoringStats(BaseModel):
    run_summary: RunSummaryStats
    gate_failure_breakdown: Dict[str, int]
    reason_code_breakdown: Dict[str, int]
    tag_breakdown_subsystem: Dict[str, SubsystemTagStats]
    tag_breakdown_skill: Dict[str, SkillTagStats]
    tier_distribution: Dict[str, TierDistributionStats]
    agent_status_distribution: Dict[str, Dict[str, int]]
    phase_status_distribution: Dict[str, Dict[str, int]]
    spend_proxy_by_phase: Dict[str, SpendProxyStats]
    spend_proxy_by_agent: Dict[str, SpendProxyStats]
    summary_quality: SummaryQualityStats
    slow_runs: List[SlowRunEntry]
    outliers: OutlierStats
    skill_usage: SkillUsageSection
    kgmcp_cache_efficiency: KgmcpCacheEfficiencyStats


# --- Ticket-corpus statistics (TCK-20260718-TICKET-CORPUS-REPORT) ---
# Field-for-field mirror of tools/ticket_stats_report.py::build_json_report()'s shape — that
# module is the single source of truth for these numbers, also consumed unchanged by its own CLI.


class VelocityStats(BaseModel):
    by_day: Dict[str, int]
    by_week: Dict[str, int]
    unparseable_rows: int


class TicketDistributionStats(BaseModel):
    tier: Dict[str, int]
    ticket_type: Dict[str, int]
    priority: Dict[str, int]
    layer: Dict[str, int]
    layer_by_tier: Dict[str, Dict[str, int]]


class IncompleteArtifactEntry(BaseModel):
    ticket_id: str
    missing: List[str]


class ArtifactCompletenessStats(BaseModel):
    complete_count: int
    incomplete_count: int
    total_checked: int
    incomplete: List[IncompleteArtifactEntry]


class TicketCorpusStats(BaseModel):
    scanned_files: int
    included_tickets: int
    skipped: Dict[str, int]
    velocity: VelocityStats
    distribution: TicketDistributionStats
    artifact_completeness: ArtifactCompletenessStats


# --- Glossary (TCK-20260718-GLOSSARY-API) ---
# Backend-owned tooltip descriptions for the dashboard's enum-like labels (ticket status/tier/
# priority/type, run/gate status, reason codes, event status, layer). Field-for-field shape over
# tools/glossary_registry.py's registry entries, plus layer entries synthesized at read time from
# tools/layer_registry.py's own `note` field (never duplicated into a second file) — see
# DashboardCache.get_glossary()'s docstring for why. The whole point of this model existing is so
# the frontend never hardcodes description text: it fetches this once and looks up by term.


class GlossaryEntry(BaseModel):
    term: str
    category: str
    description: str


class GlossaryResponse(BaseModel):
    terms: Dict[str, GlossaryEntry]


# --- Bulk run timeline (TCK-20260720-BULK-RUN-TIMELINE) ---
# Bulk sibling of RunTimeline: entries for every run in a since/until-bounded,
# limit/offset-paginated window, keyed by run_id. No files_touched/live_tail/is_live
# per run — see DashboardCache.get_bulk_timeline()'s docstring for why.


class BulkRunTimeline(BaseModel):
    entries_by_run: Dict[str, List[TimelineEntry]]
