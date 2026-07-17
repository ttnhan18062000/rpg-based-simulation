import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { RecentActivityGantt } from '../views/RecentActivityGantt'
import { useRunsPolling, type RunSummary } from '../api'

vi.mock('../api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('../api')>()
  return {
    ...actual,
    useRunsPolling: vi.fn(),
  }
})

const mockedUseRunsPolling = vi.mocked(useRunsPolling)

function completedRun(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'run-completed',
    workflow: 'implement-ticket',
    tier: 'standard',
    final_status: 'DONE',
    start_ts: '2026-07-16T10:00:00Z',
    end_ts: '2026-07-16T10:05:00Z',
    duration_s: 300,
    agent_count: 2,
    is_inferred_active: false,
    inferred_start_ts: null,
    ...overrides,
  }
}

function inferredRun(overrides: Partial<RunSummary> = {}): RunSummary {
  return {
    run_id: 'run-inferred',
    workflow: 'implement-ticket',
    tier: 'standard',
    final_status: 'DONE',
    start_ts: null,
    end_ts: null,
    duration_s: null,
    agent_count: 1,
    is_inferred_active: true,
    inferred_start_ts: '2026-07-16T10:00:00Z',
    ...overrides,
  }
}

function classesOf(el: Element): Set<string> {
  return new Set(el.className.split(' ').filter(Boolean))
}

describe('RecentActivityGantt', () => {
  const onSelectRun = vi.fn()

  beforeEach(() => {
    mockedUseRunsPolling.mockReset()
    onSelectRun.mockReset()
  })

  it('renders a completed run as a solid authoritative bar', () => {
    mockedUseRunsPolling.mockReturnValue({ runs: [completedRun()], isLoading: false, error: null })

    render(<RecentActivityGantt onSelectRun={onSelectRun} />)

    const bar = document.querySelector('[data-run-id="run-completed"]')!
    const classes = classesOf(bar)
    expect(classes.has('gantt-bar--authoritative')).toBe(true)
    expect(classes.has('gantt-bar--inferred')).toBe(false)
    expect(bar.getAttribute('data-start')).toBe('2026-07-16T10:00:00Z')
    expect(bar.getAttribute('data-end')).toBe('2026-07-16T10:05:00Z')
    expect(screen.queryByText('~est.')).not.toBeInTheDocument()
  })

  it('renders a run present only in the inferred-active set anchored at inferred_start_ts', () => {
    mockedUseRunsPolling.mockReturnValue({ runs: [inferredRun()], isLoading: false, error: null })

    render(<RecentActivityGantt onSelectRun={onSelectRun} />)

    const bar = screen.getByText('~est.').closest('[data-run-id]')!
    const classes = classesOf(bar)
    expect(classes.has('gantt-bar--inferred')).toBe(true)
    expect(classes.has('gantt-bar--authoritative')).toBe(false)
    expect(bar.getAttribute('data-start')).toBe('2026-07-16T10:00:00Z')
    expect(bar.getAttribute('data-end')).not.toBe('')
    expect(bar.getAttribute('data-end')).not.toBeNull()
  })

  it('never shares styling between an inferred-active bar and an authoritative-completed bar', () => {
    mockedUseRunsPolling.mockReturnValue({
      runs: [completedRun(), inferredRun()],
      isLoading: false,
      error: null,
    })

    render(<RecentActivityGantt onSelectRun={onSelectRun} />)

    const authoritativeBar = document.querySelector('[data-run-id="run-completed"]')!
    const inferredBar = document.querySelector('[data-run-id="run-inferred"]')!

    const authoritativeClasses = classesOf(authoritativeBar)
    const inferredClasses = classesOf(inferredBar)
    const intersection = [...authoritativeClasses].filter((cls) => inferredClasses.has(cls))

    expect(intersection).toEqual([])
  })

  it('updates the bar to authoritative style/values with no stale active state after a transition', () => {
    mockedUseRunsPolling.mockReturnValue({
      runs: [inferredRun({ run_id: 'run-x' })],
      isLoading: false,
      error: null,
    })

    const { rerender } = render(<RecentActivityGantt onSelectRun={onSelectRun} />)

    let bar = document.querySelector('[data-run-id="run-x"]')!
    expect(classesOf(bar).has('gantt-bar--inferred')).toBe(true)

    mockedUseRunsPolling.mockReturnValue({
      runs: [
        completedRun({
          run_id: 'run-x',
          start_ts: '2026-07-16T10:00:00Z',
          end_ts: '2026-07-16T10:10:00Z',
        }),
      ],
      isLoading: false,
      error: null,
    })

    rerender(<RecentActivityGantt onSelectRun={onSelectRun} />)

    bar = document.querySelector('[data-run-id="run-x"]')!
    const classes = classesOf(bar)
    expect(classes.has('gantt-bar--authoritative')).toBe(true)
    expect(classes.has('gantt-bar--inferred')).toBe(false)
    expect(bar.getAttribute('data-start')).toBe('2026-07-16T10:00:00Z')
    expect(bar.getAttribute('data-end')).toBe('2026-07-16T10:10:00Z')
    expect(screen.queryByText('~est.')).not.toBeInTheDocument()
  })

  it('calls onSelectRun with that row\'s own run_id when a row is clicked', () => {
    mockedUseRunsPolling.mockReturnValue({
      runs: [completedRun({ run_id: 'run-a' }), completedRun({ run_id: 'run-b' })],
      isLoading: false,
      error: null,
    })

    render(<RecentActivityGantt onSelectRun={onSelectRun} />)

    const barB = document.querySelector('[data-run-id="run-b"]')!
    barB.closest('.relative.h-6')!.dispatchEvent(new MouseEvent('click', { bubbles: true }))

    expect(onSelectRun).toHaveBeenCalledTimes(1)
    expect(onSelectRun).toHaveBeenCalledWith('run-b')
  })
})
