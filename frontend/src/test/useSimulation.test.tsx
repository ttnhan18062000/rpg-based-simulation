import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSimulation } from '../hooks/useSimulation'

// Mock the global fetch
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

// Mock WebSocket
class MockWebSocket {
  url: string
  send = vi.fn()
  close = vi.fn()
  onopen: (() => void) | null = null
  onmessage: ((event: any) => void) | null = null
  onclose: (() => void) | null = null
  onerror: (() => void) | null = null

  constructor(url: string) {
    this.url = url
  }
}

// Ensure the mock is spyable by Vitest but retains newable constructor signature
globalThis.WebSocket = vi.fn(function (this: MockWebSocket, url: string) {
  this.url = url
  this.send = vi.fn()
  this.close = vi.fn()
  this.onopen = null
  this.onmessage = null
  this.onclose = null
  this.onerror = null
}) as any

function defaultMockFetch(input: RequestInfo | URL) {
  const url = String(input)
  if (url.includes('/map')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({ width: 10, height: 10, grid: [] }),
    })
  }
  if (url.includes('/static')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({ buildings: [], resource_nodes: [], treasure_chests: [], regions: [] }),
    })
  }
  if (url.includes('/manifest')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        protocol_version: '1',
        dictionary_version: '1',
        terrain_types: {},
        entity_kinds: {},
        building_types: {},
      }),
    })
  }
  return Promise.resolve({
    ok: true,
    json: async () => ({
      total_spawned: 10,
      total_deaths: 5,
      running: true,
      paused: false,
    }),
  })
}

async function renderConnectedHook() {
  const { result } = renderHook(() => useSimulation())

  await waitFor(() => {
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/map')
  })

  await waitFor(() => {
    expect(vi.mocked(globalThis.WebSocket).mock.instances.length).toBeGreaterThan(0)
  })

  const wsInstances = vi.mocked(globalThis.WebSocket).mock.instances
  const mockWS = wsInstances[wsInstances.length - 1] as unknown as MockWebSocket

  act(() => {
    mockWS.onopen?.()
  })

  return { result, mockWS }
}

describe('useSimulation hook', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockImplementation(defaultMockFetch)
    vi.mocked(globalThis.WebSocket).mockClear()
  })

  afterEach(() => {
    vi.clearAllTimers()
    vi.useRealTimers()
  })

  it('initializes with default values', () => {
    const { result } = renderHook(() => useSimulation())

    expect(result.current.tick).toBe(0)
    expect(result.current.entities).toEqual([])
    expect(result.current.status).toBe('CONNECTING')
    expect(result.current.aliveCount).toBe(0)
  })

  it('sends handshake as the first outgoing message before processing any data', async () => {
    const { mockWS } = await renderConnectedHook()

    expect(mockWS.send).toHaveBeenCalledTimes(1)
    expect(mockWS.send).toHaveBeenNthCalledWith(
      1,
      JSON.stringify({ type: 'handshake', format: 'json' })
    )
  })

  it('opens WebSocket to /api/v1/ws, not EventSource', async () => {
    expect((globalThis as any).EventSource).toBeUndefined()

    const { mockWS } = await renderConnectedHook()

    expect(mockWS.url).toMatch(/\/api\/v1\/ws$/)
  })

  it('ignores/threads the initial full-state message distinctly from delta messages', async () => {
    const { result, mockWS } = await renderConnectedHook()

    const initialSummary = {
      tick: 0,
      world_time: 0,
      entities_count: 0,
      maturity: 'young',
      seed: 42,
    }

    act(() => {
      mockWS.onmessage?.({ data: JSON.stringify(initialSummary) })
    })

    // No entity/tick state should have been touched by the non-delta message
    expect(result.current.entities.length).toBe(0)
    expect(result.current.tick).toBe(0)

    const delta = {
      tick: 5,
      changed: [{ id: 1, kind: 'Hero', x: 1, y: 1, hp: 10, max_hp: 10, level: 1, faction: 'player', weapon_range: 1 }],
      removed: [],
      events: [],
      snapshot_as_of_tick: 5,
      region_id: null,
    }

    act(() => {
      mockWS.onmessage?.({ data: JSON.stringify(delta) })
    })

    await waitFor(() => {
      expect(result.current.tick).toBe(5)
      expect(result.current.entities.length).toBe(1)
      expect(result.current.aliveCount).toBe(1)
    })
  })

  it('reduces a real {tick,changed,removed,events,snapshot_as_of_tick,region_id} delta correctly', async () => {
    const { result, mockWS } = await renderConnectedHook()

    const payload = {
      tick: 150,
      changed: [
        { id: 1, kind: 'Hero', x: 1, y: 1, hp: 10, max_hp: 10, level: 1, faction: 'player', weapon_range: 1 },
        { id: 2, kind: 'Slime', x: 2, y: 2, hp: 5, max_hp: 5, level: 1, faction: 'monster', weapon_range: 1 },
      ],
      removed: [3],
      events: [],
      snapshot_as_of_tick: 150,
      region_id: null,
    }

    act(() => {
      mockWS.onmessage?.({ data: JSON.stringify(payload) })
    })

    await waitFor(() => {
      expect(result.current.tick).toBe(150)
      expect(result.current.entities.length).toBe(2)
      expect(result.current.entities[0].id).toBe(1)
      expect(result.current.aliveCount).toBe(2)
    })
  })

  it('sendControl(pause) POSTs exactly to /api/v1/control/pause, sendControl(resume) POSTs exactly to /api/v1/control/resume', async () => {
    const { result } = await renderConnectedHook()

    mockFetch.mockClear()

    await act(async () => {
      await result.current.sendControl('pause')
    })
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/control/pause', { method: 'POST' })

    mockFetch.mockClear()

    await act(async () => {
      await result.current.sendControl('resume')
    })
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/control/resume', { method: 'POST' })
  })

  it('sendControl with an unrecognized action does not construct a generic /api/v1/control/{action} URL', async () => {
    const { result } = await renderConnectedHook()

    mockFetch.mockClear()

    for (const action of ['start', 'step', 'reset']) {
      await act(async () => {
        await result.current.sendControl(action)
      })
    }

    for (const call of mockFetch.mock.calls) {
      expect(String(call[0])).not.toMatch(/\/control\/(start|step|reset)/)
    }
  })

  it('reconnects after WebSocket close', async () => {
    const { mockWS } = await renderConnectedHook()
    vi.useFakeTimers()

    const priorInstanceCount = vi.mocked(globalThis.WebSocket).mock.instances.length

    act(() => {
      mockWS.onclose?.()
    })

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(vi.mocked(globalThis.WebSocket).mock.instances.length).toBe(priorInstanceCount + 1)
  })

  it('reconnects after WebSocket error', async () => {
    const { mockWS } = await renderConnectedHook()
    vi.useFakeTimers()

    const priorInstanceCount = vi.mocked(globalThis.WebSocket).mock.instances.length

    act(() => {
      mockWS.onerror?.()
    })

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(vi.mocked(globalThis.WebSocket).mock.instances.length).toBe(priorInstanceCount + 1)
  })

  it('loadInitial still fetches /map, /static, /manifest via one Promise.all', async () => {
    renderHook(() => useSimulation())

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/map')
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/static')
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/manifest')
    })
  })
})
