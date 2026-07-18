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
}

export interface AgentMonitoringStats {
  run_summary: RunSummaryStats
  gate_failure_breakdown: Record<string, number>
  reason_code_breakdown: Record<string, number>
  tag_breakdown_subsystem: Record<string, SubsystemTagStats>
  tag_breakdown_skill: Record<string, SkillTagStats>
  tier_distribution: Record<string, TierDistributionStats>
  agent_status_distribution: Record<string, Record<string, number>>
  spend_proxy_by_phase: Record<string, SpendProxyStats>
  spend_proxy_by_agent: Record<string, SpendProxyStats>
  summary_quality: SummaryQualityStats
  slow_runs: SlowRunEntry[]
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
