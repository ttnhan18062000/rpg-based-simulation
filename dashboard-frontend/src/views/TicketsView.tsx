import { useEffect, useMemo, useState } from 'react'
import { fetchTickets, type FetchTicketsParams, type TicketSummary } from '@/api'

export interface TicketsViewProps {
  onSelectRun: (runId: string) => void
}

type FilterDimension = 'tier' | 'layer' | 'status' | 'priority'
type SortableColumn = FilterDimension | 'tag'
type SortDirection = 'asc' | 'desc'
type DateSort = 'date_asc' | 'date_desc'

interface FilterState {
  tier: string
  layer: string
  status: string
  priority: string
  tags: string[]
}

interface ColumnSort {
  column: SortableColumn
  direction: SortDirection
}

const EMPTY_FILTERS: FilterState = { tier: '', layer: '', status: '', priority: '', tags: [] }

function distinctValues(tickets: TicketSummary[], pick: (ticket: TicketSummary) => string | null): string[] {
  const values = new Set<string>()
  for (const ticket of tickets) {
    const value = pick(ticket)
    if (value) values.add(value)
  }
  return Array.from(values).sort()
}

function distinctTags(tickets: TicketSummary[]): string[] {
  const values = new Set<string>()
  for (const ticket of tickets) {
    for (const tag of ticket.tags) values.add(tag)
  }
  return Array.from(values).sort()
}

// "status" here means TicketSummary.workflow_status (the body `## Status`
// section), matching the backend's `status` query param semantics
// (ingest.py's get_tickets compares it against workflow_status, not the
// frontmatter `status` field) — not the frontmatter `status` column.
function columnSortKey(ticket: TicketSummary, column: SortableColumn): string | null {
  if (column === 'tier') return ticket.tier
  if (column === 'layer') return ticket.layer
  if (column === 'status') return ticket.workflow_status
  if (column === 'priority') return ticket.priority
  return ticket.tags[0] ?? null
}

function sortRows(rows: TicketSummary[], sort: ColumnSort): TicketSummary[] {
  const multiplier = sort.direction === 'asc' ? 1 : -1
  return [...rows].sort((a, b) => {
    const aValue = columnSortKey(a, sort.column)
    const bValue = columnSortKey(b, sort.column)
    if (aValue === null && bValue === null) return 0
    if (aValue === null) return 1
    if (bValue === null) return -1
    return aValue.localeCompare(bValue) * multiplier
  })
}

function buildFetchParams(filters: FilterState, dateSort: DateSort): FetchTicketsParams {
  return {
    tier: filters.tier || undefined,
    layer: filters.layer || undefined,
    status: filters.status || undefined,
    priority: filters.priority || undefined,
    tags: filters.tags.length > 0 ? filters.tags : undefined,
    sort: dateSort,
  }
}

function removeTag(tags: string[], tag: string): string[] {
  return tags.reduce<string[]>((remaining, existing) => {
    if (existing !== tag) remaining.push(existing)
    return remaining
  }, [])
}

interface FilterSelectProps {
  label: string
  testId: string
  value: string
  options: string[]
  onChange: (value: string) => void
}

function FilterSelect({ label, testId, value, options, onChange }: FilterSelectProps) {
  return (
    <label className="flex flex-col text-[11px] text-text-secondary gap-0.5">
      {label}
      <select
        data-testid={testId}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="bg-bg-tertiary border border-border rounded-md px-2 py-1 text-text-primary"
      >
        <option value="">All</option>
        {options.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </label>
  )
}

export function TicketsView({ onSelectRun }: TicketsViewProps) {
  const [rows, setRows] = useState<TicketSummary[]>([])
  const [optionsSource, setOptionsSource] = useState<TicketSummary[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS)
  const [dateSort, setDateSort] = useState<DateSort>('date_desc')
  const [columnSort, setColumnSort] = useState<ColumnSort | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadInitial() {
      setIsLoading(true)
      setError(null)
      try {
        const result = await fetchTickets({})
        if (!cancelled) {
          setRows(result)
          setOptionsSource(result)
          setIsLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err : new Error(String(err)))
          setIsLoading(false)
        }
      }
    }

    loadInitial()
    return () => {
      cancelled = true
    }
  }, [])

  async function applyFilters(nextFilters: FilterState) {
    setFilters(nextFilters)
    setError(null)
    try {
      const result = await fetchTickets(buildFetchParams(nextFilters, dateSort))
      setRows(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    }
  }

  async function toggleDateSort() {
    const nextDateSort: DateSort = dateSort === 'date_desc' ? 'date_asc' : 'date_desc'
    setDateSort(nextDateSort)
    setError(null)
    try {
      const result = await fetchTickets(buildFetchParams(filters, nextDateSort))
      setRows(result)
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    }
  }

  function toggleColumnSort(column: SortableColumn) {
    setColumnSort((current) => {
      if (current !== null && current.column === column) {
        return { column, direction: current.direction === 'asc' ? 'desc' : 'asc' }
      }
      return { column, direction: 'asc' }
    })
  }

  function toggleTag(tag: string) {
    const nextTags = filters.tags.includes(tag) ? removeTag(filters.tags, tag) : [...filters.tags, tag]
    applyFilters({ ...filters, tags: nextTags })
  }

  const displayedRows = useMemo(
    () => (columnSort === null ? rows : sortRows(rows, columnSort)),
    [rows, columnSort],
  )

  if (isLoading) {
    return (
      <div data-testid="tickets-view" className="p-6 text-text-secondary">
        Loading tickets…
      </div>
    )
  }

  return (
    <div data-testid="tickets-view" className="flex flex-col h-full p-6 gap-4 overflow-auto">
      {error && (
        <div className="text-accent-red text-[11px]">Failed to load tickets: {error.message}</div>
      )}

      <div className="flex flex-wrap items-end gap-3" data-testid="tickets-filter-bar">
        <FilterSelect
          label="Tier"
          testId="filter-tier"
          value={filters.tier}
          options={distinctValues(optionsSource, (ticket) => ticket.tier)}
          onChange={(value) => applyFilters({ ...filters, tier: value })}
        />
        <FilterSelect
          label="Layer"
          testId="filter-layer"
          value={filters.layer}
          options={distinctValues(optionsSource, (ticket) => ticket.layer)}
          onChange={(value) => applyFilters({ ...filters, layer: value })}
        />
        <FilterSelect
          label="Status"
          testId="filter-status"
          value={filters.status}
          options={distinctValues(optionsSource, (ticket) => ticket.workflow_status)}
          onChange={(value) => applyFilters({ ...filters, status: value })}
        />
        <FilterSelect
          label="Priority"
          testId="filter-priority"
          value={filters.priority}
          options={distinctValues(optionsSource, (ticket) => ticket.priority)}
          onChange={(value) => applyFilters({ ...filters, priority: value })}
        />
        <div className="flex flex-wrap items-center gap-1" data-testid="filter-tags">
          {distinctTags(optionsSource).map((tag) => {
            const active = filters.tags.includes(tag)
            return (
              <button
                key={tag}
                type="button"
                data-testid={`filter-tag-${tag}`}
                aria-pressed={active}
                onClick={() => toggleTag(tag)}
                className={`px-2 py-0.5 rounded-full text-[11px] border ${
                  active
                    ? 'bg-accent-blue/15 text-accent-blue border-accent-blue'
                    : 'text-text-secondary border-border'
                }`}
              >
                {tag}
              </button>
            )
          })}
        </div>
      </div>

      <table className="text-[11px] w-full border-collapse" data-testid="tickets-table">
        <thead>
          <tr className="text-left text-text-secondary border-b border-border">
            <th className="py-1 pr-3">Ticket</th>
            <th className="py-1 pr-3">Title</th>
            <th className="py-1 pr-3 cursor-pointer" data-testid="col-header-tier" onClick={() => toggleColumnSort('tier')}>
              Tier
            </th>
            <th className="py-1 pr-3 cursor-pointer" data-testid="col-header-layer" onClick={() => toggleColumnSort('layer')}>
              Layer
            </th>
            <th className="py-1 pr-3">Status</th>
            <th className="py-1 pr-3 cursor-pointer" data-testid="col-header-status" onClick={() => toggleColumnSort('status')}>
              Workflow Status
            </th>
            <th className="py-1 pr-3 cursor-pointer" data-testid="col-header-priority" onClick={() => toggleColumnSort('priority')}>
              Priority
            </th>
            <th className="py-1 pr-3">Type</th>
            <th className="py-1 pr-3 cursor-pointer" data-testid="col-header-tag" onClick={() => toggleColumnSort('tag')}>
              Tags
            </th>
            <th className="py-1 pr-3 cursor-pointer" data-testid="col-header-date" onClick={toggleDateSort}>
              Date
            </th>
            <th className="py-1 pr-3">Lifecycle</th>
            <th className="py-1 pr-3">Linked Runs</th>
          </tr>
        </thead>
        <tbody>
          {displayedRows.map((ticket) => (
            <tr
              key={ticket.ticket_id}
              data-testid={`ticket-row-${ticket.ticket_id}`}
              className="border-b border-border align-top"
            >
              <td className="py-1 pr-3">{ticket.ticket_id}</td>
              <td className="py-1 pr-3">{ticket.title}</td>
              <td className="py-1 pr-3" data-testid={`tier-cell-${ticket.ticket_id}`}>
                {ticket.tier}
              </td>
              <td className="py-1 pr-3">{ticket.layer}</td>
              <td className="py-1 pr-3">{ticket.status}</td>
              <td className="py-1 pr-3">{ticket.workflow_status}</td>
              <td className="py-1 pr-3" data-testid={`priority-cell-${ticket.ticket_id}`}>
                {ticket.priority}
              </td>
              <td className="py-1 pr-3" data-testid={`type-cell-${ticket.ticket_id}`}>
                {ticket.ticket_type}
              </td>
              <td className="py-1 pr-3">{ticket.tags.join(', ')}</td>
              <td className="py-1 pr-3">{ticket.date}</td>
              <td className="py-1 pr-3">{ticket.lifecycle_state}</td>
              <td className="py-1 pr-3" data-testid={`linked-runs-${ticket.ticket_id}`}>
                {ticket.matching_runs.length > 0 && (
                  <div className="flex flex-col gap-0.5">
                    {ticket.matching_runs.map((run) => (
                      <button
                        key={run.run_id}
                        type="button"
                        data-testid={`linked-run-link-${ticket.ticket_id}-${run.run_id}`}
                        onClick={() => onSelectRun(run.run_id)}
                        className="text-accent-blue text-left hover:underline"
                      >
                        {run.run_id} · {run.final_status}
                      </button>
                    ))}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
