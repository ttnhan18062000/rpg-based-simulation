# System Rules (RPG Simulation Project)

## 0. Core Mission

This is a **realistic, extensible, and data-driven RPG simulation engine** inspired by rich RPG games, fantasy novels, and simulation-heavy systems.

All implementations must prioritize:

* Realism (logical causality, believable mechanics)
* Extensibility (future features plug in cleanly)
* Flexibility (config-driven, minimal hardcoding)
* Long-term maintainability

Short-term hacks are forbidden.

> Agent-facing workflow rules (escalation, output format) are in [`agent_rules.md`](agent_rules.md).

---

# 1️⃣ Engine Invariants (Non-Negotiable)

These invariants must **never** be broken. Any change that violates them is a regression regardless of feature value.

## 1.1 Determinism

The engine is fully deterministic: same `SimulationConfig` + same `world_seed` → identical world state at every tick.

* All randomness flows through `DeterministicRNG` with **domain-separated** xxhash streams (`Domain.COMBAT`, `Domain.SPAWN`, etc.)
* No use of `random`, `time.time()`, or any non-deterministic source in simulation logic
* Thread scheduling must not affect outcome — all proposals are collected then sorted deterministically
* **Verified by:** `tests/test_deterministic_replay.py` (runs N ticks twice, compares SHA-256 fingerprint at every tick)
* Any PR that breaks this test is rejected

## 1.2 Single-Writer Concurrency

Only the `WorldLoop` thread may mutate `WorldState`. All other threads read from immutable `Snapshot` objects.

* `Snapshot.from_world()` deep-copies entities and wraps in `MappingProxyType`
* Worker threads receive `Snapshot` + produce `ActionProposal` (frozen dataclass) via the MPSC `ActionQueue`
* API handlers read the latest snapshot via `EngineManager.get_snapshot()` (atomic reference swap under lock)
* **Never** pass a mutable `WorldState` reference to worker threads or API handlers

## 1.3 Shared Schema — Single Source of Truth

Core data models are **pydantic dataclasses** used by both the engine and the API:

* `ItemTemplate`, `SkillDef`, `ClassDef`, `BreakthroughDef`, `TraitDef` — `pydantic_dataclass(frozen=True)`
* The API uses `TypeAdapter(CoreModel).dump_python(instance, mode="json")` — no duplicate Pydantic schemas
* Mutable runtime types (`Entity`, `SkillInstance`, `TreasureChest`, `Building`) stay as stdlib `@dataclass`
* IntEnum fields serialize to lowercase strings via `Annotated[Enum, PlainSerializer(...)]`
* **Never** create a parallel Pydantic `BaseModel` that duplicates fields from a core dataclass

---

# 2️⃣ Testing Rules (Mandatory)

Every feature or bugfix must include:

### 2.1 Unit Tests

* Cover:

  * Happy path
  * Edge cases
  * Invalid input
  * State transitions
* Tests must be reusable and structured for future expansion
* Write test files in `tests/` and run with `pytest` — no inline `python -c` commands

### 2.2 Regression Safety

If modifying existing logic:

* Update existing tests
* Add new test to prevent regression
* **Determinism test must still pass** (`make test` or `pytest tests/test_deterministic_replay.py`)

### 2.3 Simulation Integrity Tests

For core mechanics:

* Add scenario-based tests (mini-simulation cases)
* Examples:

  * Combat outcome consistency (`test_combat.py`)
  * Conflict resolution determinism (`test_conflict_resolver.py`)
  * Goal evaluation edge cases (`test_inventory_goals.py`)
  * Deterministic replay across N ticks (`test_deterministic_replay.py`)

### 2.4 Running Tests

| Command | Purpose |
|---------|---------|
| `make test` | All tests |
| `make test-quick` | Fast tests only (skip `@pytest.mark.slow`) |
| `make test-cov` | Tests with coverage report |

No feature is "done" without tests.

---

# 3️⃣ Documentation Rules

After implementation:

You MUST:

* Update relevant files in `docs/`
* If none exist → create one
* Add:

  * Purpose
  * Data model explanation
  * Extension points
  * Known limitations
  * Future scalability notes
* Update `tickets/todos/ticket_metadata.md` if the change creates, completes, or modifies a ticket

Documentation must reflect the **why**, not just the what.

---

# 4️⃣ Architecture Principles

## 4.1 Design Philosophy

The system must follow:

* OOP for behavior modeling (ABC-based state handlers, goal scorers, damage calculators)
* Data-oriented design for performance-heavy components (spatial hash, tick loop)
* SOLID principles
* Clear separation of:

  * Simulation logic (`src/engine/`, `src/actions/`)
  * Data models (`src/core/`)
  * AI/decision logic (`src/ai/`)
  * API layer (`src/api/`)

Avoid:

* God classes
* Hidden side effects
* Cross-layer coupling (e.g., API code importing engine internals directly)

## 4.2 Tick-Based Architecture

The engine uses a **synchronous tick-based loop**, not an event-driven architecture.

* Every tick: Schedule → Collect → Resolve → Cleanup (4-phase cycle)
* All entities act simultaneously per tick (turn-based, not real-time)
* One `ActionProposal` per entity per tick
* Conflict resolution is deterministic: sort by `(action_type, next_act_at, entity_id)`
* State changes are **traceable and loggable** — every applied action is recorded in the event log
* Replayability is achieved through deterministic RNG + action recording, not event sourcing

> The term "event-driven" in this project refers to the **event log** (recording what happened), not to an event-sourced architecture pattern.

## 4.3 Realism Rule

Every mechanic must answer:

* What causes this?
* What limits this?
* What counters this?
* What are the edge cases?

**Current state:** The damage system uses a strategy pattern (`PhysicalDamageCalculator`, `MagicalDamageCalculator`) with ATK/DEF, crit, variance, and attribute scaling. This is intentionally simpler than a full RPG for now.

**Future goals** (not current requirements):

* Fatigue / stamina impact on combat
* Positional advantage (flanking, elevation)
* Morale effects
* Environmental modifiers (terrain, weather)
* Lasting injuries

If a mechanic is simplistic, justify it with a comment or doc note.

## 4.4 Extensibility Rule

No hardcoded constants if they can evolve.

Use:

* Config-driven systems (`SimulationConfig` frozen dataclass)
* Registries (`ITEM_REGISTRY`, `GOAL_REGISTRY`, `SKILL_DEFS`, `CLASS_DEFS`, `TRAIT_DEFS`)
* Strategy patterns (`DamageCalculator` subclasses, `StateHandler` dict)
* Component-based systems when appropriate

Every system should allow:

* Adding new weapon types → add to `ITEM_REGISTRY`
* Adding new status effects → add `EffectType` enum + handler
* Adding new terrain types → add `Material` enum + grid logic
* Adding new AI behaviors → add `GoalScorer` subclass + register

Without rewriting core engine.

---

# 5️⃣ Data Design Rules

* Prefer explicit schemas over loose dictionaries
* Use typed models (dataclasses with type hints)
* Avoid magic strings — use `IntEnum` for categories, typed IDs for references
* IDs over object references (`actor_id: int`, not `actor: Entity`)
* State transitions must be traceable and loggable
* All changes should be replayable (future-proofing for story generation)

---

# 6️⃣ Performance Awareness

This is a simulation-heavy system.

Every new feature must consider:

* Time complexity (avoid O(n²) per tick where possible — use `SpatialHash` for proximity)
* Memory growth (event log, snapshot copies, entity accumulation)
* Impact on entity scaling (test with `make profile --entities 50`)
* Batch update potential (process all entities in one pass, not individual queries)

If feature impacts performance significantly:
➡ Propose optimization options before implementing.

### Profiling Commands

| Command | Purpose |
|---------|---------|
| `make profile` | 500-tick timing report |
| `make profile-full` | 2000-tick + cProfile `.prof` dump |
| `make profile-memory` | tracemalloc memory snapshot |

Per-tick phase timing is built into `WorldLoop._step()` at DEBUG log level.

---

# 7️⃣ Tech Stack Rules

### Current Stack

| Layer | Technology |
|-------|-----------|
| Engine | Python 3.11+ (stdlib `dataclass` + `pydantic.dataclasses`) |
| RNG | `xxhash` (domain-separated deterministic) |
| API | FastAPI + Uvicorn |
| Frontend | React + TypeScript + Vite + TailwindCSS |
| Data | In-memory (no database) |

### Evolution Rules

You may:

* Upgrade library versions
* Introduce better patterns
* Improve performance tools

But you may NOT:

* Replace the tick-based engine architecture
* Replace FastAPI or React
* Introduce a database without explicit approval

All changes must include:

* Migration notes
* Compatibility notes

---

# 8️⃣ Bug Fixing Rule

When fixing a bug:

1. Reproduce it (or write a test that demonstrates the bug)
2. Write a failing test
3. Fix it minimally — prefer upstream root-cause fix over downstream workaround
4. Verify test passes
5. Verify `make test` still passes (especially determinism)
6. Document root cause

No blind fixes. No over-engineering — use single-line changes when sufficient.

---

# 9️⃣ Code Quality Requirements

* Clear naming
* No dead code
* No commented-out logic
* Explicit types (type hints on all function signatures)
* No hidden side effects
* Small, composable classes
* Prefer composition over inheritance (unless inheritance is semantically correct — e.g., `GoalScorer` ABC hierarchy is fine)
* Do not add or remove comments/docstrings unless the change is about documentation

---

# 🔟 Simulation Consistency Rule

The world must feel alive and logically consistent.

### Current invariants:

* Characters move 1 tile per tick (modified by SPD and terrain)
* Combat requires adjacency (Manhattan distance ≤ 1)
* Death occurs when HP ≤ 0 — heroes respawn after `hero_respawn_ticks`, mobs are removed
* Town is a safe zone — hostile entities take aura damage per tick
* Camps are home territory for goblins — guards heal there
* Loot drops on the ground at death position

### Aspirational goals (not yet implemented):

* Death should require significant effort, not stat difference only
* Injuries should have lasting impact unless healed
* Information should not spread instantly without a mechanism
* Characters should not teleport unless magic exists

Every mechanic must integrate with the simulation ecosystem.
