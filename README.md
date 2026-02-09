# Deterministic Concurrent RPG Engine

A high-fidelity 2D RPG simulation engine with parallel AI, deterministic replay, conflict resolution, and a real-time web visualization.

## Architecture

```
src/
├── __main__.py              # Entry point — serve (default) or cli mode
├── config.py                # SimulationConfig dataclass
├── api/                     # FastAPI web server layer
│   ├── app.py               #   App factory (lifespan, CORS, serves frontend/dist/)
│   ├── engine_manager.py    #   Background thread wrapper (atomic snapshot swap)
│   ├── dependencies.py      #   FastAPI dependency injection
│   ├── schemas.py           #   Pydantic response models
│   └── routes/              #   Versioned REST endpoints
│       ├── map.py            #     GET /api/v1/map
│       ├── state.py          #     GET /api/v1/state, /stats
│       ├── control.py        #     POST /api/v1/control/{action}, /speed
│       └── config.py         #     GET /api/v1/config
├── core/                    # Data models & world representation
│   ├── enums.py             #   ActionType, AIState, Direction, Domain, Material
│   ├── models.py            #   Vector2, Stats, Entity (with faction + effects)
│   ├── faction.py           #   Faction, FactionRelation, FactionRegistry, TerritoryInfo
│   ├── effects.py           #   StatusEffect, EffectType, factory helpers
│   ├── buildings.py         #   Building model, shop/recipe/guild config, economy helpers
│   ├── items.py             #   ItemTemplate, Inventory, ITEM_REGISTRY, LOOT_TABLES
│   ├── grid.py              #   Tile-based map
│   ├── world_state.py       #   Mutable authoritative state
│   └── snapshot.py          #   Immutable read-only view for workers
├── engine/                  # Tick engine & concurrency
│   ├── world_loop.py        #   4-phase tick cycle (Schedule → Collect → Resolve → Cleanup)
│   ├── action_queue.py      #   Thread-safe MPSC queue
│   ├── worker_pool.py       #   ThreadPoolExecutor for AI
│   └── conflict_resolver.py #   Deterministic conflict arbitration
├── actions/                 # Action proposals & handlers
│   ├── base.py              #   ActionProposal dataclass
│   ├── move.py              #   MoveAction (validate + apply)
│   ├── rest.py              #   RestAction
│   └── combat.py            #   CombatAction with deterministic damage rolls
├── ai/                      # Intelligence layer
│   ├── brain.py             #   AIBrain dispatcher (faction-aware, class-based)
│   ├── perception.py        #   Vision & memory utilities (faction-aware)
│   └── states.py            #   Class-based StateHandler registry + AIContext
├── systems/                 # Engine systems
│   ├── rng.py               #   Domain-separated deterministic RNG (xxhash)
│   ├── spatial_hash.py      #   O(1) spatial neighbor lookups
│   └── generator.py         #   Entity spawner
└── utils/
    ├── logging.py           #   Structured logging setup
    ├── event_log.py         #   Thread-safe ring buffer for API events
    └── replay.py            #   JSON replay recorder

frontend/                    # React + Vite + TypeScript SPA
├── vite.config.ts           #   Build config + API proxy
├── src/
│   ├── App.tsx              #   Root layout (Header + Canvas + Sidebar)
│   ├── hooks/               #   useSimulation (polling), useCanvas (rendering)
│   ├── components/          #   Header, GameCanvas, Sidebar, InspectPanel, BuildingPanel, ...
│   ├── types/               #   TypeScript interfaces for API schemas
│   └── constants/           #   Colors, item display names, item stats
└── dist/                    #   Production build output (gitignored)
```

## Key Design Principles

- **Single-Writer / Multi-Reader** — Only the WorldLoop mutates state; AI workers and the API read immutable snapshots.
- **Absolute Determinism** — All randomness via `Hash(WorldSeed, Domain, EntityID, Tick)` using xxhash.
- **Intent vs. Effect** — Workers produce proposals; the world validates and applies them.
- **Atomic Ticks** — All actions for tick N resolve before tick N+1 begins.
- **Atomic Snapshot Swap** — The API layer reads from an atomically-swapped immutable snapshot; the engine thread is never blocked by HTTP requests.

## Quick Start

All commands use `make` (runs `Makefile` on Linux/macOS, `make.bat` on Windows).

```bash
make install         # Install all dependencies (Python + Node)
make serve           # Build frontend + start production server at :8000
```

Open `http://127.0.0.1:8000` in your browser.

```bash
make cli             # Run headless simulation (200 ticks)
```

## Modes

### Server Mode (default)

Starts a FastAPI server and serves the production frontend build at `http://127.0.0.1:8000`.

```bash
python -m src serve --host 127.0.0.1 --port 8000 --seed 42 --entities 10
```

| Flag          | Default     | Description                 |
|---------------|-------------|-----------------------------|
| `--host`      | 127.0.0.1   | Server bind address         |
| `--port`      | 8000        | Server port                 |
| `--seed`      | 42          | World seed for determinism  |
| `--entities`  | 10          | Initial entity count        |
| `--workers`   | 4           | AI worker threads           |
| `--log-level` | INFO        | DEBUG, INFO, or WARNING     |

### CLI Mode

Runs the simulation headless and writes a JSON replay file.

```bash
python -m src cli --seed 42 --ticks 500 --entities 15 --log-level DEBUG
```

| Flag          | Default     | Description                 |
|---------------|-------------|-----------------------------|
| `--seed`      | 42          | World seed for determinism  |
| `--ticks`     | 200         | Maximum simulation ticks    |
| `--entities`  | 10          | Initial entity count        |
| `--workers`   | 4           | AI worker threads           |
| `--replay`    | replay.json | Replay output file          |
| `--log-level` | INFO        | DEBUG, INFO, or WARNING     |

## Visualization

The frontend is a **React 19 + TypeScript** SPA built with **Vite** and **Tailwind CSS v4**, using HTML5 Canvas for rendering.

- **Triple-layer canvas** — Layer 1 (grid, drawn once) + Layer 2 (entities + ground loot, redrawn every 80ms) + Layer 3 (fog-of-war overlay)
- **Hero** rendered as a **diamond** with golden glow; goblins as circles; **loot bags** as green diamonds
- **Click-to-inspect** — click any entity on the canvas or sidebar to open the Inspect Panel showing full stats, equipment (with item hover tooltips), goals, and memory
- **Hover tooltips** — hovering over entities or loot on the canvas shows a floating name tooltip
- **Spectate vision** — selecting an entity shows only what it can see; entities outside its vision are hidden, with ghost markers for remembered-but-not-visible entities
- **Fog of war** — selecting an entity shows its vision range, explored tiles, and filtered ghost markers
- **AI state ring** — each entity has a colored ring indicating its state (green=wander, yellow=hunt, red=combat, purple=flee, coral=alert)
- **Faction markers** — entities display faction symbols (e.g., HERO_GUILD, GOBLIN_HORDE)
- **Sidebar** — context-dependent tabs: Info+Events (default), Inspect (spectating entity with entity events sub-section), BuildingPanel (clicked building), LootPanel (clicked loot)
- **Buildings on map** — colored square markers with letters (S=Store, B=Blacksmith, G=Guild); also shown on minimap

### Frontend Development

```bash
make dev             # Start backend (:8000) + Vite dev server (:5173) with hot reload
make dev-backend     # Start only the backend
make dev-frontend    # Start only the frontend dev server
make build           # Build frontend for production
make lint            # Run frontend linters
make typecheck       # Run TypeScript type checking
make clean           # Remove build artifacts
```

Run `make help` to see all available commands.

## Town Buildings & Economy

Three buildings are placed in the town at world generation:

| Building | Purpose |
|----------|---------|
| **General Store** | Heroes sell unused gear and buy potions/upgrades |
| **Blacksmith** | Heroes learn 7 crafting recipes and craft powerful items from gold + materials |
| **Adventurer's Guild** | Provides intel on goblin camp locations and crafting material sources |

**Crafting materials** (Wood, Leather, Iron Ore, Steel Bar, Enchanted Dust) drop from enemies and are used in blacksmith recipes. Heroes autonomously manage their economy: selling loot, buying upgrades, gathering materials, and crafting gear — all driven by AI state handlers (`VISIT_SHOP`, `VISIT_BLACKSMITH`, `VISIT_GUILD`).

See **[docs/buildings_economy.md](docs/buildings_economy.md)** for full details.

## Faction System

Every entity belongs to a **Faction** (`HERO_GUILD`, `GOBLIN_HORDE`). Faction relationships (`HOSTILE`, `NEUTRAL`, `ALLIED`) are stored in a data-driven `FactionRegistry`.

- **Territory intrusion** — entities can enter any tile, but stepping on hostile territory applies stat debuffs (ATK/DEF/SPD) and alerts nearby defenders
- **Town aura** — hostile entities in town take gradual HP damage each tick, preventing spawn camping; enemies retreat when HP gets low
- **Passive town heal** — heroes in town regen HP passively (blocked when adjacent hostile is fighting them)
- **ALERT state** — defenders switch to ALERT when an intruder is detected, hunting them down before returning to guard duty
- **Status effects** — generic buff/debuff system with duration; territory debuffs are automatically applied via `Entity.effective_*()` methods
- **Extensible** — add new factions by extending the `Faction` enum and registering relationships; zero AI or combat code changes needed

See **[docs/faction_system.md](docs/faction_system.md)** for full details.

## Entity Types

| Kind | Faction | Base HP | Base ATK | Base SPD | Notes |
|------|---------|---------|----------|----------|-------|
| `hero` | HERO_GUILD | 40–55 | 8–12 | 10–13 | Spawned once at init; diamond shape, golden glow |
| `goblin` | GOBLIN_HORDE | 15–25 | 3–7 | 8–12 | Spawned at init + periodically by generator |
| `goblin_scout` | GOBLIN_HORDE | Tier-scaled | Tier-scaled | Tier-scaled | Generator spawns |
| `goblin_warrior` | GOBLIN_HORDE | Tier-scaled | Tier-scaled | Tier-scaled | Camp guards |
| `goblin_chief` | GOBLIN_HORDE | Tier-scaled | Tier-scaled | Tier-scaled | Camp leaders (elite) |
| `wolf` / `dire_wolf` / `alpha_wolf` | WOLF_PACK | Race-scaled | Race-scaled | Fast (+2) | Forest regions |
| `bandit` / `bandit_archer` / `bandit_chief` | BANDIT_CLAN | Race-scaled | Race-scaled | Agile (+1) | Desert regions |
| `skeleton` / `zombie` / `lich` | UNDEAD | Tanky (1.3×) | Low (0.8×) | Slow (-2) | Swamp regions |
| `orc` / `orc_warrior` / `orc_warlord` | ORC_TRIBE | Beefy (1.2×) | Strong (1.2×) | Slow (-1) | Mountain regions |

## REST API

All endpoints are under `/api/v1/`.

| Method | Endpoint                  | Description                                      |
|--------|---------------------------|--------------------------------------------------|
| GET    | `/api/v1/map`             | Static grid data (fetch once)                    |
| GET    | `/api/v1/state`           | Entities + events (polled by UI, supports `?since_tick=N`) |
| GET    | `/api/v1/stats`           | Tick counter, alive/spawned/death counts, status |
| GET    | `/api/v1/config`          | Current simulation configuration                 |
| POST   | `/api/v1/control/{action}`| Lifecycle: `start`, `pause`, `resume`, `step`, `reset` |
| POST   | `/api/v1/speed?tps=N`    | Set simulation speed (ticks per second)          |

## Documentation

- **[docs/architecture.md](docs/architecture.md)** — Technical architecture (concurrency model, tick cycle, API layer, frontend)
- **[docs/frontend.md](docs/frontend.md)** — Frontend tech stack, component tree, hooks, canvas rendering
- **[docs/api_reference.md](docs/api_reference.md)** — REST API endpoints and schemas
- **[docs/faction_system.md](docs/faction_system.md)** — Faction system, territory intrusion, status effects
- **[docs/buildings_economy.md](docs/buildings_economy.md)** — Town buildings, shop, blacksmith, guild, crafting system
- **[docs/terrains_resources.md](docs/terrains_resources.md)** — Terrain regions, resource nodes, new mob races, harvesting
- **[docs/visual_proposal.md](docs/visual_proposal.md)** — Original API + visualization proposal

## Requirements

### Backend
- Python ≥ 3.11
- xxhash ≥ 3.4.0
- fastapi ≥ 0.115.0
- uvicorn ≥ 0.30.0
- pydantic ≥ 2.0.0

### Frontend
- Node.js ≥ 18
- npm ≥ 9