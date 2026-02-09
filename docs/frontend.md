# Frontend Visualization

Technical documentation for the browser-based simulation viewer.

---

## Overview

The frontend is a **React 19 + TypeScript** single-page application built with **Vite** and styled with **Tailwind CSS v4**. It polls the REST API every ~80ms and renders the simulation state onto layered HTML5 canvases with an interactive sidebar.

The production build is served at `/` by the FastAPI backend from `frontend/dist/`. During development, Vite's dev server proxies API requests to the backend.

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

## Project Structure

```
frontend/
├── index.html              # Vite HTML entry point
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite config (Tailwind plugin, API proxy, path alias)
├── tsconfig.app.json       # TypeScript config with @/ path alias
├── src/
│   ├── main.tsx            # React DOM entry point
│   ├── App.tsx             # Root layout (Header + Canvas + Sidebar)
│   ├── index.css           # Tailwind imports + custom theme variables
│   ├── lib/
│   │   └── utils.ts        # cn() class-merge utility
│   ├── types/
│   │   └── api.ts          # TypeScript interfaces matching Pydantic schemas
│   ├── constants/
│   │   └── colors.ts       # Tile, entity, state colors; item stats registry
│   ├── hooks/
│   │   ├── useSimulation.ts  # API polling + React state management
│   │   └── useCanvas.ts      # Canvas rendering (grid, entities, fog overlay)
│   └── components/
│       ├── Header.tsx        # Top bar with tick/alive/spawned/deaths/status
│       ├── GameCanvas.tsx    # Three-layer canvas wrapper + hover tooltip
│       ├── Sidebar.tsx       # Tab container (Info, Inspect, Events)
│       ├── ControlPanel.tsx  # Start/Pause/Resume/Step/Reset + speed slider
│       ├── EntityList.tsx    # Sorted entity list with HP bars
│       ├── InspectPanel.tsx  # Entity inspector (stats, equip, goals, memory, entity events)
│       ├── BuildingPanel.tsx # Building info (store inventory, recipes, guild intel)
│       ├── LootPanel.tsx     # Ground item detail view
│       ├── EventLog.tsx      # Scrollable combat/event log
│       └── Legend.tsx        # Tile/entity color legend
```

---

## Architecture

### Component Tree

```
App
├── Header                  # Status bar (tick, alive, spawned, deaths)
├── GameCanvas              # Canvas wrapper + hover tooltip overlay
│   ├── grid-canvas         # Layer 1 (z-index: 1) — static tiles
│   ├── entity-canvas       # Layer 2 (z-index: 2) — entities, ground items, buildings, HP bars
│   ├── overlay-canvas      # Layer 3 (z-index: 3) — fog of war, ghost markers
│   ├── minimap-canvas      # Top-left minimap with viewport rect + click-to-jump
│   └── HoverTooltip        # Fixed-position tooltip following cursor
└── Sidebar
    ├── ControlPanel        # Always visible
    └── Tabs (context-dependent)
        ├── [Default]       # Info (Legend + EntityList) + Events (EventLog)
        ├── [Spectating]    # Inspect (InspectPanel with entity events sub-section)
        ├── [Building]      # Inspect → BuildingPanel (store/blacksmith/guild info)
        └── [Loot]          # Inspect → LootPanel (ground item details)
```

### Canvas Layers

Three stacked `<canvas>` elements render the world, managed via React refs in the `useCanvas` hook:

| Layer | Ref | Z-Index | Purpose |
|-------|-----|---------|---------|
| 1 | `gridRef` | 1 | Static tile grid (drawn once on init) |
| 2 | `entityRef` | 2 | Ground items, entity sprites, HP bars, selection rings (redrawn every poll) |
| 3 | `overlayRef` | 3 | Vision/memory fog overlay + ghost markers (redrawn when entity selected) |

The overlay canvas uses `pointer-events: none` so clicks pass through to the entity canvas beneath.

### Sidebar Layout

The sidebar uses a **context-dependent tabbed interface**. The **ControlPanel** (start/pause/resume/step/reset + speed slider) is always visible above the tab bar.

| Context | Tabs Shown | Content |
|---------|------------|--------|
| **No selection** | Info + Events | Legend + entity list; global event log |
| **Spectating entity** | Inspect (single tab) | Entity stats, equipment, goals, memory, entity-filtered events |
| **Clicked building** | Inspect (building name) | BuildingPanel: store inventory / recipes / guild intel |
| **Clicked loot** | Inspect ("Loot") | LootPanel: item details |

When clicking an entity (on canvas or sidebar list), the tab auto-switches to Inspect. When clicking a building on the map, the tab shows the building's name. When the selection is cleared, tabs revert to Info + Events.

### BuildingPanel

The `BuildingPanel` component renders rich info panels based on building type:

| Building | Panel Content |
|----------|---------------|
| **General Store** | Buy inventory with prices, item stats, sell price tiers by rarity |
| **Blacksmith** | All 7 crafting recipes with materials, gold cost, output item stats |
| **Adventurer's Guild** | Services (camp intel, material hints), material source guide |

---

## Key Hooks

### `useSimulation`

Central state management hook. Handles:
- One-time map fetch on mount
- Polling `/api/v1/state` and `/api/v1/stats` every 80ms
- Exposing reactive state: `entities`, `events`, `tick`, `aliveCount`, `status`, etc.
- `sendControl(action)` and `setSpeed(tps)` callbacks
- `selectEntity(id | null)` for entity selection

```tsx
const sim = useSimulation();
// sim.entities, sim.tick, sim.status, sim.selectEntity(id), ...
```

### `useCanvas`

Canvas rendering hook. Accepts `mapData`, `entities`, `groundItems`, `buildings`, `resourceNodes`, `selectedEntityId`, and `onEntityClick`. Returns refs for the three canvas layers, click/hover handlers, and `hoverInfo` state. Uses `useEffect` to:
1. Draw the tile grid once when map data arrives
2. Redraw ground items, resource nodes, and entities every time `entities`, `groundItems`, `resourceNodes`, or `selectedEntityId` changes
3. Redraw the fog-of-war overlay and ghost markers when selection changes

**Spectate vision**: When an entity is selected, only entities and resource nodes within that entity's vision range are rendered on the entity layer. Entities outside vision are hidden; remembered-but-not-visible entities appear as ghost markers on the overlay.

**Hover detection**: `onMouseMove` resolves the grid cell under the cursor and checks entities first, then ground items, then resource nodes. Returns a `HoverInfo` object with screen coordinates and label text.

---

## Inspect Panel

When an entity is selected, the `InspectPanel` component renders these sections:

### 1. Header & Stats
- Entity name with tier badge and level
- 2-column grid: Position, State, Faction, ATK/DEF, SPD/LUCK, CRIT/EVA, Gold
- HP bar (color-coded: green > 50%, yellow > 25%, red below)
- XP bar (purple fill)

### 2. Equipment
Three equip slots displayed with shorthand unicode strings:

| Slot | Format |
|------|--------|
| Weapon | `⚔ Iron Sword` |
| Armor | `🛡 Chainmail` |
| Accessory | `💍 Speed Ring` |

Inventory bag items are shown as small bordered tags below equipment slots.

**Item hover tooltips**: Both equipment slots and inventory bag items use the `ItemWithTooltip` component. Hovering over any item shows a floating popup with:
- Item name (color-coded by rarity)
- Item type and rarity
- Stat bonuses (ATK, DEF, SPD, CRIT, EVA, LUCK, max HP)
- Consumable effects (heal amount, gold value)

Item stats are defined in `ITEM_STATS` in `constants/colors.ts`, and rarity colors in `RARITY_COLORS`:
```ts
export const RARITY_COLORS: Record<string, string> = {
  common: '#9ca3af',
  uncommon: '#34d399',
  rare: '#a78bfa',
};
```

### 3. Goals & Thoughts
Derived behavioral goals shown as a bulleted list with `◆` markers. Goals are computed server-side based on entity state, HP, level, inventory, exploration progress, and territory awareness (e.g. "Trespassing on enemy territory", "Weakened by hostile territory", "Intruder detected!").

### 4. Craft Target (hero only)
If the hero has a `craft_target`, a collapsible section shows:
- Current crafting goal item name
- Number of known recipes

### 5. Memory & Vision
- **Vision Range**: tiles (Manhattan distance)
- **Tiles Explored**: count / total (percentage)
- **Entities Remembered**: count of tracked entities
- **Remembered entity list**: sorted by recency, showing kind, level, ATK, position, and whether currently visible or stale

### 6. Entity Events (when spectating)
A collapsible sub-section showing the last 20 events filtered to the spectated entity. Events are matched by entity ID appearing in the event message. This replaces the former separate entity events tab.

---

## Vision Overlay

The overlay canvas (rendered in `useCanvas`) draws a **fog-of-war** effect when an entity is selected:

### Three Visibility States

| State | Visual | Description |
|-------|--------|-------------|
| **Visible** | Clear (no overlay) | Within current vision range |
| **Remembered** | Semi-transparent dark (55% opacity) | Previously seen, stored in `terrain_memory` |
| **Unknown** | Heavy dark fog (82% opacity) | Never explored |

### Vision Range Border
A faint blue (`rgba(74, 158, 255, 0.3)`) outline is drawn around the edges of the visible area by checking each tile's 4 neighbors.

### Ghost Entity Markers
Remembered entities from the spectated entity's `entity_memory` are drawn on the overlay as ghosts, with specific filtering rules:
- **Skip if currently visible**: If the entity is within the spectated entity's vision and present on the entity layer, no ghost is drawn.
- **Skip if remembered position is in vision**: If the remembered position is within the current vision cone but the entity has moved away, no ghost is drawn (avoids stale markers in visible tiles).
- **Skip if position unexplored**: Ghosts only appear on tiles in `terrain_memory`.

Ghost markers render as:
- Small semi-transparent circle in the entity's kind color
- Dashed stroke border
- `?` question mark label

This gives the player an accurate sense of where enemies were **last seen** by the spectated entity.

---

## Color Palette

All colors are defined in `src/constants/colors.ts` and the Tailwind theme in `src/index.css`.

### Tile Colors
| Material | Value | Color | Hex |
|----------|-------|-------|-----|
| Floor | 0 | Dark navy | `#1a1d27` |
| Wall | 1 | Grey | `#555b73` |
| Water | 2 | Deep blue | `#1e3a5f` |
| Town | 3 | Dark green | `#2d4a3e` |
| Camp | 4 | Dark red | `#4a2d2d` |
| Sanctuary | 5 | Blue-grey | `#2d3a4a` |
| Forest | 6 | Dark green | `#1b3a1b` |
| Desert | 7 | Sandy brown | `#3a3420` |
| Swamp | 8 | Dark purple-grey | `#2a2a3a` |
| Mountain | 9 | Stone grey | `#3a3a3a` |

### Entity Colors (by kind)
| Kind | Color | Hex |
|------|-------|-----|
| Hero | Blue | `#4a9eff` |
| Goblin | Red | `#f87171` |
| Goblin Scout | Orange | `#fb923c` |
| Goblin Warrior | Deep Red | `#dc2626` |
| Goblin Chief | Gold | `#fbbf24` |
| Wolf | Silver | `#a0a0a0` |
| Dire Wolf | Dark grey | `#808080` |
| Alpha Wolf | Light silver | `#c0c0c0` |
| Bandit | Sandy orange | `#e0a050` |
| Bandit Archer | Dark sandy | `#d4943c` |
| Bandit Chief | Bright sandy | `#f0c060` |
| Skeleton | Bone white | `#b0b8c0` |
| Zombie | Pale green | `#70a070` |
| Lich | Purple | `#c080ff` |
| Orc | Forest green | `#60a060` |
| Orc Warrior | Dark green | `#408040` |
| Orc Warlord | Lime green | `#80c040` |

### AI State Colors
| State | Color | Hex |
|-------|-------|-----|
| IDLE | Grey | `#8b8fa8` |
| WANDER | Green | `#34d399` |
| HUNT | Yellow | `#fbbf24` |
| COMBAT | Red | `#f87171` |
| FLEE | Purple | `#a78bfa` |
| RETURN_TO_TOWN | Blue | `#60a5fa` |
| RESTING_IN_TOWN | Cyan | `#22d3ee` |
| RETURN_TO_CAMP | Orange | `#f97316` |
| GUARD_CAMP | Bright Red | `#ef4444` |
| LOOTING | Lime | `#a3e635` |
| ALERT | Coral Red | `#ff6b6b` |
| VISIT_SHOP | Sky Blue | `#38bdf8` |
| VISIT_BLACKSMITH | Amber | `#f59e0b` |
| VISIT_GUILD | Indigo | `#818cf8` |
| HARVESTING | Mint green | `#7dd3a0` |

---

### Item Types

The `ITEM_STATS` registry in `constants/colors.ts` defines all item metadata for tooltips:

| Type | Examples |
|------|----------|
| `weapon` | Wooden Club, Iron Sword, Steel Sword, Battle Axe, Enchanted Blade, Goblin Cleaver |
| `armor` | Leather Vest, Chainmail, Iron Plate, Enchanted Robe, Goblin Guard |
| `accessory` | Lucky Charm, Speed Ring, Evasion Amulet, Ring of Power |
| `consumable` | Health potions (S/M/L), Gold pouches (S/M/L), Camp Treasure |
| `material` | Wood, Leather, Iron Ore, Steel Bar, Enchanted Dust, Herb, Fiber, Dark Moss, Stone Block, Wolf Pelt, Wolf Fang, Bone Shard, Ectoplasm, Raw Gem, Glowing Mushroom |

Rarity tiers: **Common** (grey), **Uncommon** (green), **Rare** (purple).

---

## Ground Items (Loot)

Dropped items appear on the map as green diamonds rendered on the entity canvas layer.

- **Shape**: Small diamond (rotated square, `CELL_SIZE * 0.28`)
- **Color**: Lime green (`#a3e635`) with a matching glow (`shadowBlur: 4`)
- **Badge**: If a tile has multiple items, a white count badge is drawn
- **Visibility**: When spectating, only loot within the selected entity's vision range is shown
- **Hover**: Hovering shows either the single item name or "Loot bag (N items)"

The API provides ground items via `WorldStateResponse.ground_items[]` as `GroundItemSchema { x, y, items[] }`.

---

## Entity Rendering

Canvas rendering is handled imperatively in the `useCanvas` hook.

### Hero
- **Shape**: Diamond (rotated square)
- **Glow**: Golden shadow blur (`#fbbf24`, blur 6px)
- **State border**: Colored outline matching AI state
- **ID label**: Bold white monospace

### Goblins / Mobs
- **Shape**: Circle
- **Size**: `CELL_SIZE * 0.35` radius
- **State border**: Colored ring matching AI state
- **ID label**: Semi-transparent white monospace
- **Color**: Kind-specific from `KIND_COLORS` (wolves grey, bandits sandy, undead bone/green/purple, orcs green)

### Resource Nodes
- **Shape**: Small filled square with 1px border (inset 2px from cell edge)
- **Available**: 50% opacity fill + solid 1px border in resource-type color
- **Depleted**: Grey (`#4a5568`) at 30% opacity, no border
- **Colors**: Each resource type has a unique color in `RESOURCE_COLORS` (e.g. herb_patch=mint, timber=brown, gem_deposit=purple)
- **Hover**: Shows node name, remaining/max harvests, and yielded item name
- **Minimap**: Small colored dots (green if available, grey if depleted)

### Selection
- White dashed circle ring (`CELL_SIZE * 0.55` radius)

### HP Bars
- 2px tall bar above each entity
- Green (>50%) → Yellow (>25%) → Red (<25%)

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
```

### Polling Strategy

The `useSimulation` hook polls `GET /api/v1/state` and `GET /api/v1/stats` every 80ms using `setTimeout`. The map grid is fetched once on mount since tiles don't change at runtime. Events support delta fetching via `since_tick`.

Each entity in the API response carries: stats, equipment, inventory_items, vision_range, terrain_memory, entity_memory, and goals — all needed for the Inspect panel and overlay rendering.

---

## Development

### Dev Server

```bash
cd frontend
npm install
npm run dev          # Starts Vite on http://localhost:5173
```

Vite proxies `/api/*` requests to the backend at `http://127.0.0.1:8000`.

### Production Build

```bash
cd frontend
npm run build        # Outputs to frontend/dist/
```

The FastAPI backend serves `frontend/dist/` as static files at `/`.

### Type Safety

All API response shapes are defined in `src/types/api.ts`, matching the Pydantic schemas in `src/api/schemas.py`:
- `Entity` — full entity with stats, faction, equipment, memory, goals, known_recipes, craft_target
- `Building` — building_id, name, x, y, building_type
- `GameEvent` — tick + category + message
- `GroundItem` — x, y, items[] (dropped loot on the ground)
- `ResourceNode` — node_id, resource_type, name, x, y, terrain, yields_item, remaining, max_harvests, is_available, harvest_ticks
- `WorldState` — tick, alive_count, entities[], events[], ground_items[], buildings[], resource_nodes[]
- `SimulationStats` — counters + running/paused flags
- `MapData` — width, height, grid[][]
