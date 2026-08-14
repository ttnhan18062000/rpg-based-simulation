import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useRunTimelinesPolling, type TimelineEntry } from '../api'

function makeEntry(seq: number): TimelineEntry {
  return {
    seq,
    phase: 'Implement',
    agent: 'implementer',
    status: 'DONE',
    summary: 'did a thing',
    ts: '2026-07-16T10:00:00Z',
    tool_call_count: 1,
    cost_proxy_score: 0.1,
    reason_code: null,
    tool_calls: [],
  }
}

describe('useRunTimelinesPolling', () => {
  const mockFetch = vi.fn()

  beforeEach(() => {
    mockFetch.mockReset()
    globalThis.fetch = mockFetch as unknown as typeof fetch
  })

  it('paginates when a page reaches the page limit; merges as a union across pages, not last-page-wins', async () => {
    const page1EntriesByRun: Record<string, TimelineEntry[]> = {}
    for (let i = 0; i < 100; i++) {
      page1EntriesByRun[`run-${i}`] = [makeEntry(0)]
    }
    const page2EntriesByRun: Record<string, TimelineEntry[]> = {
      'run-100': [makeEntry(0)],
    }

    mockFetch.mockImplementation(async (url: string | URL) => {
      const parsed = new URL(url.toString(), 'http://localhost')
      const offset = Number(parsed.searchParams.get('offset') ?? '0')
      const body = offset === 0 ? { entries_by_run: page1EntriesByRun } : { entries_by_run: page2EntriesByRun }
      return { ok: true, json: async () => body }
    })

    const { result } = renderHook(() => useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledTimes(2)
    expect(Object.keys(result.current.entriesByRun)).toHaveLength(101)
    expect(result.current.entriesByRun['run-100']).toBeDefined()
    expect(result.current.entriesByRun['run-0']).toBeDefined()
  })

  it('does not issue a second request when the first page is under the limit', async () => {
    const body = { entries_by_run: { 'run-a': [makeEntry(0)] } }
    mockFetch.mockResolvedValue({ ok: true, json: async () => body })

    const { result } = renderHook(() => useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledTimes(1)
    expect(Object.keys(result.current.entriesByRun)).toHaveLength(1)
  })

  it('sets error and isLoading false when the fetch rejects', async () => {
    mockFetch.mockRejectedValue(new Error('network down'))

    const { result } = renderHook(() => useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(result.current.error).not.toBeNull()
    expect(result.current.error?.message).toBe('network down')
    expect(result.current.entriesByRun).toEqual({})
  })

  it('forwards until to the bulk fetch query string when the 3rd argument is provided', async () => {
    const body = { entries_by_run: { 'run-a': [makeEntry(0)] } }
    mockFetch.mockResolvedValue({ ok: true, json: async () => body })

    const { result } = renderHook(() =>
      useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999, '2026-07-16T00:00:00Z'),
    )

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const calledUrl = new URL((mockFetch.mock.calls[0][0] as string).toString(), 'http://localhost')
    expect(calledUrl.searchParams.get('until')).toBe('2026-07-16T00:00:00Z')
  })

  it('2-argument call omits until from the query string (2nd arg still means intervalMs, not untilIso)', async () => {
    const body = { entries_by_run: { 'run-a': [makeEntry(0)] } }
    mockFetch.mockResolvedValue({ ok: true, json: async () => body })

    const { result } = renderHook(() => useRunTimelinesPolling('2026-07-15T00:00:00Z', 999_999_999))

    await waitFor(() => expect(result.current.isLoading).toBe(false))

    expect(mockFetch).toHaveBeenCalledTimes(1)
    const calledUrl = new URL((mockFetch.mock.calls[0][0] as string).toString(), 'http://localhost')
    expect(calledUrl.searchParams.has('until')).toBe(false)
  })
})
