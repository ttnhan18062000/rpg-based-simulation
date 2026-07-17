import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { compile } from '@tailwindcss/node'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { TicketsView } from '../views/TicketsView'
import type { TicketSummary, TicketsFacets } from '../api'
import TICKETS_VIEW_SOURCE from '../views/TicketsView.tsx?raw'

function makeTicket(overrides: Partial<TicketSummary> = {}): TicketSummary {
  return {
    ticket_id: 'TCK-20260101-A',
    title: 'Sample ticket',
    tier: 'standard',
    ticket_type: 'feature',
    priority: 'P2',
    layer: 'observability',
    status: 'active',
    workflow_status: 'OPEN',
    tags: ['observability'],
    date: '2026-07-16',
    lifecycle_state: 'inprogress',
    matching_runs: [],
    ...overrides,
  }
}

// Mirrors what a real backend would return as `facets` for a filtered set
// equal to `items` — i.e. this page happens to be the entire corpus. Existing
// tests rely on the filter dropdowns being populated from exactly this
// derivation, since that was `distinctValues`/`distinctTags`'s old behavior
// over the (formerly unbounded) fetch result.
function computeFacetsFromItems(items: TicketSummary[]): TicketsFacets {
  function distinct(pick: (ticket: TicketSummary) => string | null): string[] {
    const values = new Set<string>()
    for (const item of items) {
      const value = pick(item)
      if (value) values.add(value)
    }
    return Array.from(values).sort()
  }
  const tags = new Set<string>()
  for (const item of items) {
    for (const tag of item.tags) tags.add(tag)
  }
  return {
    tiers: distinct((t) => t.tier),
    layers: distinct((t) => t.layer),
    statuses: distinct((t) => t.workflow_status),
    priorities: distinct((t) => t.priority),
    tags: Array.from(tags).sort(),
  }
}

function mockFetchReturning(
  items: TicketSummary[],
  envelopeOverrides: Partial<{ total_count: number; facets: TicketsFacets }> = {},
) {
  const body = {
    items,
    total_count: envelopeOverrides.total_count ?? items.length,
    facets: envelopeOverrides.facets ?? computeFacetsFromItems(items),
  }
  const mockFetch = vi.fn().mockResolvedValue({ ok: true, json: async () => body })
  globalThis.fetch = mockFetch as unknown as typeof fetch
  return mockFetch
}

const noopOnSelectRun = () => {}

describe('TicketsView — rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders rows from fetchTickets covering all three lifecycle states', async () => {
    mockFetchReturning([
      makeTicket({ ticket_id: 'TCK-A', lifecycle_state: 'inprogress' }),
      makeTicket({ ticket_id: 'TCK-B', lifecycle_state: 'done' }),
      makeTicket({ ticket_id: 'TCK-C', lifecycle_state: 'todos' }),
    ])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    expect(screen.getByTestId('ticket-row-TCK-A')).toBeInTheDocument()
    expect(screen.getByTestId('ticket-row-TCK-B')).toBeInTheDocument()
    expect(screen.getByTestId('ticket-row-TCK-C')).toBeInTheDocument()
  })
})

describe('TicketsView — filter bar delegates to server query params', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('filter bar narrows rows AND-across-dimensions, OR-within-tag, via server query params', async () => {
    const user = userEvent.setup()
    const initial = [
      makeTicket({ ticket_id: 'TCK-A', tier: 'standard', layer: 'observability', tags: ['observability', 'infra'] }),
      makeTicket({ ticket_id: 'TCK-B', tier: 'hotfix', layer: 'combat', tags: ['combat'] }),
    ]
    const mockFetch = mockFetchReturning(initial)

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    await user.selectOptions(screen.getByTestId('filter-tier'), 'standard')
    await user.selectOptions(screen.getByTestId('filter-layer'), 'observability')
    await user.click(screen.getByTestId('filter-tag-observability'))
    await user.click(screen.getByTestId('filter-tag-infra'))

    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
    const requestedUrl = String(lastCall[0])
    expect(requestedUrl).toContain('tier=standard')
    expect(requestedUrl).toContain('layer=observability')
    const tagMatches = requestedUrl.match(/tag=/g) ?? []
    expect(tagMatches.length).toBe(2)
    expect(requestedUrl).toContain('tag=observability')
    expect(requestedUrl).toContain('tag=infra')
  })

  it('selecting two tags with no dimension filter sends both as repeated tag params', async () => {
    const user = userEvent.setup()
    const initial = [
      makeTicket({ ticket_id: 'TCK-A', tags: ['observability', 'infra'] }),
      makeTicket({ ticket_id: 'TCK-B', tags: ['combat'] }),
    ]
    const mockFetch = mockFetchReturning(initial)

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    await user.click(screen.getByTestId('filter-tag-observability'))
    await user.click(screen.getByTestId('filter-tag-infra'))

    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
    const requestedUrl = String(lastCall[0])
    expect(requestedUrl).not.toContain('tier=')
    expect(requestedUrl).not.toContain('layer=')
    expect(requestedUrl).toContain('tag=observability')
    expect(requestedUrl).toContain('tag=infra')
  })
})

describe('TicketsView — linked-runs control', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('surfaces every matching_runs entry as a separate link, never collapsed', async () => {
    const user = userEvent.setup()
    const onSelectRun = vi.fn()
    mockFetchReturning([
      makeTicket({
        ticket_id: 'TCK-MULTI',
        matching_runs: [
          { run_id: 'run-2', start_ts: '2026-07-02T00:00:00Z', end_ts: null, final_status: 'DONE' },
          { run_id: 'run-1', start_ts: '2026-07-01T00:00:00Z', end_ts: null, final_status: 'DONE' },
        ],
      }),
    ])

    render(<TicketsView onSelectRun={onSelectRun} />)
    await screen.findByTestId('tickets-table')

    const link1 = screen.getByTestId('linked-run-link-TCK-MULTI-run-2')
    const link2 = screen.getByTestId('linked-run-link-TCK-MULTI-run-1')
    expect(link1).toBeInTheDocument()
    expect(link2).toBeInTheDocument()

    await user.click(link2)
    expect(onSelectRun).toHaveBeenCalledWith('run-1')

    await user.click(link1)
    expect(onSelectRun).toHaveBeenCalledWith('run-2')
  })

  it('renders no link/picker control when matching_runs is empty', async () => {
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-NONE', matching_runs: [] })])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const cell = screen.getByTestId('linked-runs-TCK-NONE')
    expect(cell.querySelector('button')).toBeNull()
  })
})

describe('TicketsView — null-safe rendering', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('null tier/priority/type render as null/empty, never a placeholder string', async () => {
    mockFetchReturning([
      makeTicket({ ticket_id: 'TCK-NULLS', tier: null, priority: null, ticket_type: null }),
    ])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const tierCell = screen.getByTestId('tier-cell-TCK-NULLS')
    const priorityCell = screen.getByTestId('priority-cell-TCK-NULLS')
    const typeCell = screen.getByTestId('type-cell-TCK-NULLS')

    for (const cell of [tierCell, priorityCell, typeCell]) {
      expect(cell.textContent).toBe('')
      expect(cell.textContent).not.toBe('N/A')
      expect(cell.textContent).not.toBe('null')
      expect(cell.textContent).not.toBe('—')
      expect(cell.textContent).not.toBe('unknown')
    }
  })
})

describe('TicketsView — client-side column sort', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('a tier column-header click re-orders rendered rows without triggering a new fetchTickets call, and surfaces a page-scoped-sort note when more than one page exists', async () => {
    const user = userEvent.setup()
    const mockFetch = mockFetchReturning(
      [
        makeTicket({ ticket_id: 'TCK-B', tier: 'standard' }),
        makeTicket({ ticket_id: 'TCK-A', tier: 'hotfix' }),
      ],
      { total_count: 500 },
    )

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    expect(screen.queryByTestId('column-sort-page-scoped-note')).toBeNull()
    const callsBeforeSort = mockFetch.mock.calls.length

    await user.click(screen.getByTestId('col-header-tier'))

    const rowsAfterSort = screen.getAllByTestId(/^ticket-row-/)
    expect(rowsAfterSort.map((row) => row.getAttribute('data-testid'))).toEqual([
      'ticket-row-TCK-A',
      'ticket-row-TCK-B',
    ])

    expect(mockFetch.mock.calls.length).toBe(callsBeforeSort)
    expect(screen.getByTestId('column-sort-page-scoped-note')).toBeInTheDocument()
  })

  it('does not surface the page-scoped-sort note when the loaded page is the entire corpus', async () => {
    const user = userEvent.setup()
    mockFetchReturning(
      [
        makeTicket({ ticket_id: 'TCK-B', tier: 'standard' }),
        makeTicket({ ticket_id: 'TCK-A', tier: 'hotfix' }),
      ],
      { total_count: 2 },
    )

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    await user.click(screen.getByTestId('col-header-tier'))

    expect(screen.queryByTestId('column-sort-page-scoped-note')).toBeNull()
  })
})

describe('TicketsView — pagination', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders only page-size ticket rows when the mocked corpus exceeds 1000 rows', async () => {
    const pageItems = Array.from({ length: 100 }, (_, i) => makeTicket({ ticket_id: `TCK-${i}` }))
    mockFetchReturning(pageItems, { total_count: 1109 })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    expect(screen.getAllByTestId(/^ticket-row-/).length).toBe(100)
  })

  it('requests a bounded limit/offset param on initial load', async () => {
    const mockFetch = mockFetchReturning([makeTicket()])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const firstCall = mockFetch.mock.calls[0]
    const requestedUrl = String(firstCall[0])
    expect(requestedUrl).toContain('limit=100')
    expect(requestedUrl).toContain('offset=0')
  })
})

describe('TicketsView — facets independent of page window', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('filter dropdown options include values from tickets outside the currently-loaded page', async () => {
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-A', tier: 'standard' })], {
      total_count: 500,
      facets: {
        tiers: ['epic', 'standard'],
        layers: ['combat', 'observability'],
        statuses: ['OPEN'],
        priorities: ['P1', 'P2'],
        tags: ['observability', 'offpage-tag'],
      },
    })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const tierSelect = screen.getByTestId('filter-tier') as HTMLSelectElement
    const tierOptionValues = Array.from(tierSelect.options).map((option) => option.value)
    expect(tierOptionValues).toContain('epic')

    expect(screen.getByTestId('filter-tag-offpage-tag')).toBeInTheDocument()
  })
})

describe('TicketsView — tag search/collapse', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('typing a substring into the tag search narrows the rendered tag options case-insensitively without a new fetchTickets call', async () => {
    const user = userEvent.setup()
    const mockFetch = mockFetchReturning([makeTicket({ ticket_id: 'TCK-A', tags: ['observability'] })], {
      facets: {
        tiers: ['standard'],
        layers: ['observability'],
        statuses: ['OPEN'],
        priorities: ['P1'],
        tags: ['observability', 'infra', 'combat', 'economy', 'strategy'],
      },
    })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const callsBeforeSearch = mockFetch.mock.calls.length
    const rowsBeforeSearch = screen.getAllByTestId(/^ticket-row-/).map((row) => row.getAttribute('data-testid'))

    await user.type(screen.getByTestId('filter-tags-search'), 'co')

    expect(screen.getByTestId('filter-tag-combat')).toBeInTheDocument()
    expect(screen.getByTestId('filter-tag-economy')).toBeInTheDocument()
    expect(screen.queryByTestId('filter-tag-observability')).toBeNull()
    expect(screen.queryByTestId('filter-tag-infra')).toBeNull()
    expect(screen.queryByTestId('filter-tag-strategy')).toBeNull()

    expect(mockFetch.mock.calls.length).toBe(callsBeforeSearch)
    const rowsAfterSearch = screen.getAllByTestId(/^ticket-row-/).map((row) => row.getAttribute('data-testid'))
    expect(rowsAfterSearch).toEqual(rowsBeforeSearch)
  })

  it('the tag selector does not render all ~1,309 facets.tags option buttons simultaneously on initial load', async () => {
    const manyTags = Array.from({ length: 1500 }, (_, i) => `tag-${String(i).padStart(4, '0')}`)
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-A' })], {
      facets: {
        tiers: ['standard'],
        layers: ['observability'],
        statuses: ['OPEN'],
        priorities: ['P1'],
        tags: manyTags,
      },
    })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    expect(screen.getAllByTestId(/^filter-tag-/).length).toBe(40)
  })

  it('an off-page facets tag remains reachable through the tag search after narrowing', async () => {
    const user = userEvent.setup()
    const manyTags = Array.from({ length: 1500 }, (_, i) => `tag-${String(i).padStart(4, '0')}`)
    manyTags.push('zzz-offpage-target')
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-A' })], {
      facets: {
        tiers: ['standard'],
        layers: ['observability'],
        statuses: ['OPEN'],
        priorities: ['P1'],
        tags: manyTags,
      },
    })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    expect(screen.queryByTestId('filter-tag-zzz-offpage-target')).toBeNull()

    await user.type(screen.getByTestId('filter-tags-search'), 'zzz-offpage')

    expect(screen.getByTestId('filter-tag-zzz-offpage-target')).toBeInTheDocument()
  })

  it('selecting a tag through the search-narrowed control still sends exactly one repeated tag= query param per selection', async () => {
    const user = userEvent.setup()
    const fiftyTags = Array.from({ length: 50 }, (_, i) => `tag-${String(i).padStart(2, '0')}`)
    const mockFetch = mockFetchReturning([makeTicket({ ticket_id: 'TCK-A' })], {
      facets: {
        tiers: ['standard'],
        layers: ['observability'],
        statuses: ['OPEN'],
        priorities: ['P1'],
        tags: fiftyTags,
      },
    })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    await user.type(screen.getByTestId('filter-tags-search'), 'tag-07')
    await user.click(screen.getByTestId('filter-tag-tag-07'))

    const lastCall = mockFetch.mock.calls[mockFetch.mock.calls.length - 1]
    const requestedUrl = String(lastCall[0])
    const tagMatches = requestedUrl.match(/tag=/g) ?? []
    expect(tagMatches.length).toBe(1)
    expect(requestedUrl).toContain('tag=tag-07')
  })

  it('clearing the tag search restores the full (bounded) option list', async () => {
    const user = userEvent.setup()
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-A' })], {
      facets: {
        tiers: ['standard'],
        layers: ['observability'],
        statuses: ['OPEN'],
        priorities: ['P1'],
        tags: ['observability', 'infra', 'combat'],
      },
    })

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const searchInput = screen.getByTestId('filter-tags-search')
    await user.type(searchInput, 'obs')
    expect(screen.queryByTestId('filter-tag-infra')).toBeNull()

    await user.clear(searchInput)

    expect(screen.getByTestId('filter-tag-observability')).toBeInTheDocument()
    expect(screen.getByTestId('filter-tag-infra')).toBeInTheDocument()
    expect(screen.getByTestId('filter-tag-combat')).toBeInTheDocument()
  })
})

describe('TicketsView — anti-drift source guards', () => {
  it('never re-implements a client-side .filter( pass over fetched ticket rows', () => {
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/\.filter\(/)
  })

  it('never re-sorts matching_runs client-side', () => {
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/matching_runs[^\n]*\.sort\(/)
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/\.sort\([^)]*\)[^\n]*matching_runs/)
  })

  it('never constructs a sort value other than date_asc/date_desc for a fetchTickets call', () => {
    const sortLiteralAssignments = TICKETS_VIEW_SOURCE.match(/sort:\s*'[^']*'/g) ?? []
    for (const assignment of sortLiteralAssignments) {
      expect(['date_asc', 'date_desc'].some((literal) => assignment.includes(literal))).toBe(true)
    }
    expect(TICKETS_VIEW_SOURCE).not.toMatch(/'tier_asc'|'tier_desc'|'layer_asc'|'layer_desc'|'priority_asc'|'priority_desc'|'status_asc'|'status_desc'|'tag_asc'|'tag_desc'/)
  })
})

// jsdom's getComputedStyle does not evaluate rules nested inside @layer at
// all (verified empirically: a rule declared only inside `@layer utilities`
// never affects computed style, even though CSSOM parses it correctly as a
// CSSLayerBlockRule). A real browser resolves cascade layers per spec —
// unlayered rules always beat layered ones regardless of specificity, and
// among layered rules the later-declared layer wins — so this walk
// reimplements just that comparison against the real, Tailwind-compiled
// index.css to prove which declaration actually wins for a given element.
function findLayerPriorityOrder(sheet: CSSStyleSheet): string[] {
  const order: string[] = []
  for (const rule of Array.from(sheet.cssRules)) {
    if (rule instanceof CSSLayerStatementRule) {
      for (const name of Array.from(rule.nameList)) {
        if (!order.includes(name)) order.push(name)
      }
    } else if (rule instanceof CSSLayerBlockRule && !order.includes(rule.name)) {
      order.push(rule.name)
    }
  }
  return order
}

function resolveCascadeWinner(sheet: CSSStyleSheet, element: Element, property: string): string | null {
  const layerPriorityOrder = findLayerPriorityOrder(sheet)
  const unlayeredValues: string[] = []
  const layeredValues: { priority: number; value: string }[] = []

  function visit(rules: CSSRuleList, layerName: string | null) {
    for (const rule of Array.from(rules)) {
      if (rule instanceof CSSLayerBlockRule) {
        visit(rule.cssRules, rule.name)
        continue
      }
      if (!(rule instanceof CSSStyleRule)) continue
      let matches: boolean
      try {
        matches = element.matches(rule.selectorText)
      } catch {
        // jsdom's selector engine rejects some of Tailwind preflight's
        // vendor-prefixed pseudo-classes (e.g. :-moz-focusring); those never
        // apply to our td elements, so treat an unparseable selector as a miss.
        matches = false
      }
      if (!matches) continue
      const value = rule.style.getPropertyValue(property)
      if (!value) continue
      if (layerName === null) {
        unlayeredValues.push(value)
      } else {
        layeredValues.push({ priority: layerPriorityOrder.indexOf(layerName), value })
      }
    }
  }

  visit(sheet.cssRules, null)
  if (unlayeredValues.length > 0) return unlayeredValues[unlayeredValues.length - 1]
  if (layeredValues.length === 0) return null
  return layeredValues.reduce((best, current) => (current.priority > best.priority ? current : best)).value
}

const DASHBOARD_ROOT = process.cwd()
const INDEX_CSS_SOURCE = readFileSync(path.join(DASHBOARD_ROOT, 'src/index.css'), 'utf8')

describe('TicketsView — index.css reset does not zero out padding utilities', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('the compiled reset no longer sits unlayered above the utilities layer, so pr-3 wins the cascade on the Tier and Layer cells', async () => {
    mockFetchReturning([makeTicket({ ticket_id: 'TCK-PAD', tier: 'standard', layer: 'engine' })])

    render(<TicketsView onSelectRun={noopOnSelectRun} />)
    await screen.findByTestId('tickets-table')

    const tierCell = screen.getByTestId('tier-cell-TCK-PAD')
    const layerCell = tierCell.nextElementSibling as HTMLElement
    expect(layerCell).not.toBeNull()

    const candidates = Array.from(
      new Set([...tierCell.className.split(/\s+/), ...layerCell.className.split(/\s+/)].filter(Boolean)),
    )

    const compiler = await compile(INDEX_CSS_SOURCE, { base: DASHBOARD_ROOT, onDependency: () => {} })
    const compiledCss = compiler.build(candidates)

    const styleTag = document.createElement('style')
    styleTag.textContent = compiledCss
    document.head.appendChild(styleTag)
    const sheet = styleTag.sheet as CSSStyleSheet

    const tierPaddingRight = resolveCascadeWinner(sheet, tierCell, 'padding-right')
    const layerPaddingRight = resolveCascadeWinner(sheet, layerCell, 'padding-right')

    // pr-3 resolves to calc(var(--spacing) * 3) with --spacing: 0.25rem,
    // i.e. 0.25rem * 3 = 0.75rem = 12px at the default 16px root font size —
    // the exact scale value the ticket's reported "standardengine" run-together
    // bug depended on being silently zeroed.
    expect(tierPaddingRight).toBe('calc(var(--spacing) * 3)')
    expect(layerPaddingRight).toBe('calc(var(--spacing) * 3)')
    expect(tierPaddingRight).not.toBe('0px')
    expect(tierPaddingRight).not.toBe('0')

    // Independently confirm that declaration is the 12px scale step Tailwind
    // ships by default, not an accidental theme override.
    expect(INDEX_CSS_SOURCE).toMatch(/--spacing:\s*0\.25rem|@import ['"]tailwindcss['"]/)

    // getComputedStyle itself can't resolve calc()/var() in jsdom, but it does
    // apply unlayered rules directly, so it still proves the reset stopped
    // forcing an explicit zero on this cell.
    expect(getComputedStyle(tierCell).paddingRight).not.toBe('0px')
  })

  it('the margin/padding/box-sizing reset lives inside @layer base, not unlayered', () => {
    expect(INDEX_CSS_SOURCE).toMatch(/@layer base\s*{\s*\*\s*{\s*margin:\s*0;\s*padding:\s*0;\s*box-sizing:\s*border-box;/)
  })
})
