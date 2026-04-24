# Deterministic Concurrent RPG Engine

A high-fidelity 2D RPG simulation engine with parallel AI, deterministic replay, conflict resolution, and a real-time web visualization.

## Architecture

> [!NOTE]
> **Architectural Convergence Complete**: The engine has successfully migrated to a **Feature-Based Aspect-Oriented Architecture** (AOA). This design uses composition (Aspects) for entities and domain-separated modules for simulation logic.

> [!IMPORTANT]
> **Operational Cutover Complete**: The engine has successfully transitioned to the **src_v2** authoritative runtime as of Phase 12. The legacy `src` logic is officially deprecated and slated for retirement in Phase 13. See the [Phase 12 Entry Package](docs/engine/phase12_entry_package.md) and the [Phase 13 Retirement Manifest](docs/engine/phase13_retirement_manifest.md) for details.

```
src_v2/
├── __main__.py              # Entry point — serve (default) or cli mode
├── cli/                     # CLI entrypoint and argument parsing
├── config/                  # Configuration loaders and validators
├── api/                     # FastAPI web server and WebSocket layer
│   ├── server.py            #   FastAPI app factory
│   ├── engine_manager.py    #   V2 Engine lifecycle management
│   └── ws/                  #   High-performance Binary WebSocket (BWS)
├── core/                    # Authoritative state and domain models
│   ├── state.py             #   The singular source of truth
│   ├── strategic.py         #   Strategic cognition models
│   └── worker_protocol.py   #   Worker intent/result contracts
├── engine/                  # The Simulation Kernel
│   ├── kernel.py            #   The 8-phase deterministic tick executor
│   ├── worker_manager.py    #   Parallel worker orchestration
│   └── replay_manager.py    #   Chunked, resource-safe replay system
├── systems/                 # Pure domain systems (No side effects)
│   ├── movement.py          #   Legality and redirection
│   ├── combat.py            #   Deterministic combat resolution
│   └── strategic.py         #   Strategic project evaluation
├── platform/                # Hardware and OS abstractions
│   ├── rng.py               #   Domain-separated xxhash RNG
│   └── clock.py             #   Monotonic tick timing
├── logging/                 # Structured, contextual logging
└── certification/           # Forensic verification and parity harness

frontend/                    # React + Vite + TypeScript SPA
├── vite.config.ts           #   Build config + API proxy
├── src/
│   ├── App.tsx              #   Root layout (Header + Canvas/ApiDocs + Sidebar)
│   ├── hooks/               #   useSimulation (polling), useCanvas (rendering)
│   ├── contexts/            #   MetadataContext (fetches + caches all metadata)
│   ├── components/
│   │   ├── ApiDocsPage.tsx  #   Interactive API documentation (OpenAPI explorer)
│   │   ├── InspectPanel.tsx #   Entity inspector (uses metadata)
│   │   ├── ClassHallPanel.tsx # Class browser (uses metadata)
│   │   ├── BuildingPanel.tsx#   Building details (uses metadata)
│   │   └── ...              #   Header, GameCanvas, Sidebar, LootPanel, etc.
│   ├── types/
│   │   ├── api.ts           #   Simulation state types
│   │   └── metadata.ts      #   Metadata response types (mirrors core schemas)
│   └── constants/           #   Visual-only: colors, icons, cell size
└── dist/                    #   Production build output (gitignored)

## Key Design Principles

- **Single-Writer / Multi-Reader** — Only the WorldLoop mutates state; AI workers and the API read immutable snapshots.
- **Absolute Determinism** — All randomness via `Hash(WorldSeed, Domain, EntityID, Tick)` using xxhash.
- **Intent vs. Effect** — Workers produce proposals; the world validates and applies them.
- **Emotional Intelligence** — Entities track persistent grudges (Nemesis system), emotional mood, and locational trauma (memory biasing).
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

Starts the FastAPI server with the V2 engine backend.

```bash
python3 -m src serve --host 127.0.0.1 --port 8000 --seed 42 --entities 10
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

Runs the simulation headless and writes a chunked replay directory.

```bash
python3 -m src cli --seed 42 --ticks 1000 --entities 50 --log-level INFO
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
- **Tile tooltips** — hovering any tile shows all info: terrain type, entities (with stats), buildings, loot, resources, ghost markers — fog-gated when spectating
- **Spectate vision** — selecting an entity shows only what it can see; entities outside its vision are hidden, with ghost markers for remembered-but-not-visible entities
- **Three-level fog of war** — visible (clear), explored (50% dimmed), unseen (completely dark) — on both main canvas and minimap
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

Every entity belongs to one of **10 Factions** (HERO_GUILD, GOBLIN_HORDE, WOLF_PACK, BANDIT_CLAN, UNDEAD, ORC_TRIBE, CENTAUR_HERD, FROST_KIN, LIZARDFOLK, DEMON_HORDE). Faction relationships (`HOSTILE`, `NEUTRAL`, `ALLIED`) are stored in a data-driven `FactionRegistry`.

- **Territory intrusion** — entities can enter any tile, but stepping on hostile territory applies stat debuffs (ATK/DEF/SPD) and alerts nearby defenders
- **Town aura** — hostile entities in town take gradual HP damage each tick, preventing spawn camping; enemies retreat when HP gets low
- **Passive town heal** — heroes in town regen HP passively (blocked when adjacent hostile is fighting them)
- **ALERT state** — defenders switch to ALERT when an intruder is detected, hunting them down before returning to guard duty
- **Status effects** — generic buff/debuff system with duration; territory debuffs are automatically applied via `Entity.stats.atk` etc.
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
| `centaur` / `centaur_warrior` / `centaur_chief` | CENTAUR_HERD | Race-scaled | Race-scaled | Fast (+2) | Grassland regions |
| `frost_wolf` / `frost_giant` / `frost_shaman` | FROST_KIN | Race-scaled | Race-scaled | Race-scaled | Snow regions |
| `lizard` / `lizard_warrior` / `lizard_chief` | LIZARDFOLK | Race-scaled | Race-scaled | Race-scaled | Jungle regions |
| `imp` / `hellhound` / `demon_lord` | DEMON_HORDE | Race-scaled | Race-scaled | Race-scaled | Volcanic regions |
| `gorath` / `vexira` / `morgul` | (Various) | Boss-scaled | Boss-scaled | Boss-scaled | **Calamity World Bosses** |

## REST API

All endpoints are under `/api/v1/`. Interactive documentation available via the **API Docs** page in the frontend header, or at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Simulation

| Method | Endpoint                  | Description                                      |
|--------|---------------------------|--------------------------------------------------|
| GET    | `/api/v1/map`             | Static grid data (fetch once)                    |
| GET    | `/api/v1/state`           | Entities + events (polled by UI, supports `?since_tick=N`) |
| GET    | `/api/v1/stats`           | Tick counter, alive/spawned/death counts, status |
| GET    | `/api/v1/config`          | Current simulation configuration                 |
| POST   | `/api/v1/control/{action}`| Lifecycle: `start`, `pause`, `resume`, `step`, `reset` |
| POST   | `/api/v1/speed?tps=N`    | Set simulation speed (ticks per second)          |

### Metadata (Game Definitions)

These endpoints serialize **core pydantic dataclasses** directly — the single source of truth used by both the game engine and the frontend.

| Method | Endpoint                       | Description                                      |
|--------|--------------------------------|--------------------------------------------------|
| GET    | `/api/v1/metadata/enums`       | Materials, AI states, tiers, rarities, factions, entity kinds |
| GET    | `/api/v1/metadata/items`       | All item templates (stats, bonuses, rarity, type) |
| GET    | `/api/v1/metadata/classes`     | Class defs, skills, breakthroughs, scaling, mastery tiers |
| GET    | `/api/v1/metadata/traits`      | All personality trait definitions                 |
| GET    | `/api/v1/metadata/attributes`  | 9 primary attribute definitions with descriptions |
| GET    | `/api/v1/metadata/buildings`   | Building type names and descriptions              |
| GET    | `/api/v1/metadata/resources`   | Resource node types per terrain                   |
| GET    | `/api/v1/metadata/recipes`     | Crafting recipes with materials and output         |
| GET    | `/api/v1/metadata/protocol`    | **[NEW]** BWS Protocol KeyMap & Enum indices        |

### High-Performance Binary Protocol (BWS)

For real-time frontend synchronization with high entity counts, use the **Binary WebSocket Protocol**:

- **Endpoint**: `ws://localhost:8000/api/v1/ws`
- **Protocol**: MessagePack over WebSockets with Positional Arrays.
- **Payload**: ~95% smaller than standard REST JSON.
- **Handshake**: Clients must send `{"type": "handshake", "format": "msgpack"}` upon connection.
- **Metadata**: Fetch the transposition rules from `/api/v1/metadata/protocol`.

### API Documentation

Three ways to explore the API:

- **In-app API Docs page** — click "API Docs" in the header for a custom interactive explorer with Try It Out
- **Swagger UI** — visit `/docs` for the standard OpenAPI interactive docs
- **ReDoc** — visit `/redoc` for a clean read-only reference

## Shared Schema Architecture

Core game definitions are **pydantic dataclasses** that serve as the single source of truth for both the engine and the API:

| Model | File | Purpose |
|-------|------|--------|
| `ItemTemplate` | `core/items.py` | All item properties — stats, rarity, type, effects |
| `SkillDef` | `core/classes.py` | Skill templates — cost, cooldown, power, modifiers |
| `ClassDef` | `core/classes.py` | Class templates — bonuses, scaling, breakthroughs |
| `BreakthroughDef` | `core/classes.py` | Class promotions — requirements and bonuses |
| `TraitDef` | `core/traits.py` | Personality traits — utility modifiers, stat multipliers |

Enum fields use `Annotated[EnumType, PlainSerializer(...)]` — **IntEnums at runtime** for fast game logic, **lowercase strings in JSON** for the API. No duplicate schemas.

See **[docs/design_patterns.md](docs/design_patterns.md)** §7 for full details.

## Observable AI & Strategic Cognition [NEW]

The engine now supports a sophisticated **Strategic Cognition Layer** (Phase 7) that provides entities with long-term memory and hierarchical reasoning. 

- **Mind Hierarchy**: Motives -> Projects -> Objectives. No more "tactical jitter".
- **Continuity**: AI characters remember their current mission even after combat interruptions.
- **Cognition Visualizer**: Interactive top-down mind-map visualization for auditing AI decisions.
- **Headless Regression**: 100% deterministic simulation verifier with artifact generation.

### Using the Cognition Visualizer
To inspect an entity's strategic mind:
1. Open `tools/viz_strategy.html` in any modern browser.
2. Drag and drop a `cognition_e[id].json` file from your `logs/` directory.
3. Explore the nodes (Directives, Projects, Objectives) and edges (pursuing, influenced by).

---

## Documentation Integrity & Milestone Records

The version 2 engine is protected by a **Documentation Integrity Suite** that enforces strict structural and semantic compliance across all technical contracts.

### Substrate Implementation Milestones (100% Complete)

The following milestones define the **Simulation Substrate** (Kernel, Scheduling, Persistence). These represent the 100% complete foundation, but do not imply 100% gameplay logic recovery.

- **[Milestone 1 — Simulation Kernel & Resource Envelope](resource_implementation_milestone_1.md)** — Sets the 8-phase deterministic tick law.
- **[Milestone 2 — Deterministic Tick Loop & Execution Phases](resource_implementation_milestone_2.md)** — Frozen 6-phase atomic resolution cycle.
- **[Milestone 3 — Bounded State Models & Retention Policy](resource_implementation_milestone_3.md)** — Authoritative vs local state separation.
- **[Milestone 4 — Deterministic Scheduling & Work Classes](resource_implementation_milestone_4.md)** — Readiness-driven work selection logic.
- **[Milestone 5 — Resource Governor & Degradation State Machine](resource_implementation_milestone_5.md)** — Adaptive load shedding.
- **[Milestone 6 — Streaming Replay & Bounded Persistence](resource_implementation_milestone_6.md)** — Bit-identical forensic recording.
- **[Milestone 7 — Observability & Operational Controls](resource_implementation_milestone_7.md)** — Structured reason taxonomy.
- **[Milestone 8 — Safe Concurrency & Bounded Worker Execution](resource_implementation_milestone_8.md)** — Parallel AI with single-writer safety.
- **[Milestone 9 — Resource Certification & Resilience Harness](resource_implementation_milestone_9.md)** — Envelope compliance proofs.
- **[Milestone 10 — Documentation Integrity & Project Maintenance](resource_implementation_milestone_10.md)** — Final project lawbook and maintenance cycle.

### Core Documentation

- **[Project Lawbook](docs/engine/project_lawbook_m10.md)** — The canonical summary of all engine laws.
- **[Engineering Playbook](docs/engine/engineering_playbook_m10.md)** — Guidelines for extending the engine safely.
- **[Architecture Guide](docs/architecture.md)** — High-level technical overview of the AOA design.

## Requirements

### Backend
- Python ≥ 3.11
- msgpack ≥ 1.0.0
- xxhash ≥ 3.4.0
- fastapi ≥ 0.115.0
- uvicorn ≥ 0.30.0
- pydantic ≥ 2.0.0

### Frontend
- Node.js ≥ 18
- npm ≥ 9

## Infrastructure & Troubleshooting

The simulation uses **Docker Compose** for a production-grade stack (Redis, RabbitMQ, Kafka, Zookeeper, Loki, Grafana).

### Centralized Logging

All service logs are aggregated into **Loki** and can be explored via **Grafana**:
- **Grafana URL**: `http://localhost:3000` (User: `admin`, Pass: `admin`)
- **Direct Command**: `docker compose logs -f` (to see all service logs in one stream)
- **Service Logs**: `docker compose logs -f [service_name]` (e.g. `sim_kafka`, `backend`)

### Troubleshooting Kafka Startup

If Kafka fails with an `InconsistentClusterIdException`, it is likely due to a mismatch between the persistent volumes and a new container recreation. To fix:

```bash
# Total Wipe (Removes all volumes for Redis, RabbitMQ, Kafka, etc.)
docker compose down -v
docker compose up -d --build
```