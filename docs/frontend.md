# Frontend Visualization

Technical documentation for the browser-based simulation viewer.

---

## Overview

The frontend is a **React 19 + TypeScript** single-page application built with **Vite** and styled with **Tailwind CSS v4**. It polls the REST API every ~80ms and renders the simulation state onto layered HTML5 canvases with an interactive sidebar.

The production build is served at `/` by the FastAPI backend from `frontend/dist/`. During development, Vite's dev server proxies API requests to the backend.

**Primary files:** `frontend/src/`

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Build | Vite | Fast HMR, TypeScript, API proxy |
| Framework | React 19 + TypeScript | Component architecture, type safety |
| Styling | Tailwind CSS v4 | Utility-first CSS with custom theme |
| Icons | Lucide React | Lightweight icon set |
| Primitives | Radix UI | Accessible tabs, scroll areas, sliders |
| Canvas | HTML5 Canvas (imperative) | Tile grid + entity rendering via React refs |

---

## Component Tree

```
MetadataProvider              # Wraps App — fetches all 8 /metadata/* endpoints on mount
└── App
    ├── Header                # Status bar + page toggle (Simulation | API Docs)
    ├── [Simulation view]
    │   ├── GameCanvas        # Canvas wrapper + hover tooltip overlay
    │   │   ├── grid-canvas   # Layer 1 (z-index: 1) — static tiles
    │   │   ├── entity-canvas # Layer 2 (z-index: 2) — entities, items, buildings, HP bars
    │   │   ├── overlay-canvas# Layer 3 (z-index: 3) — fog of war, ghost markers
    │   │   ├── minimap-canvas# Top-left minimap with viewport rect + click-to-jump
    │   │   ├── Locations     # Collapsible panel under minimap
    │   │   └── HoverTooltip  # Fixed-position tooltip following cursor
    │   └── Sidebar
    │       ├── ControlPanel  # Always visible (start/pause/resume/step/reset + speed slider)
    │       └── Tabs (context-dependent)
    │           ├── [Default]     # Info (Legend + EntityList) + Events (EventLog)
    │           ├── [Spectating]  # Inspect (InspectPanel — 6 tabs, uses useMetadata)
    │           ├── [Building]    # BuildingPanel / ClassHallPanel (uses useMetadata)
    │           └── [Loot]        # LootPanel (uses useMetadata)
    └── [API Docs view]
        └── ApiDocsPage       # Interactive OpenAPI explorer (fetches /openapi.json)
            ├── Tag sidebar   # Grouped endpoint navigation + search
            └── Endpoint cards# Method badge, path, params, schema, Try It Out
```

---

## Canvas Layers

Three stacked `<canvas>` elements managed via React refs in `useCanvas`:

| Layer | Ref | Z-Index | Purpose |
|-------|-----|---------|---------|
| 1 | `gridRef` | 1 | Static tile grid (drawn once on init) |
| 2 | `entityRef` | 2 | Ground items, resource nodes, entity sprites, HP bars, buildings, selection rings (redrawn every poll) |
| 3 | `overlayRef` | 3 | Vision/memory fog overlay + ghost markers (redrawn on selection change) |

The overlay uses `pointer-events: none` so clicks pass through.

---

## Sidebar Layout

Context-dependent tabbed interface. **ControlPanel** always visible above tab bar.

| Context | Tabs | Content |
|---------|------|---------|
| No selection | Info + Events | Legend + entity list; global event log with count + clear button |
| Spectating entity | Inspect (single tab) | 6-tab inspector panel |
| Clicked building | Inspect (building name) | BuildingPanel or ClassHallPanel |
| Clicked loot | Inspect ("Loot") | LootPanel with item details |

---

## Inspect Panel (6 Tabs)

When spectating an entity:

### Stats Tab
- **Header** — HP/stamina bars, ATK/DEF/MATK/MDEF/SPD/Gold in colored grid
- **Attributes** — 9-stat grid with caps/bars, hover tooltips showing full name, scaling, training progress
- **Detailed Stats** — base + equipment + buff breakdown
- **Equipment** — weapon, armor, accessory slots with item tooltips
- **Inventory** — bag items as small bordered tags with hover tooltips

### Class Tab
- Class info, skills with damage type (PHY/MAG) and element badges, mastery bars

### Quests Tab
- Title, type badge, progress bar, gold/XP reward, completion checkmark

### Events Tab
- Timestamped event history filtered to spectated entity, category color-coded

### Effects Tab
- Active buffs/debuffs with stat modifier badges, HP per tick, remaining duration

### AI Tab
- Current AI state with description
- Personality traits with colors/descriptions
- Utility AI goals explanation
- Craft target
- Memory & vision info

### Item Tooltips

Both equipment slots and inventory items use `ItemWithTooltip`. Hover shows:
- Item name (color-coded by rarity)
- Type and rarity
- Stat bonuses (ATK, DEF, SPD, CRIT, EVA, LUCK, max HP, MATK, MDEF)
- Consumable effects (heal amount, gold value)

Rarity colors: Common (`#9ca3af`), Uncommon (`#34d399`), Rare (`#a78bfa`).

---

## Vision Overlay

When spectating, the overlay canvas draws fog-of-war:

| State | Visual | Description |
|-------|--------|-------------|
| Visible | Clear | Within current vision range |
| Remembered | Semi-transparent (55% opacity) | Previously seen, in `terrain_memory` |
| Unknown | Heavy fog (82% opacity) | Never explored |

### Vision Range Border
Faint blue outline (`rgba(74, 158, 255, 0.3)`) around visible area edges.

### Ghost Entity Markers
Remembered entities from `entity_memory` drawn as ghosts:
- Skip if currently visible or if remembered position is in vision cone
- Skip if position unexplored
- Render: semi-transparent circle, dashed border, `?` label

---

## Minimap

### Features
- **Size:** `MINIMAP_SCALE = 2` px/tile, default 180×180 px container
- **Resizable:** Drag bottom-right handle (80–400 px range)
- **Separate zoom:** Scroll over minimap zooms minimap (1×–5×); scroll over world zooms world (0.5×–3×)
- **Click to jump:** Click anywhere on minimap moves world camera
- **Spectate filtering:** When spectating, entities/resources outside vision hidden on minimap

### Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `MINIMAP_SCALE` | 2 | Pixels per tile |
| `MM_DEFAULT_W/H` | 180 | Default container size (px) |
| `MM_MIN_SIZE` / `MM_MAX_SIZE` | 80 / 400 | Resize bounds |
| `MM_MIN_ZOOM` / `MM_MAX_ZOOM` | 1.0 / 5.0 | Minimap zoom range |
| `MIN_ZOOM` / `MAX_ZOOM` | 0.5 / 3.0 | World zoom range |

### Locations Panel

Collapsible panel under minimap showing:
- **Buildings:** Store, Blacksmith, Guild, Class Hall, Inn — with position and color
- **Tile clusters:** Camps, Sanctuaries, Ruins, Dungeons — detected via flood-fill with centroid coordinates
- Click any entry to jump camera

---

## Entity Rendering

### Hero
- **Shape:** Diamond (rotated square)
- **Glow:** Golden shadow blur (`#fbbf24`, 6px)
- **State border:** Colored outline matching AI state
- **ID label:** Bold white monospace

### Mobs
- **Shape:** Circle (`CELL_SIZE * 0.35` radius)
- **Color:** Kind-specific from `KIND_COLORS`
- **State border:** Colored ring matching AI state
- **ID label:** Semi-transparent white monospace

### Buildings
- **Shape:** Colored square markers with letter labels
- **Store:** S (blue), **Blacksmith:** B (amber), **Guild:** G (purple), **Class Hall:** C (violet), **Inn:** I (orange)
- Also appear as colored dots on minimap

### Ground Items
- **Shape:** Small diamond (rotated square, `CELL_SIZE * 0.28`)
- **Color:** Lime green (`#a3e635`) with glow
- **Badge:** White count badge if multiple items on tile

### Resource Nodes
- **Available:** 50% opacity fill + 1px border in resource-type color
- **Depleted:** Grey (`#4a5568`) at 30% opacity

### Selection Ring
- White dashed circle (`CELL_SIZE * 0.55` radius)

### HP Bars
- 2px tall bar above each entity
- Green (>50%) → Yellow (>25%) → Red (<25%)

---

## Tile Hover Tooltip (epic-09 F10)

Hovering any tile shows a multi-line tooltip with **all** information on that tile. No early-return — every layer is collected and displayed.

### Tooltip Lines

| Icon | Category | Content |
|------|----------|--------|
| 🗺 | **Terrain** | Tile type name + grid coordinates, always shown |
| ⚔ | **Entities** | All entities on tile: `#id kind Lv# (class) \| HP \| STA \| state` |
| 👻 | **Ghosts** | Remembered entities in fog: id, kind, level, ATK, HP, last-seen tick |
| 🏛 | **Buildings** | Building name |
| 💎 | **Loot** | Item name or bag count |
| 🌿 | **Resources** | Node name, remaining/max harvests, yields item |

### Implementation

- `TILE_NAMES` map in `src/constants/colors.ts` — maps `Material` enum values (0–22) to display names
- `handleCanvasHover` in `useCanvas.ts` collects all lines, joins with `\n`
- Tooltip rendered with `whitespace-pre-line max-w-xs` in `GameCanvas.tsx`
- Fog-of-war respected: entities/loot/resources hidden outside vision when spectating

---

## Color Palette

All colors in `src/constants/colors.ts` and Tailwind theme in `src/index.css`.

### Tile Colors

| Material | Hex |
|----------|-----|
| Floor | `#1a1d27` |
| Wall | `#555b73` |
| Water | `#1e3a5f` |
| Town | `#2d4a3e` |
| Camp | `#4a2d2d` |
| Sanctuary | `#2d3a4a` |
| Forest | `#1b3a1b` |
| Desert | `#3a3420` |
| Swamp | `#2a2a3a` |
| Mountain | `#3a3a3a` |
| Road | `#5a5040` |
| Bridge | `#4a6050` |
| Ruins | `#4a4035` |
| Dungeon | `#6a3040` |
| Lava | `#8a3000` |
| Grassland | `#4a6030` |
| Snow | `#c8d8e8` |
| Jungle | `#0a4a0a` |
| Shallow Water | `#2a5070` |
| Farmland | `#6a7a40` |
| Cave | `#3a3040` |
| Volcanic | `#5a2a1a` |
| Graveyard | `#4a4050` |

### Entity Colors (by kind)

| Kind | Hex |
|------|-----|
| Hero | `#4a9eff` |
| Goblin | `#f87171` |
| Goblin Scout | `#fb923c` |
| Goblin Warrior | `#dc2626` |
| Goblin Chief | `#fbbf24` |
| Wolf | `#a0a0a0` |
| Dire Wolf | `#808080` |
| Alpha Wolf | `#c0c0c0` |
| Bandit | `#e0a050` |
| Bandit Archer | `#d4943c` |
| Bandit Chief | `#f0c060` |
| Skeleton | `#b0b8c0` |
| Zombie | `#70a070` |
| Lich | `#c080ff` |
| Orc | `#60a060` |
| Orc Warrior | `#408040` |
| Orc Warlord | `#80c040` |
| Centaur | `#b0a060` |
| Centaur Lancer | `#c0b070` |
| Centaur Elder | `#d0c080` |
| Frost Wolf | `#90b0d0` |
| Frost Giant | `#7090b0` |
| Frost Shaman | `#a0c0e0` |
| Imp | `#e06040` |
| Hellhound | `#c04020` |
| Demon Lord | `#ff5030` |
| Lizard | `#40a080` |
| Lizard Warrior | `#308060` |
| Lizard Chief | `#50c0a0` |

### AI State Colors

| State | Hex |
|-------|-----|
| IDLE | `#8b8fa8` |
| WANDER | `#34d399` |
| HUNT | `#fbbf24` |
| COMBAT | `#f87171` |
| FLEE | `#a78bfa` |
| RETURN_TO_TOWN | `#60a5fa` |
| RESTING_IN_TOWN | `#22d3ee` |
| RETURN_TO_CAMP | `#f97316` |
| GUARD_CAMP | `#ef4444` |
| LOOTING | `#a3e635` |
| ALERT | `#ff6b6b` |
| VISIT_SHOP | `#38bdf8` |
| VISIT_BLACKSMITH | `#f59e0b` |
| VISIT_GUILD | `#818cf8` |
| HARVESTING | `#7dd3a0` |
| VISIT_CLASS_HALL | `#c084fc` |
| VISIT_INN | `#fb923c` |

---

## Key Hooks & Contexts

### `MetadataProvider` / `useMetadata()`

**File:** `src/contexts/MetadataContext.tsx`

Fetches all 8 `/api/v1/metadata/*` endpoints in parallel on mount. Builds derived lookup maps for O(1) access. Wraps the entire `App` in `main.tsx`.

**Provided data:**
- Raw data: `enums`, `items`, `classes`, `traits`, `attributes`, `buildings`, `resources`, `recipes`
- Lookup maps: `itemMap`, `traitMap`, `skillMap`, `classMap`, `aiStateMap`, `buildingTypeMap`
- Attribute helpers: `attrKeys`, `attrLabels`

**Used by:** `InspectPanel`, `ClassHallPanel`, `BuildingPanel`, `LootPanel`

### `useSimulation`

Central state management:
- One-time map fetch on mount
- Polls `/api/v1/state` and `/api/v1/stats` every 80ms via `setTimeout`
- Accumulates events (deduplicates by `tick:message` key)
- Exposes: `entities`, `events`, `tick`, `status`, `buildings`, `resourceNodes`, `groundItems`
- Callbacks: `sendControl(action)`, `setSpeed(tps)`, `selectEntity(id)`, `clearEvents()`

### `useCanvas`

Canvas rendering:
- Draws tile grid once when map data arrives
- Redraws entities/items/resources/buildings every poll cycle
- Redraws fog overlay + ghosts on selection change
- Spectate vision filtering: only entities within selected entity's vision rendered
- Hover detection: resolves grid cell, collects ALL info (terrain + entities + buildings + loot + resources) into multi-line tooltip
- Zoom-corrected coordinates for click and hover

---

## API Documentation Page

**File:** `src/components/ApiDocsPage.tsx`

An interactive API explorer accessible via the "API Docs" button in the header. Fetches `/openapi.json` from FastAPI and renders a custom UI.

### Features

- **Tag-grouped sidebar** — endpoints grouped by tag (State, Map, Control, Config, Metadata) with search
- **Endpoint cards** — expandable cards with method badge (color-coded), path, description
- **Parameter table** — name, location (path/query), type, required flag
- **Schema viewer** — request body and response schema rendered as typed pseudocode with copy button
- **Try It Out** — interactive request builder: fill parameters, edit body JSON, send real requests, view formatted response with status and timing
- **External links** — links to Swagger UI (`/docs`) and ReDoc (`/redoc`) in the sidebar footer

### Navigation

The `Header` component provides a page toggle between `Simulation` and `API Docs` views. The active page is stored in `App` state as `PageView` (`'simulation' | 'api-docs'`).

---

## Data Flow

```
Backend (WorldLoop) → Snapshot → API /state → useSimulation() hook
                                                    ↓
                                  React state (entities, groundItems, events, ...)
                                   ↓              ↓                ↓
                            useCanvas()    InspectPanel         EventLog
                          (3 canvas +      (React +             (React
                           hover tooltip)   item tooltips)       component)

Backend (core/) → /metadata/* → MetadataProvider (once on mount)
                                       ↓
                           GameMetadata context (itemMap, classMap, ...)
                            ↓              ↓                ↓
                     InspectPanel   ClassHallPanel    BuildingPanel

Backend → /openapi.json → ApiDocsPage (on mount)
                                ↓
                    Parsed OpenAPI spec → endpoint cards + Try It Out
```

---

## Type Safety

Two type definition files:

### `src/types/api.ts` — Simulation State

Matches Pydantic schemas for dynamic runtime data:
- `Entity` — full entity with stats, faction, equipment, memory, goals, skills, traits, quests
- `Building` — building_id, name, x, y, building_type
- `GameEvent` — tick + category + message
- `GroundItem` — x, y, items[]
- `ResourceNode` — node_id, resource_type, name, position, yields_item, remaining, is_available
- `WorldState` — tick, alive_count, entities[], events[], ground_items[], buildings[], resource_nodes[]
- `SimulationStats` — counters + running/paused flags
- `MapData` — width, height, grid[][]

### `src/types/metadata.ts` — Game Definitions

Mirrors core pydantic dataclass schemas (the single source of truth):
- `ItemEntry` — mirrors `ItemTemplate` (item_type/rarity/damage_type/element as strings)
- `SkillDefEntry` — mirrors `SkillDef` (skill_type/target/class_req as strings)
- `ClassEntry` — mirrors `ClassView` (grouped attr_bonuses, scaling, breakthrough)
- `TraitEntry` — mirrors `TraitDef` (trait_type as number, all utility/stat fields)
- `GameMetadata` — aggregated type with raw data + derived lookup maps

---

## Development

### Dev Server

```bash
cd frontend
npm install
npm run dev          # Starts Vite on http://localhost:5173
```

Vite proxies `/api/*`, `/openapi.json`, `/docs`, and `/redoc` to `http://127.0.0.1:8000`.

### Production Build

```bash
cd frontend
npm run build        # Outputs to frontend/dist/
```

FastAPI serves `frontend/dist/` at `/`.
