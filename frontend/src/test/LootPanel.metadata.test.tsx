import { render, screen, waitFor } from '@testing-library/react'
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { MetadataProvider } from '../contexts/MetadataContext'
import { LootPanel } from '../components/LootPanel'
import type { GroundItem } from '../types/api'

// TCK-20260825-METADATA-API-BACKEND-MISSING: proves the real, end-to-end path -- a panel
// component genuinely renders a real item name/type/rarity/gold-value looked up through
// MetadataProvider's real itemMap, not the EMPTY_METADATA fallback. The fixture body below is a
// real response captured live from a running backend (`curl -H "X-API-Key: ..."
// http://127.0.0.1:8000/api/v1/metadata/items`), not hand-invented -- the same "iron_sword" entry
// this repo's real data/content/world/items.yaml defines.
const mockFetch = vi.fn()
globalThis.fetch = mockFetch

const REAL_IRON_SWORD = {
  item_id: 'iron_sword', name: 'Iron Sword', item_type: 'weapon', rarity: 'UNCOMMON',
  weight: 0.0, atk_bonus: 0.0, def_bonus: 0.0, spd_bonus: 0.0, max_hp_bonus: 0.0,
  crit_rate_bonus: 0.0, evasion_bonus: 0.0, luck_bonus: 0.0, matk_bonus: 0.0, mdef_bonus: 0.0,
  damage_type: '', element: '', heal_amount: 0.0, mana_restore: 0.0,
  gold_value: 80.0, sell_value: 80.0,
}

function okJson(body: unknown) {
  return Promise.resolve({ ok: true, json: async () => body })
}

function realBackedFetchImpl(url: string) {
  if (url.includes('/enums')) {
    return okJson({
      materials: [], ai_states: [], tiers: [], rarities: [], item_types: [],
      damage_types: [], elements: [], entity_roles: [], factions: [],
      faction_relations: [], entity_kinds: [],
    })
  }
  if (url.includes('/items')) return okJson({ items: [REAL_IRON_SWORD] })
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

const loot: GroundItem = { x: 1, y: 2, items: ['iron_sword'] }

describe('LootPanel + real MetadataProvider data', () => {
  beforeEach(() => {
    mockFetch.mockReset()
    mockFetch.mockImplementation(realBackedFetchImpl)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders the real item name/type/rarity/gold-value, not the itemId fallback', async () => {
    render(
      <MetadataProvider>
        <LootPanel loot={loot} onClose={() => {}} />
      </MetadataProvider>
    )

    await waitFor(() => {
      expect(screen.getByText('Iron Sword')).toBeInTheDocument()
    })
    expect(screen.queryByText('iron_sword')).not.toBeInTheDocument()
    expect(screen.getByText(/weapon/i)).toBeInTheDocument()
    expect(screen.getByText('UNCOMMON')).toBeInTheDocument()
    expect(screen.getByText(/Worth 80g/)).toBeInTheDocument()
  })
})
