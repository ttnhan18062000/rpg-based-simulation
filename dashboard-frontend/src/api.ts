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

export interface FetchTicketsParams {
  tier?: string
  layer?: string
  status?: string
  priority?: string
  tags?: string[]
  lifecycle?: string
  q?: string
  sort?: 'date_asc' | 'date_desc'
}

export async function fetchTickets(params: FetchTicketsParams = {}): Promise<TicketSummary[]> {
  const query = new URLSearchParams()
  if (params.tier !== undefined) query.set('tier', params.tier)
  if (params.layer !== undefined) query.set('layer', params.layer)
  if (params.status !== undefined) query.set('status', params.status)
  if (params.priority !== undefined) query.set('priority', params.priority)
  for (const tag of params.tags ?? []) query.append('tag', tag)
  if (params.lifecycle !== undefined) query.set('lifecycle', params.lifecycle)
  if (params.q !== undefined) query.set('q', params.q)
  if (params.sort !== undefined) query.set('sort', params.sort)

  const response = await fetch(`/api/tickets?${query.toString()}`)
  if (!response.ok) {
    throw new Error(`GET /api/tickets failed with status ${response.status}`)
  }
  return (await response.json()) as TicketSummary[]
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
