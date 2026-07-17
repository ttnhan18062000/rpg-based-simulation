import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useRunsPolling, type RunSummary } from '../api'

function makeRun(id: string, startTs: string): RunSummary {
  return {
    run_id: id,
    workflow: 'implement-ticket',
    tier: 'standard',
    final_status: 'DONE',
    start_ts: startTs,
    end_ts: startTs,
    duration_s: 120,
    agent_count: 1,
    is_inferred_active: false,
    inferred_start_ts: null,
  }
}

describe('useRunsPolling', () => {
  const mockFetch = vi.fn()

  beforeEach(() => {
    mockFetch.mockReset()
    globalThis.fetch = mockFetch as unknown as typeof fetch
  })

  it('paginates when a since-window match count reaches the page limit', async () => {
    const page1 = Array.from({ length: 100 }, (_, i) =>
      makeRun(`run-${i}`, `2026-07-16T10:${String(i % 60).padStart(2, '0')}:00Z`),
    )
    const page2 = [makeRun('run-100', '2026-07-15T09:00:00Z')]

    mockFetch.mockImplementation(async (url: string | URL) => {
      const parsed = new URL(url.toString(), 'http://localhost')
      const offset = Number(parsed.searchParams.get('offset') ?? '0')
      const body = offset === 0 ? page1 : page2
      return { ok: true, json: async () => body }
    })

    const { result } = renderHook(() => useRunsPolling('2026-07-15T00:00:00Z', 999_999_999))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledTimes(2)
    expect(result.current.runs).toHaveLength(101)
    expect(result.current.runs.some((run) => run.run_id === 'run-100')).toBe(true)
  })

  it('does not issue a second request when the first page is under the limit', async () => {
    const page1 = [makeRun('run-a', '2026-07-16T10:00:00Z')]
    mockFetch.mockResolvedValue({ ok: true, json: async () => page1 })

    const { result } = renderHook(() => useRunsPolling('2026-07-15T00:00:00Z', 999_999_999))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(result.current.runs).toHaveLength(1)
  })
})
