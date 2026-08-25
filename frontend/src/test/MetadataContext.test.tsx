import { renderHook, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { MetadataProvider, useMetadata } from '../contexts/MetadataContext'

const mockFetch = vi.fn()
globalThis.fetch = mockFetch

function okJson(body: unknown) {
  return Promise.resolve({ ok: true, json: async () => body })
}

const EMPTY_ENUMS_BODY = {
  materials: [], ai_states: [], tiers: [], rarities: [], item_types: [],
  damage_types: [], elements: [], entity_roles: [], factions: [],
  faction_relations: [], entity_kinds: [],
}

function successfulFetchImpl(url: string) {
  if (url.includes('/enums')) return okJson(EMPTY_ENUMS_BODY)
  if (url.includes('/items')) return okJson({ items: [] })
  if (url.includes('/classes')) {
    return okJson({ classes: [], skills: [], race_skills: {}, scaling_grades: [], mastery_tiers: [], skill_targets: [] })
  }
  if (url.includes('/traits')) return okJson({ traits: [] })
  if (url.includes('/attributes')) return okJson({ attributes: [] })
  if (url.includes('/buildings')) return okJson({ building_types: [] })
  if (url.includes('/resources')) return okJson({ resource_types: [] })
  if (url.includes('/recipes')) return okJson({ recipes: [] })
  return Promise.reject(new Error(`unexpected URL: ${url}`))
}

describe('MetadataProvider', () => {
  beforeEach(() => {
    mockFetch.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('provides real metadata once all 8 fetches succeed', async () => {
    mockFetch.mockImplementation(successfulFetchImpl)

    const { result } = renderHook(() => useMetadata(), {
      wrapper: ({ children }) => <MetadataProvider>{children}</MetadataProvider>,
    })

    await waitFor(() => {
      expect(result.current.enums).toEqual(EMPTY_ENUMS_BODY)
    })
  })

  it('does not block rendering when the backend routes 404 -- falls back to empty metadata', async () => {
    vi.spyOn(console, 'error').mockImplementation(() => {})
    mockFetch.mockImplementation(() => Promise.resolve({ ok: false, status: 404, json: async () => ({}) }))

    const { result } = renderHook(() => useMetadata(), {
      wrapper: ({ children }) => <MetadataProvider>{children}</MetadataProvider>,
    })

    // useMetadata() must never throw (the null-context guard) -- reaching this assertion at all
    // is part of what's being tested. Falls back to the all-empty GameMetadata shape.
    await waitFor(() => {
      expect(result.current.items.items).toEqual([])
      expect(result.current.itemMap).toEqual({})
    })
  })
})
