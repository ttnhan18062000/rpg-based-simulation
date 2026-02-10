# System Architecture

Technical documentation for the runtime architecture, concurrency model, and project structure.

---

## Overview

The RPG simulation engine is a **deterministic concurrent system** that simulates a living 2D world with autonomous entities. The core principle: heavy AI logic runs in parallel threads while world mutation is strictly single-threaded.

**Key guarantees:**

1. **Single-Writer / Multi-Reader** — Only `WorldLoop` mutates `WorldState`; workers read immutable snapshots
2. **Absolute Determinism** — Given a `WorldSeed`, the simulation reproduces the exact same state on any machine
3. **Intent vs Effect** — Workers produce `ActionProposal` (intent); `WorldLoop` resolves and applies effects
4. **Atomic Ticks** — All actions for tick N are resolved before tick N+1 begins

**Primary files:** `src/engine/world_loop.py`, `src/core/world_state.py`, `src/core/snapshot.py`, `src/api/engine_manager.py`

---

## Concurrency Model

### Thread Layout

| Thread | Role | Reads | Writes |
|--------|------|-------|--------|
| **Main** (uvicorn) | HTTP request handling | `latest_snapshot`, `EventLog` | Control signals |
| **Engine** (`WorldLoop`) | Tick cycle, mutation | `WorldState` | `WorldState`, `Snapshot` |
| **Workers** (ThreadPool) | AI computation | `Snapshot` (immutable) | `ActionQueue` (thread-safe) |

### Data Flow

```
WorldLoop ──1. creates──▶ Snapshot (immutable)
                              │
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
                Worker 1   Worker 2   Worker 3
                    │         │         │
                    └─────────┼─────────┘
                              ▼
                     ActionQueue (thread-safe)
                              │
                    ◀─2. consumed by── WorldLoop
                              │
                    3. mutates ──▶ WorldState
```

Workers never see partial updates. The `ActionQueue` is the only shared mutable structure between workers and the engine thread.

---

## Tick Cycle (4 Phases)

Each tick in `WorldLoop._step()` executes:

### Phase 1: Scheduling

- Identify entities whose `next_act_at <= current_tick`
- Generators execute immediately (spawn actions)
- Characters are dispatched to the worker pool with an immutable `Snapshot`

### Phase 2: Wait & Collect

- Workers compute `ActionProposal` from the snapshot and push to `ActionQueue`
- Hard timeout (`worker_timeout_seconds`, default 2s) prevents engine stalls — late entities miss their turn

### Phase 3: Conflict Resolution & Application

- Sort proposals deterministically (by `next_act_at`, then `entity_id`)
- Validate each proposal (bounds, adjacency, alive checks)
- Apply valid actions to `WorldState` (move, attack, loot, harvest, use_skill, use_item)
- Reject invalid actions with logged reasons

### Phase 4: Cleanup & Effects

- Remove dead entities, drop loot
- Process territory effects (debuffs, alerts, aura damage)
- Tick status effects (decrement durations, apply hp_per_tick, prune expired)
- Tick resource node cooldowns
- Check level-ups (stat growth + attribute gains)
- Regenerate stamina, tick skill cooldowns
- Update entity memory (terrain + entity)
- Tick quests (EXPLORE completion, pruning)
- Update entity goals (display text)
- Advance tick counter

---

## Core Data Structures

### WorldState (Mutable, Private)

The authoritative "truth". Never exposed directly to workers.

| Field | Type | Description |
|-------|------|-------------|
| `tick` | int | Current simulation tick |
| `entities` | dict[int, Entity] | All living entities by ID |
| `grid` | Grid | 2D tile grid |
| `ground_items` | dict[tuple, list[str]] | Dropped loot by position |
| `buildings` | list[Building] | Town buildings |
| `camps` | list[Vector2] | Camp center positions |
| `resource_nodes` | dict[int, ResourceNode] | Harvestable nodes by ID |
| `treasure_chests` | dict[int, TreasureChest] | Lootable chests by ID |

### Snapshot (Immutable, Public)

Point-in-time read-only view for workers and the API layer. Created at the start of each tick.

Uses `MappingProxyType` for entity dict and tuples for lists to prevent mutation. Contains only what AI needs: entities, grid, camps, buildings, resource nodes, treasure chests.

### ActionProposal

```python
@dataclass
class ActionProposal:
    actor_id: int
    verb: ActionType      # MOVE, ATTACK, REST, USE_ITEM, LOOT, HARVEST, USE_SKILL
    target: Any           # Coordinates, EntityID, or item ID
    reason: str           # Debug string
```

---

## Deterministic RNG

All randomness uses `DeterministicRNG` (`src/systems/rng.py`) with **domain-separated hashing**.

**Formula:** `value = hash64(world_seed, domain, entity_id, tick)`

### RNG Domains

| Domain | Value | Usage |
|--------|-------|-------|
| COMBAT | 0 | Damage variance, crit rolls, evasion rolls |
| LOOT | 1 | Item drops, chest loot |
| AI_DECISION | 2 | Goal tie-breaking |
| SPAWN | 3 | Entity stat rolls, tier selection |
| WEATHER | 4 | (Reserved) |
| LEVEL_UP | 5 | Level-up variance |
| ITEM | 6 | Item-related rolls |
| HARVEST | 7 | Harvest-related rolls |
| MAP_GEN | 8 | World generation |

**Key benefit:** Adding a new feature with a new domain does not change existing RNG sequences.

---

## API Layer

The FastAPI backend (`src/api/`) bridges the simulation to HTTP clients.

### EngineManager

Singleton wrapper that:
1. Builds the world (grid, zones, buildings, entities) during startup
2. Runs `WorldLoop` in a background daemon thread
3. Holds a thread-safe `latest_snapshot` reference (atomic swap after each tick)
4. Manages an unbounded `EventLog` for simulation events
5. Exposes control signals (start, pause, resume, step, reset)

### Lifespan

```
FastAPI startup → EngineManager._build() → WorldLoop thread starts
FastAPI shutdown → WorldLoop thread joins
```

### Endpoints

All under `/api/v1/`. See `api_reference.md` for full specification.

| Group | Routes | Purpose |
|-------|--------|---------|
| **State** | `/state`, `/stats` | Live simulation state (polled every ~80ms) |
| **Map** | `/map` | Static grid data (fetched once) |
| **Control** | `/control/{action}`, `/speed` | Simulation lifecycle |
| **Config** | `/config` | Read-only simulation config |
| **Metadata** | `/metadata/*` (8 endpoints) | Game definitions — serialized core pydantic dataclasses |

### Shared Schema Architecture

Core game definitions (`ItemTemplate`, `SkillDef`, `ClassDef`, `BreakthroughDef`, `TraitDef`) are **pydantic dataclasses** that serve as the single source of truth for both the engine and the API:

- **Runtime:** Fields like `item_type: ItemType` remain `IntEnum` for fast game logic comparisons
- **Serialization:** `Annotated[EnumType, PlainSerializer(...)]` converts enums to lowercase strings in JSON
- **No duplication:** `metadata.py` uses `TypeAdapter(CoreModel).dump_python()` to serialize core objects directly
- **Mutable types stay stdlib:** `SkillInstance`, `TreasureChest`, `Building` use standard `dataclasses.dataclass`

See `docs/design_patterns.md` §7 for full details.

### API Documentation

Three views available:
- **In-app API Docs** — custom React page in the frontend (fetches `/openapi.json`)
- **Swagger UI** — `/docs`
- **ReDoc** — `/redoc`

---

## Event System

`EventLog` (`src/utils/event_log.py`) stores `SimEvent` records. Thread-safe via a simple lock.

- **Unbounded** — all events kept since simulation start
- **Writers** append batches (once per tick)
- **Readers** snapshot slices (non-blocking copies)
- **Manual clear** via `POST /api/v1/clear_events`

---

## Configuration

`SimulationConfig` (`src/config.py`) is a frozen dataclass with all tunable parameters. Key defaults:

| Category | Parameter | Default |
|----------|-----------|---------|
| World | `grid_width` / `grid_height` | 128 × 128 |
| World | `world_seed` | 42 |
| Timing | `max_ticks` | 1000 |
| Workers | `num_workers` | 4 |
| Workers | `worker_timeout_seconds` | 2.0 |
| Entities | `initial_entity_count` | 25 |
| Entities | `generator_max_entities` | 80 |
| Town | `town_center_x/y` | 12, 12 |
| Town | `town_radius` | 4 |
| Camps | `num_camps` | 8 |
| AI | `vision_range` | 6 |
| Combat | `max_level` | 20 |

Full parameter list in `src/config.py`.

---

## Project File Map

```
src/
├── __main__.py                  # CLI entry point
├── config.py                    # SimulationConfig dataclass
├── core/                        # Data models (pydantic shared schemas)
│   ├── enums.py                 # ActionType, AIState, Material, Domain, etc.
│   ├── grid.py                  # 2D tile grid with walkability
│   ├── models.py                # Entity dataclass
│   ├── world_state.py           # Mutable world state
│   ├── snapshot.py              # Immutable snapshot for workers
│   ├── items.py                 # ItemTemplate (pydantic), Inventory, ITEM_REGISTRY
│   ├── classes.py               # ClassDef, SkillDef, BreakthroughDef (pydantic)
│   ├── traits.py                # TraitDef (pydantic), UtilityBonus, TraitRegistry
│   ├── buildings.py             # Building, Recipe, shop config
│   ├── faction.py               # Faction, FactionRelation, FactionRegistry
│   ├── effects.py               # StatusEffect, EffectType
│   ├── attributes.py            # Attributes, derived stats, training
│   ├── quests.py                # Quest, QuestType, templates
│   ├── resource_nodes.py        # ResourceNode, TERRAIN_RESOURCES
│   ├── entity_builder.py        # Fluent builder for Entity construction
│   └── vector2.py               # Vector2 position type
├── engine/
│   ├── world_loop.py            # 4-phase tick cycle (the engine core)
│   └── conflict_resolver.py     # Deterministic conflict resolution
├── actions/
│   ├── combat.py                # CombatAction (damage pipeline)
│   └── damage.py                # DamageCalculator strategy pattern
├── ai/
│   ├── brain.py                 # AIBrain (hybrid: goals + state machine)
│   ├── states.py                # StateHandler subclasses (18 states)
│   ├── perception.py            # Vision, memory, faction-aware queries
│   ├── goal_evaluator.py        # Backward-compat shim
│   └── goals/
│       ├── base.py              # GoalScorer ABC, GoalEvaluator, registry
│       ├── scorers.py           # 9 built-in goal scorers
│       └── registry.py          # register_all_goals()
├── systems/
│   ├── rng.py                   # DeterministicRNG (domain-separated hashing)
│   └── generator.py             # EntityGenerator (spawn, spawn_race)
├── utils/
│   └── event_log.py             # Unbounded EventLog
└── api/
    ├── app.py                   # FastAPI app factory (OpenAPI tags, CORS)
    ├── engine_manager.py        # World builder + background thread manager
    ├── schemas.py               # Pydantic response models (state endpoints)
    └── routes/
        ├── __init__.py          # Router registration (api_router)
        ├── state.py             # GET /state, /stats
        ├── map.py               # GET /map
        ├── control.py           # POST /control/{action}, /speed
        ├── config.py            # GET /config
        └── metadata.py          # GET /metadata/* (8 endpoints, uses core schemas)

frontend/
├── src/
│   ├── App.tsx                  # Root layout + page toggle (Simulation | API Docs)
│   ├── main.tsx                 # Entry point (wraps App with MetadataProvider)
│   ├── types/
│   │   ├── api.ts               # Simulation state types
│   │   └── metadata.ts          # Metadata types (mirrors core pydantic schemas)
│   ├── contexts/
│   │   └── MetadataContext.tsx   # MetadataProvider + useMetadata() hook
│   ├── constants/
│   │   └── colors.ts            # Visual-only: colors, icons, cell size
│   ├── hooks/
│   │   ├── useSimulation.ts     # API polling + state management
│   │   └── useCanvas.ts         # Canvas rendering
│   └── components/
│       ├── Header.tsx           # Status bar + Simulation/API Docs nav toggle
│       ├── ApiDocsPage.tsx      # Interactive API docs (OpenAPI explorer + Try It)
│       ├── GameCanvas.tsx       # 3-layer canvas + minimap
│       ├── Sidebar.tsx          # Tab container
│       ├── ControlPanel.tsx     # Simulation controls
│       ├── InspectPanel.tsx     # Entity inspector (6 tabs, uses useMetadata)
│       ├── BuildingPanel.tsx    # Building info (uses useMetadata)
│       ├── ClassHallPanel.tsx   # Class browser (uses useMetadata)
│       ├── LootPanel.tsx        # Ground item detail (uses useMetadata)
│       ├── EventLog.tsx         # Event history with clear button
│       ├── EntityList.tsx       # Sorted entity list
│       └── Legend.tsx           # Tile/entity color legend
└── ...
```
