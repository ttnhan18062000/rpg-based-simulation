import { renderHook, waitFor, act } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { useSimulation } from '../hooks/useSimulation'

// Mock the global fetch
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

// Mock EventSource
class MockEventSource {
  url: string
  onmessage: ((event: any) => void) | null = null
  onerror: ((event: any) => void) | null = null
  close = vi.fn()

  constructor(url: string) {
    this.url = url
  }
}

// Ensure the mock is spyable by Vitest but retains newable constructor signature
globalThis.EventSource = vi.fn(function(this: MockEventSource, url: string) {
  this.url = url
  this.onmessage = null
  this.onerror = null
  this.close = vi.fn()
}) as any

describe('useSimulation hook', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    vi.mocked(globalThis.EventSource).mockClear()

    
    // Default fetch mocks for the fallback loop
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        total_spawned: 10,
        total_deaths: 5,
        running: true,
        paused: false,
      })
    })
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('initializes with default values', () => {
    const { result } = renderHook(() => useSimulation())
    
    expect(result.current.tick).toBe(0)
    expect(result.current.entities).toEqual([])
    expect(result.current.status).toBe('CONNECTING')
    expect(result.current.aliveCount).toBe(0)
  })

  it('connects to SSE and processes entity streams correctly', async () => {
    // Mock the mapData response so the hook will start
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        width: 10,
        height: 10,
        grid: [],
        static_data: { buildings: [] }
      })
    })

    const { result } = renderHook(() => useSimulation())

    // Initial state
    expect(result.current.entities.length).toBe(0)

    // Wait for the hook to finish its initial map fetch and construct EventSource
    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith('/api/v1/map')
    })
    
    // We expect EventSource to have been initialized
    await waitFor(() => {
        expect(vi.mocked(globalThis.EventSource).mock.instances.length).toBeGreaterThan(0)
    })

    // Grab our mocked EventSource instance
    const esInstances = vi.mocked(globalThis.EventSource).mock.instances
    const mockES = esInstances[0] as unknown as MockEventSource
    expect(mockES.url).toBe('/api/v1/stream')

    // Simulate an incoming SSE message with 2 new/changed entities and 1 removed
    const payload = {
      tick: 150,
      changed: [
        { id: 1, kind: 'Hero', hp: 10 },
        { id: 2, kind: 'Slime', hp: 5 }
      ],
      removed: [3],
      events: []
    }

    // Trigger the onmessage handler directly
    if (mockES.onmessage) {
      act(() => {
        mockES.onmessage!({ data: JSON.stringify(payload) })
      })
    }

    // Hook state should now be updated mapping to array
    await waitFor(() => {
      expect(result.current.tick).toBe(150)
      expect(result.current.entities.length).toBe(2)
      expect(result.current.entities[0].id).toBe(1)
      expect(result.current.aliveCount).toBe(2)
    })
  })
})
