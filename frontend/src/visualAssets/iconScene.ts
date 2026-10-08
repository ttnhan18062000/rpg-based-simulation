// Pure helpers of the icon preview page (`TCK-20261006-VISUAL-ASSETS-ICON-KEY-DRAFT-SET`): the key list, the stacking order, a small deterministic map scene, the colour-vision
// filter matrices and each key's fallback. No DOM, no React. Nothing here computes a pass or fail: the verdict is the recorded result of the Python sheet rule.

export const TIERS = ['e', 'd', 'c', 'b', 'a', 's', 'ss', 'sss'] as const
export type Tier = (typeof TIERS)[number]

export const PLATE_KEY = 'icon.plate.location'
export const GLYPH_KEY = 'icon.marker.enemy_camp'
export const BUFF_KEY = 'icon.status.frame_buff'
export const DEBUFF_KEY = 'icon.status.frame_debuff'
export const tierKey = (tier: Tier): string => `icon.tier.${tier}`

/** Native size in art pixels of every key of the set (the registry's own descriptions state them). */
export const ICON_SIZES: Readonly<Record<string, number>> = Object.freeze({
  [PLATE_KEY]: 16, [GLYPH_KEY]: 16, 'icon.building.blacksmith': 24, 'icon.class.warrior': 24, [BUFF_KEY]: 16, [DEBUFF_KEY]: 16,
  ...Object.fromEntries(TIERS.map((t) => [tierKey(t), 8])),
})
export const ICON_KEYS: readonly string[] = Object.freeze(Object.keys(ICON_SIZES).sort())

/** Icon set v2 (`TCK-20261007-VISUAL-ASSETS-ICON-V2-DRAFT-SET`): the families of the sheets, in display order; a key's family is the second part of its name. Which keys exist and their sizes come from the manifests. */
export const V2_FAMILIES: readonly string[] = Object.freeze(['marker', 'building', 'class', 'item', 'rarity'])
export const RARITIES = ['common', 'uncommon', 'rare'] as const
export const rarityKey = (rarity: (typeof RARITIES)[number]): string => `icon.rarity.${rarity}`
export const familyOf = (key: string): string => key.split('.')[1] ?? ''

/** Plate first, glyph over it: both are 16x16 canvases the client composites at the same origin (planner ruling, 2026-10-06). */
export const MARKER_LAYERS: readonly string[] = Object.freeze([PLATE_KEY, GLYPH_KEY])

/** The Live Map's own flat terrain fills of the tiles the scene uses (a copy of `TILE_COLORS`; the page imports nothing from the app). */
export const TILE_FILLS: Readonly<Record<string, string>> = Object.freeze({
  'terrain.floor': '#1a1d27', 'terrain.snow': '#c8d8e8', 'terrain.grassland': '#4a6030', 'terrain.water': '#1e3a5f', 'terrain.forest': '#1b3a1b',
  'terrain.mountain': '#3a3a3a', 'terrain.desert': '#3a3420', 'terrain.farmland': '#6a7a40',
})

const SCENE_LEGEND: Readonly<Record<string, string>> = Object.freeze({
  '.': 'terrain.floor', s: 'terrain.snow', g: 'terrain.grassland', w: 'terrain.water', f: 'terrain.forest', m: 'terrain.mountain', d: 'terrain.desert', a: 'terrain.farmland',
})
export const SCENE_ROWS: readonly string[] = Object.freeze([
  '....ssss....',
  '..mmsssss.ww',
  '.mmm.sss.www',
  '..ff..gg.ww.',
  '.fff.ggggg..',
  '..dd.gaaa...',
  '.dddd.aaaa..',
])
/** Marker cells of the scene (x, y): one over the darkest tile, one over snow, one over grass, one over water. */
export const SCENE_MARKERS: readonly (readonly [number, number])[] = Object.freeze([[1, 0], [6, 0], [7, 4], [10, 2]])

export const sceneKey = (x: number, y: number): string => SCENE_LEGEND[SCENE_ROWS[y][x]]
export const SCENE_COLUMNS = SCENE_ROWS[0].length
export const SCENE_ROW_COUNT = SCENE_ROWS.length

// Colour-vision approximations as SVG `feColorMatrix` values, applied in linear RGB (`color-interpolation-filters="linearRGB"`), the same space and matrices (Machado, Oliveira and Fernandes
// 2009, severity 1.0) as tests/visual_assets/pilot_colour_vision.py, which a test compares. This is a visual approximation for the eye, not the rule.
export const MACHADO: Readonly<Record<'protan' | 'deutan' | 'tritan', readonly (readonly number[])[]>> = Object.freeze({
  protan: [[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]],
  deutan: [[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.01182, 0.04294, 0.968881]],
  tritan: [[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.3039]],
})
const LUMA = [0.2126, 0.7152, 0.0722]

export interface VisionFilter { readonly id: string; readonly label: string; readonly values: string }
const toValues = (rows: readonly (readonly number[])[]): string => [...rows.map((r) => `${r[0]} ${r[1]} ${r[2]} 0 0`), '0 0 0 1 0'].join(' ')
export const VISION_FILTERS: readonly VisionFilter[] = Object.freeze([
  { id: 'colour', label: 'colour', values: '' },
  { id: 'grey', label: 'greyscale', values: toValues([LUMA, LUMA, LUMA]) },
  { id: 'protan', label: 'protanopia', values: toValues(MACHADO.protan) },
  { id: 'deutan', label: 'deuteranopia', values: toValues(MACHADO.deutan) },
  { id: 'tritan', label: 'tritanopia', values: toValues(MACHADO.tritan) },
])

/** Today's grade chip colours (ClassHallPanel's GRADE_COLORS, copied): the fallback of a tier badge is the colour chip plus the letter. */
export const GRADE_CHIPS: Readonly<Record<Tier, string>> = Object.freeze({
  e: '#6b7280', d: '#94a3b8', c: '#34d399', b: '#60a5fa', a: '#fb923c', s: '#f87171', ss: '#f59e0b', sss: '#ffd700',
})

// Lucide paths of today's panel icons (lucide-react 0.563.0, ISC licence, copied so this module imports nothing from the app): the fallback of the blacksmith and warrior icons.
export const LUCIDE_PATHS: Readonly<Record<'hammer' | 'shield', readonly string[]>> = Object.freeze({
  hammer: [
    'm15 12-9.373 9.373a1 1 0 0 1-3.001-3L12 9', 'm18 15 4-4',
    'm21.5 11.5-1.914-1.914A2 2 0 0 1 19 8.172v-.344a2 2 0 0 0-.586-1.414l-1.657-1.657A6 6 0 0 0 12.516 3H9l1.243 1.243A6 6 0 0 1 12 8.485V10l2 2h1.172a2 2 0 0 1 1.414.586L18.5 14.5',
  ],
  shield: ['M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z'],
})

export type Fallback =
  | { readonly kind: 'emoji'; readonly glyph: string; readonly color: string; readonly note: string }
  | { readonly kind: 'lucide'; readonly name: 'hammer' | 'shield'; readonly color: string; readonly note: string }
  | { readonly kind: 'chip'; readonly letter: string; readonly color: string; readonly note: string }
  | { readonly kind: 'text'; readonly text: string; readonly note: string }
  | { readonly kind: 'none'; readonly note: string }

const textFallback = (text: string, note: string): Fallback => ({ kind: 'text', text, note: `identifying: ${note}` })
const RARITY_CHIPS: Readonly<Record<string, string>> = Object.freeze({ common: '#9ca3af', uncommon: '#34d399', rare: '#a78bfa' })
const MARKER_FALLBACKS: Readonly<Record<string, readonly [string, string]>> = Object.freeze({
  resource_grove: ['herb emoji', '#4ade80'], ruins: ['classical building emoji', '#a0906a'], dungeon_entrance: ['door emoji', '#e06080'], shrine: ['four-pointed star symbol', '#60a5fa'], boss_arena: ['skull emoji', '#f59e0b'],
})
const PANEL_FALLBACKS: Readonly<Record<string, string>> = Object.freeze({
  'icon.building.store': 'Lucide Store icon (#38bdf8) plus the building name as text', 'icon.building.guild': 'Lucide Shield icon (#818cf8) plus the building name as text',
  'icon.building.inn': 'Lucide Bed icon (#fb923c) plus the building name as text', 'icon.building.hero_house': 'Lucide Home icon (#34d399) plus the building name as text',
  'icon.building.class_hall': 'the building name as text (the building panel has no icon for it today)',
  'icon.class.ranger': 'Lucide Crosshair icon plus the class name as text', 'icon.class.mage': 'Lucide Wand2 icon plus the class name as text', 'icon.class.rogue': 'Lucide Sword icon plus the class name as text',
})
/** The fallbacks of the 22 icon set v2 keys, as each key's description in the registry states them (copied; the page imports nothing from the app). */
const V2_FALLBACKS: Readonly<Record<string, Fallback>> = Object.freeze({
  ...Object.fromEntries(Object.entries(MARKER_FALLBACKS).map(([n, [what, color]]) => [`icon.marker.${n}`, textFallback(`${what} (${color}) plus the location name as hover text`, `today's ${what} label`)])),
  ...Object.fromEntries(Object.entries(PANEL_FALLBACKS).map(([k, what]) => [k, textFallback(what, 'today\'s panel label')])),
  ...Object.fromEntries(['weapon', 'armor', 'trinket', 'tool', 'consumable', 'material'].map((n) => [`icon.item.${n}`, textFallback(`${n} (item type as text)`, 'the item type as text, as the loot and inspect panels show it today')])),
  ...Object.fromEntries(RARITIES.map((r) => [rarityKey(r), { kind: 'chip', letter: r, color: RARITY_CHIPS[r], note: 'identifying: today\'s rarity colour on the rarity name as text, which the badge never replaces' } as Fallback])),
})

/** What the Live Map or a panel shows today where the icon will go (docs/assets/fallback_safety.md; each key's description in the registry states the same). */
export function fallbackFor(key: string): Fallback {
  if (key === PLATE_KEY) return { kind: 'none', note: 'decorative: the bare glyph, no plate' }
  if (key === GLYPH_KEY) return { kind: 'emoji', glyph: '⚔', color: '#f87171', note: 'identifying: today\'s emoji label plus the location name as hover text' }
  if (key === 'icon.building.blacksmith') return { kind: 'lucide', name: 'hammer', color: '#f59e0b', note: 'identifying: today\'s Lucide Hammer plus the building name as text' }
  if (key === 'icon.class.warrior') return { kind: 'lucide', name: 'shield', color: '#e5e7eb', note: 'identifying: today\'s Lucide Shield plus the class name as text' }
  if (key === BUFF_KEY) return { kind: 'text', text: 'effect name (buff)', note: 'identifying: the effect\'s name as text in the Effects tab, which has no icon today' }
  if (key === DEBUFF_KEY) return { kind: 'text', text: 'effect name (debuff)', note: 'identifying: the effect\'s name as text in the Effects tab, which has no icon today' }
  const v2 = V2_FALLBACKS[key]
  if (v2) return v2
  const tier = TIERS.find((t) => tierKey(t) === key)
  if (tier) return { kind: 'chip', letter: tier.toUpperCase(), color: GRADE_CHIPS[tier], note: 'identifying: today\'s colour chip plus the letter, which the badge never replaces' }
  throw new Error(`no fallback is declared for ${key}`)
}
