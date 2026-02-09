# Technical Architecture

This document describes the runtime architecture, concurrency model, API layer, and frontend visualization of the RPG Simulation Engine.

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI Server                      │
│  ┌──────────┐  ┌────────────┐  ┌─────────────────────┐ │
│  │  Routes   │  │  Schemas   │  │  Static Files       │ │
│  │ /api/v1/* │  │ (Pydantic) │  │ frontend/index.html │ │
│  └─────┬─────┘  └────────────┘  └─────────────────────┘ │
│        │ Depends()                                       │
│  ┌─────▼──────────────────────────────────────────────┐ │
│  │              EngineManager (singleton)               │ │
│  │  ┌──────────────┐  ┌───────────┐  ┌─────────────┐ │ │
│  │  │ Atomic        │  │ EventLog  │  │ Controls    │ │ │
│  │  │ Snapshot Ref  │  │ RingBuf   │  │ pause/step  │ │ │
│  │  └──────┬───────┘  └───────────┘  └─────────────┘ │ │
│  └─────────┼──────────────────────────────────────────┘ │
└────────────┼────────────────────────────────────────────┘
             │ atomic swap (threading.Lock)
┌────────────▼────────────────────────────────────────────┐
│               Engine Thread (daemon)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │                  WorldLoop                        │   │
│  │  tick_once() → _step() → create_snapshot()        │   │
│  │                                                    │   │
│  │  Phase 1: Generators + Scheduling                  │   │
│  │  Phase 2: Worker dispatch → collect proposals      │   │
│  │  Phase 3: Conflict resolution → apply actions      │   │
│  │  Phase 4: Cleanup, territory effects, tick effects  │   │
│  └──────────────────────────────────────────────────┘   │
│  ┌─────────────┐  ┌───────────────┐  ┌──────────────┐  │
│  │ WorkerPool   │  │ ConflictRes.  │  │ EntityGen.   │  │
│  │ (ThreadPool) │  │ (deterministic│  │ (spawner)    │  │
│  └─────────────┘  └───────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Concurrency Model

### Single-Writer / Multi-Reader

The engine enforces a strict concurrency discipline:

| Component | Thread | Access |
|-----------|--------|--------|
| `WorldState` | Engine thread only | Read + Write |
| `Snapshot` | Any thread | Read-only (immutable) |
| `EventLog` | Any thread | Lock-guarded append/read |
| `EngineManager._latest_snapshot` | Any thread | Atomic swap via `threading.Lock` |

**Why this works:**
- The `WorldLoop` is the sole writer of `WorldState`. It never exposes mutable state.
- After each tick, `WorldLoop.create_snapshot()` deep-copies entities into a frozen `Snapshot`.
- `EngineManager` atomically swaps the snapshot reference under a lock.
- HTTP handlers read the snapshot without blocking the engine thread.

### Thread Layout

```
Main Thread          → Uvicorn event loop (HTTP requests)
Engine Thread        → WorldLoop.tick_once() in a while-loop
Worker Threads (N)   → AIBrain.decide() via ThreadPoolExecutor
```

## Tick Cycle (4 Phases)

Each tick proceeds through four sequential phases inside `WorldLoop._step()`:

### Phase 1: Scheduling
- Run entity generators (spawn new goblins on interval)
- Identify entities where `next_act_at <= current_tick`
- Sort by `(next_act_at, entity_id)` for determinism

### Phase 2: Wait & Collect
- Create an immutable `Snapshot` of current world
- Dispatch ready entities to `WorkerPool` (parallel AI)
- Each worker calls `AIBrain.decide(entity, snapshot)` → returns `(new_state, ActionProposal)`
- Drain all proposals from the thread-safe `ActionQueue`

### Phase 3: Conflict Resolution
- `ConflictResolver.resolve()` validates and applies proposals
- Move conflicts: first-come-first-served by entity ID
- Attack validation: target must exist and be adjacent
- All applied actions update `WorldState` in deterministic order

### Phase 4: Cleanup & Effects
- **Town aura**: hostile entities on TOWN tiles take `town_aura_damage` HP per tick (prevents spawn camping)
- **Passive heal**: heroes in town regen `town_passive_heal` HP per tick even while not resting, blocked when adjacent hostile exists
- **Resting heal**: heroes in `RESTING_IN_TOWN` state heal at the faster `hero_heal_per_tick` rate (also blocked by adjacent hostiles)
- **Camp heal**: goblins guarding camp heal 1 HP per tick
- Remove dead entities (`hp <= 0`), drop loot (including crafting materials), respawn heroes
- **Territory intrusion**: apply stat debuffs to entities on hostile tiles, alert nearby defenders (→ `ALERT` state)
- **Tick effects**: decrement status effect durations, remove expired effects
- Level-up checks
- Update entity memory (terrain + entity sightings) and goals
- Record tick to replay log (CLI mode)

## API Layer

### Architecture

```
src/api/
├── app.py           # create_app() factory with lifespan
├── engine_manager.py # Singleton managing engine thread
├── dependencies.py   # FastAPI Depends() for DI
├── schemas.py        # Pydantic response models
└── routes/
    ├── map.py        # GET /api/v1/map
    ├── state.py      # GET /api/v1/state, /stats
    ├── control.py    # POST /api/v1/control/{action}, /speed
    └── config.py     # GET /api/v1/config
```

### Lifespan

The FastAPI app uses a lifespan context manager:

1. **Startup**: `EngineManager` is created, builds the world, starts the engine thread
2. **Shutdown**: Engine thread is stopped, worker pool is shut down

### Dependency Injection

All routes receive `EngineManager` via `Depends(get_engine_manager)`. The singleton is stored in `app.state.engine` during lifespan startup.

### Endpoints

| Method | Path | Description | Response Model |
|--------|------|-------------|---------------|
| GET | `/api/v1/map` | Static grid (fetch once) | `MapResponse` |
| GET | `/api/v1/state?since_tick=N` | Entities + events since tick N | `WorldStateResponse` |
| GET | `/api/v1/stats` | Counters + status | `SimulationStats` |
| GET | `/api/v1/config` | Simulation parameters | `SimulationConfigResponse` |
| POST | `/api/v1/control/{action}` | start/pause/resume/step/reset | `ControlResponse` |
| POST | `/api/v1/speed?tps=N` | Set ticks per second | `ControlResponse` |

### Snapshot Flow

```
Engine Thread:
  tick_once() → _step() → create_snapshot()
  │
  └─► EngineManager._publish_snapshot_and_events()
        ├─ lock → swap _latest_snapshot → unlock
        └─ event_log.append_many(events)

HTTP Thread:
  GET /state → manager.get_snapshot()
        └─ lock → read _latest_snapshot → unlock → serialize → JSON
```

## Faction System

Every entity belongs to a **Faction** (e.g. `HERO_GUILD`, `GOBLIN_HORDE`). Relationships between factions are stored in a `FactionRegistry` and looked up at runtime.

### Key Components

| Component | File | Purpose |
|-----------|------|---------|
| `Faction` | `core/faction.py` | Enum of faction identities |
| `FactionRelation` | `core/faction.py` | `ALLIED`, `NEUTRAL`, `HOSTILE` |
| `FactionRegistry` | `core/faction.py` | Data-driven registry: relations, territories, kind→faction |
| `TerritoryInfo` | `core/faction.py` | Debuff multipliers + alert radius per territory |
| `StatusEffect` | `core/effects.py` | Temporary stat modifier with duration |
| `EffectType` | `core/effects.py` | Categories: `TERRITORY_DEBUFF`, `TERRITORY_BUFF`, `POISON`, etc. |

### Faction Relationships

| Faction A | Faction B | Relation |
|-----------|-----------|----------|
| HERO_GUILD | GOBLIN_HORDE | HOSTILE |
| Same faction | Same faction | ALLIED (implicit) |

New factions are added by extending the `Faction` enum, calling `set_relation()`, and `register_kind()` on the registry. Zero AI or combat code changes needed.

### Territory Intrusion

Each faction owns a tile type (HERO_GUILD → TOWN, GOBLIN_HORDE → CAMP). When an entity steps on a hostile faction's territory:

1. **Debuff applied**: ATK/DEF/SPD multipliers (e.g. 0.6–0.7×) via `StatusEffect`
2. **Alert propagated**: All same-faction defenders within `alert_radius` switch to `ALERT` AI state
3. **Debuff removed**: Automatically cleared when the entity leaves enemy territory

Debuffs flow through `Entity.effective_*()` methods, so combat and movement automatically reflect them with no special-case code.

### Status Effects

`StatusEffect` is a generic system for temporary stat modifiers:
- Multiplicative stat modifiers (`atk_mult`, `def_mult`, `spd_mult`, `crit_mult`, `evasion_mult`)
- Flat modifiers (`hp_per_tick` for regen/DoT)
- Duration in ticks (0 = permanent until removed)
- Factory helpers: `territory_debuff()`, `territory_buff()`

Effects are ticked down each simulation tick and expired effects are pruned automatically.

## Town Buildings & Economy

Three static buildings are placed in the town during world generation (`engine_manager.py`):

| Building | ID | Position | Purpose |
|----------|----|----------|---------|
| General Store | `store` | Top-left of town | Buy/sell items |
| Blacksmith | `blacksmith` | Top-right of town | Learn recipes, craft powerful gear |
| Adventurer's Guild | `guild` | Bottom-center of town | Camp intel, material hints |

Buildings are stored in `WorldState.buildings` as `Building` dataclass instances and exposed to the frontend via `BuildingSchema` in the API.

### Crafting Materials

Materials drop from enemies across all terrain regions and from harvestable resource nodes:

| Material | Rarity | Source |
|----------|--------|--------|
| Wood | Common | Basic goblins, Timber nodes (forest) |
| Leather | Common | Goblins, scouts, wolves |
| Iron Ore | Uncommon | Warriors, orcs, ore nodes |
| Steel Bar | Uncommon | Warriors, orc warriors (rare) |
| Enchanted Dust | Rare | Elite goblins, liches, orc warlords, Crystal Nodes |
| Wolf Pelt | Common | Wolves (forest) |
| Wolf Fang | Uncommon | Dire wolves, alpha wolves (forest) |
| Fiber | Common | Bandits (desert), Cactus Fiber nodes |
| Raw Gem | Uncommon | Bandit archers/chiefs (desert) |
| Bone Shard | Common | Skeletons, zombies (swamp) |
| Ectoplasm | Uncommon | Zombies, liches (swamp) |
| Stone Block | Common | Orcs (mountain), Granite Quarries |
| Herb | Common | Herb Patch nodes (forest) |

### Crafting Recipes

Fourteen recipes convert gold + materials into powerful equipment. Seven use goblin-sourced materials, seven use race-specific materials from terrain regions (forest, desert, swamp, mountain). Heroes learn recipes by visiting the blacksmith, then gather materials through combat and harvesting before returning to craft.

### Economy AI Flow

After healing in town, `RestingInTownHandler` evaluates economy actions in priority order:
1. Sell unused items → `VISIT_SHOP`
2. Buy upgrade/potions → `VISIT_SHOP`
3. Learn recipes or craft → `VISIT_BLACKSMITH`
4. Get camp intel → `VISIT_GUILD`
5. Leave town → `WANDER`

See **[docs/buildings_economy.md](buildings_economy.md)** for full details on shop inventory, recipes, and AI decision logic.

## Entity System

### Entity Types

| Kind | Faction | Base HP | Base ATK | Base SPD | Spawning |
|------|---------|---------|----------|----------|----------|
| `hero` | HERO_GUILD | 40–55 | 8–12 | 10–13 | Once at init (1 per simulation) |
| `goblin` | GOBLIN_HORDE | 15–25 | 3–7 | 8–12 | At init + generator spawns |
| `goblin_scout` | GOBLIN_HORDE | Tier-scaled | Tier-scaled | Tier-scaled | Generator spawns |
| `goblin_warrior` | GOBLIN_HORDE | Tier-scaled | Tier-scaled | Tier-scaled | Camp guards |
| `goblin_chief` | GOBLIN_HORDE | Tier-scaled | Tier-scaled | Tier-scaled | Camp leaders |
| `wolf` / `dire_wolf` / `alpha_wolf` | WOLF_PACK | Race-scaled | Race-scaled | Fast (+2) | Forest regions |
| `bandit` / `bandit_archer` / `bandit_chief` | BANDIT_CLAN | Race-scaled | Race-scaled | Agile (+1) | Desert regions |
| `skeleton` / `zombie` / `lich` | UNDEAD | Tanky (1.3×) | Low (0.8×) | Slow (-2) | Swamp regions |
| `orc` / `orc_warrior` / `orc_warlord` | ORC_TRIBE | Beefy (1.2×) | Strong (1.2×) | Slow (-1) | Mountain regions |

### AI State Machine

State handlers are class-based (`StateHandler` ABC) and registered in a `STATE_HANDLERS` dict. The `AIBrain` dispatches via `AIContext` — a single dataclass bundling actor, snapshot, config, RNG, and faction registry.

```
         ┌───────────┐
    ┌───►│   IDLE    │
    │    └─────┬─────┘
    │          │ (always transitions)
    │    ┌─────▼─────┐    enemy visible    ┌──────────┐
    ├────│  WANDER   │───────────────────►│   HUNT   │
    │    └─────┬─────┘                     └────┬─────┘
    │          │ low HP                         │ adjacent
    │    ┌─────▼─────┐                     ┌────▼─────┐
    ├────│   FLEE    │◄────── low HP ──────│  COMBAT  │
    │    └─────┬─────┘                     └──────────┘
    │          │ HP recovered                    ▲
    │          └──────────────────────────►│   HUNT   │
    │                                      └──────────┘
    │    ┌───────────┐                     ┌──────────┐
    │    │  LOOTING  │                     │  ALERT   │
    │    └───────────┘                     └────┬─────┘
    │                                           │ enemy found → HUNT
    │                                           │ no enemy → GUARD_CAMP
    └──────── no enemies visible ─────────────────────┘
```

**New state: ALERT** — triggered when a territory intrusion is detected. Defenders in ALERT seek and engage the intruder, then return to guard duty.

**New state: HARVESTING** — hero is channeling a resource harvest or moving toward a resource node. Interrupted by enemies within 3 tiles or low HP.

**Economy states** (hero only):

```
  RESTING_IN_TOWN (fully healed)
        │
        ├── has sellable items ──────► VISIT_SHOP ───► sell / buy ──► back
        ├── needs recipes / can craft ► VISIT_BLACKSMITH ► learn / craft ► back
        ├── lacks camp intel ─────────► VISIT_GUILD ──► get intel ──► back
        └── nothing to do ────────────► WANDER
```

| State | Trigger | Behaviour |
|-------|---------|----------|
| `VISIT_SHOP` | Sellable items or buyable upgrade | Walk to store → sell inferior gear/materials, buy potions/upgrades |
| `VISIT_BLACKSMITH` | No recipes learned, or can craft | Walk to blacksmith → learn all recipes, craft if materials+gold available |
| `VISIT_GUILD` | No goblin camp intel in memory | Walk to guild → receive camp locations + material source hints |

### Deterministic RNG

All randomness uses `DeterministicRNG` backed by xxhash:

```
hash = xxhash64(WorldSeed || Domain || EntityID || Tick || SubKey)
```

This ensures:
- Same seed → identical simulation
- Domain separation prevents cross-system correlation
- Replays are byte-exact

## Frontend Visualization

The frontend is a **React 19 + TypeScript** SPA built with **Vite** and **Tailwind CSS v4**. Source lives in `frontend/src/`, production build outputs to `frontend/dist/`.

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Build | Vite (HMR, API proxy to backend) |
| Framework | React 19 + TypeScript |
| Styling | Tailwind CSS v4 |
| Icons | Lucide React |
| Canvas | HTML5 Canvas via React refs (`useCanvas` hook) |

### Triple-Layer Canvas

| Layer | Ref | Redrawn | Content |
|-------|-----|---------|---------|
| 1 | `gridRef` | Once | Tile map (floor/wall/water) + grid lines |
| 2 | `entityRef` | Every poll (~80ms) | Ground items (loot), entities, HP bars, selection highlights |
| 3 | `overlayRef` | On selection change | Fog-of-war, vision border, ghost entity markers |

### Key Components

| Component | Purpose |
|-----------|---------|
| `App` | Root layout (Header + GameCanvas + Sidebar) |
| `Header` | Status bar (tick, alive, spawned, deaths, sim status) |
| `GameCanvas` | Canvas wrapper with three layers + hover tooltip |
| `Sidebar` | Tab container with ControlPanel always visible |
| `InspectPanel` | Full entity stats, equipment (with item hover tooltips), goals, memory |
| `EntityList` | Sorted entity list with HP bars |
| `EventLog` | Scrollable combat/event log |
| `BuildingPanel` | Building info (store inventory, recipes, guild intel) |
| `LootPanel` | Ground item detail view |

### Key Hooks

| Hook | Purpose |
|------|---------|
| `useSimulation` | API polling (80ms), React state, control/speed callbacks |
| `useCanvas` | Imperative canvas rendering, hover detection, spectate vision filtering |

### Entity Rendering

| Kind | Shape | Color | Effect |
|------|-------|-------|--------|
| `hero` | Diamond | Blue (#4a9eff) | Golden glow (shadowBlur) |
| `goblin` | Circle | Red (#f87171) | State-colored ring |

### Click-to-Inspect

Click priority on the canvas: **entities → buildings → ground items**. Clicking an entity on the canvas or in the sidebar opens the **InspectPanel** component, showing:
- Entity ID, kind, position, level, tier
- AI state (color-coded)
- ATK/DEF, SPD/LUCK, CRIT/EVA, Gold
- HP bar and XP bar with numeric values
- Equipment slots and inventory (hover for detailed item stats)
- Goals & thoughts
- Memory & vision (explored tiles, remembered entities)

The selected entity gets a dashed white ring on the canvas.

### Hover Tooltips

Moving the cursor over an entity or ground loot on the canvas shows a floating tooltip with:
- **Entities**: `#ID kind LvN`
- **Ground items**: item name or `Loot bag (N items)`
- **Resource nodes**: name, remaining/max harvests, yielded item

In the InspectPanel, hovering over equipment or inventory items shows a detailed popup with item name, type, rarity (color-coded), and all stat bonuses.

### Spectate Vision

Selecting (spectating) an entity restricts the entity layer to only render entities within the spectated entity's vision range. Entities outside vision are hidden entirely. Ghost markers for remembered-but-not-visible entities are drawn on the overlay, filtered to avoid stale markers in visible tiles.

### Polling Strategy

The `useSimulation` hook polls `GET /api/v1/state` and `GET /api/v1/stats` every 80ms. Events support delta fetching via `since_tick` to avoid redundant data transfer. The map is fetched once on mount.

## Configuration

All simulation parameters are defined in `SimulationConfig` (frozen dataclass):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `world_seed` | 42 | Deterministic seed |
| `grid_width` / `grid_height` | 128 | Map dimensions |
| `max_ticks` | 1000 | Simulation length |
| `num_workers` | 4 | AI thread pool size |
| `initial_entity_count` | 25 | Starting entities |
| `generator_spawn_interval` | 10 | Ticks between spawns |
| `generator_max_entities` | 80 | Entity cap |
| `vision_range` | 6 | AI perception radius |
| `flee_hp_threshold` | 0.3 | HP ratio to trigger flee |
| `territory_debuff_duration` | 3 | Ticks debuff lasts after leaving |
| `territory_alert_radius` | 6 | How far intrusion alert propagates |
| `sanctuary_radius` | 7 | Buffer zone around town |
| `town_aura_damage` | 2 | HP lost per tick by hostiles in town |
| `town_passive_heal` | 1 | HP regained per tick by heroes in town (passive) |
| `num_forest/desert/swamp/mountain_regions` | 4/3/3/3 | Terrain region counts |
| `region_min_radius` / `region_max_radius` | 6 / 12 | Region size range |
| `resources_per_region` | 4 | Resource nodes per region |
| `harvest_duration` | 2 | Default harvest channel ticks |

## File Map

```
rpg-based-simulation/
├── src/
│   ├── __main__.py           # CLI entry: serve (default) or cli mode
│   ├── config.py             # SimulationConfig
│   ├── api/                  # FastAPI server layer
│   │   ├── app.py            #   App factory (serves frontend/dist/ at /)
│   │   ├── engine_manager.py #   Background thread wrapper
│   │   ├── dependencies.py   #   FastAPI dependency injection
│   │   ├── schemas.py        #   Pydantic response models
│   │   └── routes/           #   Versioned REST endpoints
│   ├── core/                 # Data models, grid, world state, snapshot
│   │   ├── faction.py        #   Faction enum, FactionRelation, FactionRegistry, TerritoryInfo
│   │   ├── effects.py        #   StatusEffect, EffectType, factory helpers
│   │   ├── models.py         #   Vector2, Stats, Entity (with faction + effects)
│   │   ├── buildings.py      #   Building model, shop/recipe/guild config, economy helpers
│   │   ├── items.py          #   ItemTemplate, Inventory, ITEM_REGISTRY, LOOT_TABLES, RACE_* tables
│   │   ├── resource_nodes.py #   ResourceNode model, TERRAIN_RESOURCES definitions
│   │   └── ...               #   enums, grid, world_state, snapshot
│   ├── engine/               # WorldLoop, action queue, workers, resolver
│   ├── actions/              # Action handlers (move, combat, rest)
│   ├── ai/                   # Brain, perception, class-based state handlers
│   ├── systems/              # RNG, spatial hash, entity generator
│   └── utils/                # Logging, event log, replay recorder
├── frontend/                 # React + Vite + TypeScript SPA
│   ├── package.json          #   Node dependencies
│   ├── vite.config.ts        #   Build config + API proxy
│   ├── src/
│   │   ├── App.tsx           #   Root component
│   │   ├── hooks/            #   useSimulation, useCanvas
│   │   ├── components/       #   Header, GameCanvas, Sidebar, InspectPanel, ...
│   │   ├── types/            #   TypeScript API interfaces
│   │   └── constants/        #   Colors, item names
│   └── dist/                 #   Production build (gitignored)
├── docs/
│   ├── architecture.md       # This document
│   ├── frontend.md           # Frontend tech docs
│   ├── api_reference.md      # REST API reference
│   ├── buildings_economy.md  # Town buildings, shop, blacksmith, guild, crafting
│   ├── terrains_resources.md # Terrain regions, resource nodes, new mobs, harvesting
│   └── ...                   # Proposals, RPG systems, etc.
├── requirements.txt
└── pyproject.toml
```
