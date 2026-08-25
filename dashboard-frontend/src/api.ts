import { useEffect, useState } from 'react'

// Mirrors src/api/agent_ops_dashboard/models.py exactly. Do not add fields
// here that main.py's routes don't actually return.

export interface RunSummary {
  run_id: string
  workflow: string
  tier: string
  final_status: string
  start_ts: string | null
  end_ts: string | null
  duration_s: number | null
  agent_count: number
  is_inferred_active: boolean
  inferred_start_ts: string | null
}

export interface RunDetail extends RunSummary {
  ticket_title: string | null
  ticket_lifecycle_state: string | null
}

export interface RawToolCall {
  tool: string
  input_summary: string
  status: string
  duration_ms: number | null
  ts: string
}

export interface FileTouch {
  path: string
  tool: string
  ts: string
}

export interface TimelineEntry {
  seq: number
  phase: string | null
  agent: string | null
  status: string
  summary: string
  ts: string
  tool_call_count: number | null
  cost_proxy_score: number | null
  reason_code: string | null
  tool_calls: RawToolCall[]
}

export interface RunTimeline {
  run_id: string
  is_live: boolean
  entries: TimelineEntry[]
  live_tail: RawToolCall[]
  files_touched: FileTouch[]
}

export interface HealthStatus {
  status: string
  cache_last_rebuilt_ts: string | null
  cache_source_mtimes: Record<string, number>
  unparsed_lines: Record<string, number>
}

export interface FetchRunsParams {
  since?: string
  limit?: number
  offset?: number
  status?: string
  workflow?: string
}

export interface RunMatchSummary {
  run_id: string
  start_ts: string | null
  end_ts: string | null
  final_status: string
}

export interface TicketSummary {
  ticket_id: string
  title: string
  tier: string | null
  ticket_type: string | null
  priority: string | null
  layer: string
  status: string
  workflow_status: string | null
  tags: string[]
  date: string
  lifecycle_state: string
  matching_runs: RunMatchSummary[]
}

export interface TicketsFacets {
  tiers: string[]
  layers: string[]
  statuses: string[]
  priorities: string[]
  tags: string[]
}

export interface TicketsPage {
  items: TicketSummary[]
  total_count: number
  facets: TicketsFacets
}

export interface FetchTicketsParams {
  tier?: string
  layer?: string
  status?: string
  priority?: string
  tags?: string[]
  lifecycle?: string
  q?: string
  sort?: 'date_asc' | 'date_desc'
  limit?: number
  offset?: number
}

export async function fetchTickets(params: FetchTicketsParams = {}): Promise<TicketsPage> {
  const query = new URLSearchParams()
  if (params.tier !== undefined) query.set('tier', params.tier)
  if (params.layer !== undefined) query.set('layer', params.layer)
  if (params.status !== undefined) query.set('status', params.status)
  if (params.priority !== undefined) query.set('priority', params.priority)
  for (const tag of params.tags ?? []) query.append('tag', tag)
  if (params.lifecycle !== undefined) query.set('lifecycle', params.lifecycle)
  if (params.q !== undefined) query.set('q', params.q)
  if (params.sort !== undefined) query.set('sort', params.sort)
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))

  const response = await fetch(`/api/tickets?${query.toString()}`)
  if (!response.ok) {
    throw new Error(`GET /api/tickets failed with status ${response.status}`)
  }
  return (await response.json()) as TicketsPage
}

// --- Statistics (TCK-20260718-AGENTOPS-STATS-API / TCK-20260718-TICKET-CORPUS-REPORT) ---
// Mirrors src/api/agent_ops_dashboard/models.py's AgentMonitoringStats/TicketCorpusStats trees
// field-for-field, per this file's own established convention.

export interface RunSummaryStats {
  total: number
  done_count: number
  gate_fail_count: number
  avg_duration_min: number
  avg_agents: number
  total_agent_calls: number
}

export interface SubsystemTagStats {
  runs: number
  done: number
  gate_fails: number
}

export interface SkillTagStats {
  runs: number
  gate_hits: number | null
}

export interface TierDistributionStats {
  count: number
  scoped: number
  done: number
}

export interface SpendProxyStats {
  events_scored: number
  total: number
  avg: number
}

export interface SummaryQualityStats {
  empty_summaries_current: number
  legacy_event_count: number
  long_summaries: number
}

export interface SlowRunEntry {
  run_id: string
  duration_s: number | null
  final_status: string
  // TCK-20260822-DASHBOARD-DURATION-GAP-AWARE: sourced strictly from the sibling
  // TCK-20260822-DURATION-ACTIVE-IDLE-SPLIT's shared duration_utils computation — never
  // independently computed here. null when unavailable (e.g. unparseable start_ts/end_ts).
  active_duration_s: number | null
  idle_gap_s: number | null
}

export interface DurationOutlierEntry {
  run_id: string
  tier: string
  duration_s: number
  median: number
  ratio: number
  // See SlowRunEntry's identical fields above for provenance/null-handling.
  active_duration_s: number | null
  idle_gap_s: number | null
}

export interface CostProxyOutlierEntry {
  run_id: string
  seq: number | null
  phase: string
  agent: string
  cost_proxy_score: number
  median: number
  ratio: number
}

export interface OutlierStats {
  duration_s: DurationOutlierEntry[]
  cost_proxy_score: CostProxyOutlierEntry[]
}

export interface SkillUsageSection {
  total_skill_invocations: number
  unparseable: number
  per_skill: Record<string, number>
  per_skill_per_run: Record<string, Record<string, number>>
  derivation: string
}

export interface KgmcpCacheTicketStats {
  hit: number
  write: number
  reuse_rate: number | null
}

export interface KgmcpRepeatedRefetchEntry {
  cache_level: string | null
  run_id: string | null
  ticket_id: string
  agent: string
  gap_s: number
  prior_run_id: string | null
  prior_event_type: string | null
}

export interface KgmcpDeadWriteEntry {
  cache_level: string | null
  run_id: string | null
  ticket_id: string
  agent: string
  ts: number | null
}

export interface KgmcpCoverageStats {
  search_calls_total: number
  cache_events_total: number
  coverage_rate: number | null
}

export interface KgmcpCacheEfficiencyStats {
  total_hits: number
  total_writes: number
  overall_reuse_rate: number | null
  per_ticket: Record<string, KgmcpCacheTicketStats>
  per_agent: Record<string, KgmcpCacheTicketStats>
  repeated_refetch_window_seconds: number
  repeated_refetches: KgmcpRepeatedRefetchEntry[]
  dead_writes: KgmcpDeadWriteEntry[]
  dead_write_count: number
  coverage: KgmcpCoverageStats
  verdict: string
  verdict_explanation: string
  stale_attribution_count: number
  derivation: string
}

export interface AgentMonitoringStats {
  run_summary: RunSummaryStats
  gate_failure_breakdown: Record<string, number>
  reason_code_breakdown: Record<string, number>
  tag_breakdown_subsystem: Record<string, SubsystemTagStats>
  tag_breakdown_skill: Record<string, SkillTagStats>
  tier_distribution: Record<string, TierDistributionStats>
  agent_status_distribution: Record<string, Record<string, number>>
  phase_status_distribution: Record<string, Record<string, number>>
  spend_proxy_by_phase: Record<string, SpendProxyStats>
  spend_proxy_by_agent: Record<string, SpendProxyStats>
  summary_quality: SummaryQualityStats
  slow_runs: SlowRunEntry[]
  outliers: OutlierStats
  skill_usage: SkillUsageSection
  kgmcp_cache_efficiency: KgmcpCacheEfficiencyStats
}

export interface VelocityStats {
  by_day: Record<string, number>
  by_week: Record<string, number>
  unparseable_rows: number
}

export interface TicketDistributionStats {
  tier: Record<string, number>
  ticket_type: Record<string, number>
  priority: Record<string, number>
  layer: Record<string, number>
  layer_by_tier: Record<string, Record<string, number>>
}

export interface IncompleteArtifactEntry {
  ticket_id: string
  missing: string[]
}

export interface ArtifactCompletenessStats {
  complete_count: number
  incomplete_count: number
  total_checked: number
  incomplete: IncompleteArtifactEntry[]
}

export interface TicketCorpusStats {
  scanned_files: number
  included_tickets: number
  skipped: Record<string, number>
  velocity: VelocityStats
  distribution: TicketDistributionStats
  artifact_completeness: ArtifactCompletenessStats
}

export async function fetchAgentMonitoringStats(): Promise<AgentMonitoringStats> {
  const response = await fetch('/api/stats/agent-monitoring')
  if (!response.ok) {
    throw new Error(`GET /api/stats/agent-monitoring failed with status ${response.status}`)
  }
  return (await response.json()) as AgentMonitoringStats
}

export async function fetchTicketCorpusStats(): Promise<TicketCorpusStats> {
  const response = await fetch('/api/stats/tickets')
  if (!response.ok) {
    throw new Error(`GET /api/stats/tickets failed with status ${response.status}`)
  }
  return (await response.json()) as TicketCorpusStats
}

// --- Glossary (TCK-20260718-GLOSSARY-TOOLTIPS-FRONTEND) ---
// Mirrors src/api/agent_ops_dashboard/models.py's GlossaryEntry/GlossaryResponse exactly.
// Description text originates ONLY here (fetched from the backend) — never hardcoded as a
// literal string anywhere else in dashboard-frontend/src/*.tsx.

export interface GlossaryEntry {
  term: string
  category: string
  description: string
}

export type GlossaryTerms = Record<string, GlossaryEntry>

export async function fetchGlossary(): Promise<GlossaryTerms> {
  const response = await fetch('/api/glossary')
  if (!response.ok) {
    throw new Error(`GET /api/glossary failed with status ${response.status}`)
  }
  const data = (await response.json()) as { terms: GlossaryTerms }
  return data.terms
}

// Module-level cache — every `useGlossary()` caller across every mounted view shares this one
// promise, so the glossary is fetched exactly once per page load regardless of how many
// components use it, never once per hover and never once per component mount. Reset only by a
// full page reload (this dashboard has no client-side router/navigation that would need a
// manual invalidation path).
let _glossaryPromise: Promise<GlossaryTerms> | null = null

export function useGlossary(): GlossaryTerms {
  const [glossary, setGlossary] = useState<GlossaryTerms>({})

  useEffect(() => {
    let cancelled = false
    if (_glossaryPromise === null) {
      _glossaryPromise = fetchGlossary()
    }
    _glossaryPromise
      .then((terms) => {
        // Graceful degradation also covers a resolved-but-malformed response (e.g. a stubbed
        // fetch in a test that returns some other endpoint's shape, or a future backend change
        // that omits `terms`) — coerce to {} rather than trust the network response's shape
        // blindly, since a bad `terms` value here must never crash every view that uses
        // GlossaryTooltip.
        if (!cancelled) setGlossary(terms && typeof terms === 'object' ? terms : {})
      })
      .catch(() => {
        // Graceful degradation, per this ticket's architectural constraint: a glossary fetch
        // failure must never crash a view or block rendering the labels themselves — callers
        // just render without tooltips (GlossaryTooltip already handles an empty/missing entry).
        if (!cancelled) setGlossary({})
      })
    return () => {
      cancelled = true
    }
  }, [])

  return glossary
}

// Test-only escape hatch for the module-level cache above: within a single test file, every
// `render()` that mounts a view calling `useGlossary()` shares the SAME `_glossaryPromise` once
// it's been set — a later test's differently-mocked `/api/glossary` response is silently ignored
// if an earlier test in the same file already resolved the cache first. Production code has no
// reason to ever call this (a real page load never needs to re-fetch the glossary mid-session);
// test files that vary glossary content across multiple `it()` blocks must call this in
// `beforeEach`/`afterEach` to avoid cross-test pollution.
export function _resetGlossaryCacheForTests(): void {
  _glossaryPromise = null
}

export async function fetchRunTimeline(runId: string): Promise<RunTimeline> {
  const response = await fetch(`/api/runs/${encodeURIComponent(runId)}/timeline`)
  if (!response.ok) {
    throw new Error(`GET /api/runs/${runId}/timeline failed with status ${response.status}`)
  }
  return (await response.json()) as RunTimeline
}

export async function fetchRuns(params: FetchRunsParams = {}): Promise<RunSummary[]> {
  const query = new URLSearchParams()
  if (params.since !== undefined) query.set('since', params.since)
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))
  if (params.status !== undefined) query.set('status', params.status)
  if (params.workflow !== undefined) query.set('workflow', params.workflow)

  const response = await fetch(`/api/runs?${query.toString()}`)
  if (!response.ok) {
    throw new Error(`GET /api/runs failed with status ${response.status}`)
  }
  return (await response.json()) as RunSummary[]
}

// GET /api/runs has no total-count field: `since` bounds the candidate set but
// `limit`/`offset` still slice it, so a busy window silently truncates unless
// the caller loops on `offset` while a page comes back full.
const RUNS_PAGE_LIMIT = 100

async function fetchAllRunsSince(sinceIso: string): Promise<RunSummary[]> {
  const merged: RunSummary[] = []
  let offset = 0

  for (;;) {
    const page = await fetchRuns({ since: sinceIso, limit: RUNS_PAGE_LIMIT, offset })
    merged.push(...page)
    if (page.length < RUNS_PAGE_LIMIT) {
      break
    }
    offset += RUNS_PAGE_LIMIT
  }

  return merged
}

function mergeAndSortRuns(runs: RunSummary[]): RunSummary[] {
  const byId = new Map<string, RunSummary>()
  for (const run of runs) {
    byId.set(run.run_id, run)
  }
  return Array.from(byId.values()).sort((a, b) => {
    const aTs = a.start_ts ?? a.inferred_start_ts ?? ''
    const bTs = b.start_ts ?? b.inferred_start_ts ?? ''
    return bTs.localeCompare(aTs)
  })
}

export interface UseRunsPollingResult {
  runs: RunSummary[]
  isLoading: boolean
  error: Error | null
}

export function useRunsPolling(sinceIso: string, intervalMs = 5000): UseRunsPollingResult {
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const allRuns = await fetchAllRunsSince(sinceIso)
        if (!cancelled) {
          setRuns(mergeAndSortRuns(allRuns))
          setError(null)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    poll()
    const intervalId = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [sinceIso, intervalMs])

  return { runs, isLoading, error }
}

// --- Bulk run timelines (TCK-20260720-PROGRESS-TIMELINE-VIEW) ---
// Mirrors src/api/agent_ops_dashboard/models.py's BulkRunTimeline exactly.

export interface BulkRunTimeline {
  entries_by_run: Record<string, TimelineEntry[]>
}

async function fetchRunTimelines(params: {
  since?: string
  until?: string
  limit?: number
  offset?: number
}): Promise<BulkRunTimeline> {
  const query = new URLSearchParams()
  if (params.since !== undefined) query.set('since', params.since)
  if (params.until !== undefined) query.set('until', params.until)
  if (params.limit !== undefined) query.set('limit', String(params.limit))
  if (params.offset !== undefined) query.set('offset', String(params.offset))

  const response = await fetch(`/api/runs/timeline?${query.toString()}`)
  if (!response.ok) {
    throw new Error(`GET /api/runs/timeline failed with status ${response.status}`)
  }
  return (await response.json()) as BulkRunTimeline
}

const RUN_TIMELINES_PAGE_LIMIT = 100

async function fetchAllRunTimelinesSince(
  sinceIso: string,
  untilIso?: string,
): Promise<Record<string, TimelineEntry[]>> {
  const merged: Record<string, TimelineEntry[]> = {}
  let offset = 0

  for (;;) {
    const page = await fetchRunTimelines({
      since: sinceIso,
      until: untilIso,
      limit: RUN_TIMELINES_PAGE_LIMIT,
      offset,
    })
    const pageRunCount = Object.keys(page.entries_by_run).length
    Object.assign(merged, page.entries_by_run)
    if (pageRunCount < RUN_TIMELINES_PAGE_LIMIT) {
      break
    }
    offset += RUN_TIMELINES_PAGE_LIMIT
  }

  return merged
}

export interface UseRunTimelinesPollingResult {
  entriesByRun: Record<string, TimelineEntry[]>
  isLoading: boolean
  error: Error | null
}

export function useRunTimelinesPolling(
  sinceIso: string,
  intervalMs = 5000,
  untilIso?: string,
): UseRunTimelinesPollingResult {
  const [entriesByRun, setEntriesByRun] = useState<Record<string, TimelineEntry[]>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const merged = await fetchAllRunTimelinesSince(sinceIso, untilIso)
        if (!cancelled) {
          setEntriesByRun(merged)
          setError(null)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    poll()
    const intervalId = setInterval(poll, intervalMs)
    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [sinceIso, intervalMs, untilIso])

  return { entriesByRun, isLoading, error }
}
