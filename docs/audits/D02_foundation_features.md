---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, foundation-features, codebase-health, feature-inventory]
---

# D02 — Foundation Feature Inventory

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | 0 — Feature Inventory |
| **State** | `done` |
| **Impact** | 5 / 5 |
| **Interest** | 4 / 5 |
| **Priority** | 9 |
| **Method** | code-read |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Which technical enabling capabilities exist, which are
partial, and which are missing — the substrate that RPG features run on top of. This is
not about gameplay systems (those are D01); it is about algorithms, mathematical systems,
data structures, design patterns, and infrastructure.

**Related dimensions:**
- D09 (System Wiring & Integration) — must verify every `[E]` feature here is actually
  called from the live pipeline. A feature can be unit-tested but never reach `kernel.py`.
- D10 (Test Coverage) — the `[P]` items here have the highest regression risk.
- D14 (Coupling Depth) — the domain architecture section needs hidden coupling analysis.
- D17 (Documentation Currency) — `known_limitations.md` was found stale during this audit.

---

## Rating Method

Three status labels per feature:

| Label | Meaning |
|---|---|
| `[E]` Existing | Implemented and verified in current source |
| `[P]` Partial | Implemented with confirmed gaps — source confirmed, gap identified |
| `[M]` Missing | Zero or near-zero code for this capability |

Scoring framework for individual feature depth: see `foundation_feature_framework.md`
(6 dimensions A–F, 1–10 each, 60 max). That framework is available for deeper analysis
within any feature but is not applied to every entry here — status labels are sufficient
for the inventory pass.

**Scope:** Technical enabling capabilities only. Not RPG features (combat, economy,
quests) — only the systems those features depend on to function.

### Foundation Risk Scoring — `[P]` and `[M]` items

`[P]` and `[M]` items are additionally scored by implementation risk. Five dimensions,
each 1–10. Maximum: 50. Higher score = higher priority to close the gap.

| Dimension | 1 | 5 | 10 |
|---|---|---|---|
| **Gap Severity** | Minor limitation, cosmetic only | Confirmed behavior gap | Active P0 parity bug or silent correctness failure |
| **Downstream Risk** | Self-contained within one module | Affects 2–3 systems in one domain | Cross-cutting — blocks or degrades multiple domains |
| **Test Shield** | Behavior fully tested at the boundary | Partial or fragile coverage | Regression-blind — no tests protect this behavior |
| **Runtime Impact** | Cosmetic or debug-only effect | Behavioral degradation, non-critical | Incorrect simulation state or silent non-determinism |
| **Recurrence Risk** | Rare edge case | Hit under realistic scenarios | Triggered on every production run |

### Group Health Scoring — per-section summary

Each major section (§1–§10) receives a group-level score on three dimensions. Maximum: 15.
Applied once per group rather than per individual feature. Higher score = higher priority
to address the section's remaining gaps.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Completeness Gap** | All items `[E]` — no gaps in this group | One `[P]` item with a confirmed minor gap | One or more `[M]` items, or two or more `[P]` items, or any `[P]` carrying an active P0 parity defect |
| **Impact if Gaps Persist** | Gaps are cosmetic, debug-only, or rare edge cases | Gaps affect production scenarios or cause behavioral skew | Gaps cause silent correctness failures, P0 parity bugs, or block dependent feature work |
| **Test Shield** | All gaps regression-protected by tests at the boundary | Partial or fragile coverage; some gap behaviors lack regression tests | Regression-blind — one or more gaps could silently break on refactor with no failing test |

---

## 1. Kernel & Execution

**Group Score: 3 / 15** — All 9 items `[E]`; no gaps (updated 2026-06-26: 1.8 and 1.9 resolved)

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 9 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 1.1 Deterministic Tick Loop `[E]`
**Source:** `src/engine/kernel.py` — `Kernel.tick_once()`, `_tick_once_inner()`

Single-threaded deterministic entry point. Phase costs tracked per-tick.
`_guard_stability()` detects isolation breaches (state mutation during non-resolution
phases).

---

### 1.2 6-Phase Kernel Ordering `[E]`
**Source:** `src/engine/phases.py` — `TickPhase`, `get_authoritative_phases()`

Fixed sequence: Init → Scheduling → Collection → Resolution → Cleanup → Advancement →
Persistence. Order is not configurable at runtime — it is a law.

---

### 1.3 Phase Dependency Graph `[E]`
**Source:** `src/engine/phase_graph.py` — `PhaseDependencyGraph`, `PhaseMetadata`

Feature-flag-aware phase enabling. `should_run_phase()` consults graph and active
feature flags. Prevents orphaned phase execution when a dependency domain is disabled.

**Note:** Per-phase declared read/write domain permissions enforced via item 1.9 (`src/engine/phase_domain_permissions.py`).

---

### 1.4 Deterministic Scheduler `[E]`
**Source:** `src/engine/scheduler.py` — `DeterministicScheduler`, `PeriodicDefinition`

Selects work for each tick across CRITICAL / PERIODIC / DEFERRED work classes.
Deterministic ordering guaranteed — same tick always produces same work selection.

---

### 1.5 Cadence Gating `[E]`
**Source:** `src/engine/cadence.py` — `SystemCadence`, `should_run()`

Per-system, per-entity cadence control. `should_run(tick, entity_id, cadence)` gates
subsystem execution without scheduler overhead.

---

### 1.6 Level of Detail (LOD) System `[E]`
**Source:** `src/engine/lod.py` — `LODService`

Distance-based execution skipping. `determine_lod()` and `should_execute()` concentrate
computation near active areas.

---

### 1.7 Governance / Eligibility Gating `[E]`
**Source:** `src/engine/governor.py`, `src/engine/phase_governor.py`, `src/core/governance.py`

Policy-based per-entity eligibility checks before scheduling. Prevents invalid or dead
entities from consuming pipeline budget.

---

### 1.8 Worker / Concurrency Model `[E]`
**Source:** `src/engine/worker_manager.py`, `src/engine/worker_logic.py`,
`src/core/worker_protocol.py`, `src/core/concurrency_law.py`

Thread and worker execution modes alongside sequential.

**Status (updated 2026-06-26):** Resolved by TCK-20260513-PERF-WORKER-HARDENING. 100% deterministic parity certified for thread/worker modes with sequential baseline (3.3× speedup). `test_worker_equivalence.py`, `test_dirty_parity.py`, `test_concurrency_parity.py` pass.

---

### 1.9 Per-Phase Read/Write Domain Permissions `[E]`
**Source:** `src/engine/phase_domain_permissions.py` — `PHASE_READ_DOMAINS`, `PHASE_WRITE_DOMAINS`

**Status (updated 2026-06-26):** Implemented (RPG-INFRA-155/156/157). Full `PHASE_READ_DOMAINS` and `PHASE_WRITE_DOMAINS` tables defined for all 7 tick phases, enforcing fine-grained per-phase domain boundaries alongside the coarse single-mutation-point law.

---

## 2. State Architecture

**Group Score: 3 / 15** — All 6 items `[E]`; no gaps.

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 6 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 2.1 Authoritative State Model `[E]`
**Source:** `src/core/state.py` — `AuthoritativeState`

Central frozen dataclass holding all durable simulation truth. Never directly mutated —
only replaced through the apply path.

---

### 2.2 Immutability Enforcement `[E]`
**Source:** `src/core/immutability.py` — `deep_freeze()`, `shallow_freeze()`

Runtime immutability guard. Converts mutable containers to read-only proxies.
Used at state boundaries to prevent accidental in-place mutation.

---

### 2.3 Deterministic RNG `[E]`
**Source:** `src/core/state.py` — `rng_checkpoint` field. `src/engine/checkpoint.py`.
`docs/engine/architecture.md` — Seed-Domain-Identity formula.

All randomness flows through a seeded `DeterministicRNG`. No authoritative logic may
use `time.time()`, `random.random()`, or other non-seeded sources. RNG state is
checkpointed in `AuthoritativeState.rng_checkpoint` for replay fidelity.

---

### 2.4 Canonical State Hashing `[E]`
**Source:** `src/engine/checkpoint.py` — `CanonicalStateHasher`, `BudgetedCanonicalHasher`,
`CanonicalHashScheduler`, `HashMode`

SHA-256 hash of canonical JSON representation of `AuthoritativeState`. Used for replay
verification and determinism certification.

---

### 2.5 Authoritative vs Non-Authoritative State Partitioning `[E]`
**Source:** `docs/core/state.md`, `src/core/state.py`

Hard rule: anything that survives beyond the current tick lives in `AuthoritativeState`.
Enforced by convention and architecture tests.

---

### 2.6 State Serialization `[E]`
**Source:** `src/core/serialization.py` — `StateSerializer`

`serialize()` / `deserialize()`. Used by replay manager and certification harness.

---

## 3. Mutation Architecture

**Group Score: 3 / 15** — All 7 items `[E]`; no gaps.

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 7 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 3.1 Typed Result Records Pattern `[E]`
**Source:** `src/core/updates.py` — `StateUpdate`, typed sub-update models.
`src/core/update_models/`

Domains never write state directly. They return typed `StateUpdate` records. The apply
path reads these and decides whether and how to commit them.

---

### 3.2 Authoritative Mutation Pipeline (Apply Path) `[E]`
**Source:** `src/engine/apply.py` — 17-phase refinement sequence.

The single authoritative path through which all durable state changes flow. All
conservation law enforcement, conflict resolution, and integrity checks run here.

---

### 3.3 State Update Compactor `[E]`
**Source:** `src/engine/compactor.py` — `StateUpdateCompactor`

Merges redundant fields in a `StateUpdate` before the apply path. Reduces dataclass
`replace()` calls and memory allocation pressure under high entity counts.

---

### 3.4 Dirty Entity Tracking `[E]`
**Source:** `src/core/dirty.py` — `DirtySet`, `DirtySetBuilder`, `DirtyDependencyGraph`,
`CandidateSelector`

Rich change-set propagation. `DirtyDependencyGraph.expand()` grows dirty sets to
transitively affected entities. `DirtySetLeakError` catches sets escaping their scope.

---

### 3.5 Conflict Resolution (Deterministic Priority Order) `[E]`
**Source:** `src/engine/kernel.py` — result sorting by `(class_priority, -local_priority, entity_id)`.

Contending updates resolved by deterministic ordering — identical resolution across
replays.

---

### 3.6 Phase Stability Guard `[E]`
**Source:** `src/engine/kernel.py` — `_guard_stability()`

Fingerprints `AuthoritativeState` at start/end of each non-Resolution phase. Raises
`IsolationBreach` if state changed. Primary runtime guard against illegal mutation.

---

### 3.7 Resource Conservation Law `[E]`
**Source:** `src/core/conservation.py` — `ResourceTransactionResolver`, `TransactionResult`

Atomic transaction model: no resource created or destroyed, only transferred.
All harvest, trade, crafting, and loot operations must go through this.

---

## 4. Spatial & Navigation

**Group Score: 3 / 15** — All 7 items `[E]`; no gaps (updated 2026-06-26: 4.3 and 4.7 resolved)

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 7 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 4.1 Spatial Grid / Cell-Based Indexing `[E]`
**Source:** `src/engine/spatial.py` — `SpatialGrid`

Fixed-size cells (`cell_size=5`). O(1) average neighbor lookup vs. O(N) linear scan.
Rebuilt each tick from current entity positions.

---

### 4.2 Spatial Query Service `[E]`
**Source:** `src/engine/spatial_query.py` — `SpatialQueryService`

High-level spatial queries: `nearest_resource_node()`, `nearest_building()`,
`nearby_entities()`, `get_region_at()`, `get_corpse_at()`, `get_ground_item_at()`.

**Gap:** `get_region_at()` uses a point-in-bounds rectangle check — no geospatial index
for large region counts. Acceptable at current world scale.

---

### 4.3 Flow Field Navigation `[E]`
**Source:** `src/systems/world_systems/navigation.py` — `FlowFieldService`, `NavigationSystem`

`get_next_step()` combines flow field with occupancy avoidance.

**Status (updated 2026-06-26):** Resolved. A* pathfinding added alongside flow field (`navigation.py:74` — "Decides between local A* and global Flow Field"). Local-minima risk addressed via hybrid routing.

---

### 4.4 Movement System `[E]`
**Source:** `src/engine/movement.py` — `MovementSystem.resolve_move()`

Applies a single movement step from flow field output. Validates against occupancy and
spatial constraints before producing a `StateUpdate`.

---

### 4.5 Movement Plan Cache `[E]`
**Source:** `src/engine/movement_cache.py` — `MovementPlanCache`, `MovementPlanKey`, `MovementPlan`

Caches next-step decisions keyed by `(entity_id, target_pos, occupancy_version)`.
`invalidate_for_dirty()` clears stale entries via dirty set. Implements `ICacheable`.

---

### 4.6 Occupancy Snapshot `[E]`
**Source:** `src/engine/occupancy_snapshot.py`

Point-in-time snapshot of which grid cells are occupied. Used by movement and legality.

---

### 4.7 Legality Checking `[E]`
**Source:** `src/engine/legality.py` — `LegalityServiceV2`

`get_manhattan_dist()`, `is_adjacent()`, `verify_occupancy()`, `get_region_for_position()`.

**Status (updated 2026-06-26):** Resolved by TCK-20260619-PARITY-P0-BUGS. Parity entry COMB-006 (`status: verified`) — AoE legality now correctly splits impact-center and radius legality checks.

---

## 5. Mathematical & Formula Systems

**Group Score: 3 / 15** — All 10 items `[E]`; no gaps (updated 2026-06-26: 5.4 and 5.10 resolved)

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 10 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 5.1 Combat Damage Formula `[E]`
**Source:** `src/engine/combat.py` — `CombatResolutionSystem.calculate_damage()`

`damage = (atk × atk_mult) × ((atk × atk_mult) / ((atk × atk_mult) + (def × def_mult) × 2.0 + 1.0))`

Diminishing-return damage curves. Supports single, multi-attack, AoE, opportunity,
skill usage variants.

---

### 5.2 Attribute Cap Enforcement `[E]`
**Source:** `src/engine/rpg_depth.py` — `enforce_attribute_caps()`

Clamps all entity attributes to defined min/max bounds after any modification.

---

### 5.3 Stamina System `[E]`
**Source:** `src/engine/rpg_depth.py` — `StaminaService`

Per-action drain rates (`drain_attack`, `drain_move`, `drain_harvest`, `drain_skill`).
Regen via `tick_regen()`. `get_exhaustion_multiplier()` returns performance penalty scalar.

---

### 5.4 Wound System `[E]`
**Source:** `src/engine/rpg_depth.py` — `WoundService`

`should_inflict_wound()`, `create_wound()`, `get_wound_stat_penalties()`,
`get_scar_stat_penalties()`.

**Status (updated 2026-06-26):** Resolved by TCK-20260619-PARITY-P0-BUGS. Parity entry COMB-290 (`status: verified`) — wound threshold confirmed in parity with the Mechanics Bible.

---

### 5.5 Tactical Decision Scoring `[E]`
**Source:** `src/engine/tactical.py` — `TacticalDecisionSystem`, `target_score()`

Composite tuple ordering `(priority, score, distance, id)` for deterministic
tie-breaking. `evaluate_entity_intent()` scores all candidate actions and targets.

---

### 5.6 Goal / Route Scoring Framework `[E]`
**Source:** `src/ai/goals/scorers.py`, `src/ai/goals/base.py`
`src/ai/score_modifiers.py`, `src/ai/personality.py`

Pluggable scoring: each route type has a dedicated `GoalScorer` subclass.
`ScoreModifierSystem.apply_modifiers()` applies OCEAN personality trait weights.

---

### 5.7 XP / Reward Classification Math `[E]`
**Source:** `src/engine/combat.py` — `CombatRewardClassificationService`
`src/engine/combat_rewards.py`

`xp_gain = evolution_level × xp_multiplier`. `gold_gain = evolution_level × gold_multiplier`.
`rebirth_eligible` flag triggers entity recycling vs permanent death.

---

### 5.8 Parameter Expression Evaluator `[E]`
**Source:** `src/worldmodules/evaluator.py` — `ModuleParameterEvaluator`

AST-safe arithmetic evaluator for world module parameter expressions. Prevents arbitrary
code execution while allowing flexible parameter authoring.

---

### 5.9 Module Scoring System `[E]`
**Source:** `src/worldgeneration/scorer.py` — `ModuleScorer`, `ModuleScore`

Scores world modules against a generation intent across 4 dimensions. Used by the
procedural composition generator.

---

### 5.10 Macro-Economy Health Metrics `[E]`
**Source:** `src/engine/gold_sink.py` — `GoldSinkSystem`; `src/observability/events.py` — `economy_health_monitor`; `src/api/routes/economy.py` — `get_economy_health()`

**Status (updated 2026-06-26):** Implemented. `GoldSinkSystem` tracks Gini index and gold drain. `economy_health_monitor` events emitted for aggregate monitoring. REST endpoint `GET /economy/health` exposes macro-economy health signals.

---

## 6. Entity & Content Modelling

**Group Score: 9 / 15** — 1 `[P]` (6.6 hardcoded content fallbacks)

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 2 | One `[P]` item with a moderate but non-critical gap |
| Impact if Gaps Persist | 4 | Silent wrong entity types in fallback mode; affects world assembly, entity spawning, and quest generation |
| Test Shield | 3 | `FallbackRestrictedError` tests have teardown errors observed in D10; coverage is fragile |

### 6.1 Entity Anatomy Model `[E]`
**Source:** `src/core/state.py` (EntityState), `docs/mechanics/01_entity_anatomy.md`

Core attributes (STR, DEX, INT, END, CHA), derived stats, biological pressures, XP
scaling, evolution level, identity, personality.

---

### 6.2 Entity Lifecycle Model `[E]`
**Source:** `src/systems/lifecycle_systems/lifecycle.py`, `src/core/lifecycle.py`
`src/systems/lifecycle_systems/biological.py`

Spawn → alive → dead → cleanup transitions. Biological pressures (hunger, stamina,
aging) processed each tick.

---

### 6.3 Entity Builder `[E]`
**Source:** `src/core/builder.py` — `EntityBuilder`

Fluent builder for assembling `EntityState` from class definitions, traits, and starting
inventory. Ensures all required fields are populated.

---

### 6.4 Typed Durable State Rule `[E]` (design pattern)
**Source:** `docs/core/state.md`, `CLAUDE.md` Architecture Rule.

Anything that survives beyond the current tick must have a typed model, stable location
in entity/world/registry state, a defined lifecycle, and tests. No durable meaning in
`reason` strings, free-form `metadata`, comments, or temporary variables.
Enforced by code review and architecture tests.

---

### 6.5 Content Catalog & Registry `[E]`
**Source:** `src/core/registries.py`, `src/content/repository.py`, `src/content/schema.py`,
`src/content/resolver.py`

Loads content families at startup. `ContentResolver` maps symbolic IDs to concrete
definitions. `ContentRepository` manages the loaded catalog at runtime.

---

### 6.6 Hardcoded Fallback Paths `[P]`

> **Ticket:** TCK-20260627-P2N-DEGRADED-FALLBACK

**Source:** `src/core/registries.py` — `runtime_content_source = "legacy_hardcoded"`
`src/core/modes.py` — `HardcodedFallbackForbiddenError`

Silent fallback to hardcoded seed maps when content catalog is missing or incomplete.

**Risk:** Silent in non-strict modes. Missing catalog entries become old hardcoded values
instead of validation errors. Content types with no fallback entry fail at runtime, not
at authoring time.

**Status (updated 2026-06-27):** Resolved by TCK-20260627-P2N-DEGRADED-FALLBACK.
Module-level default `runtime_content_source` changed from `"legacy_hardcoded"` to `None`
(`src/core/registries.py:541`).  `GracefulDegradationManager.resolve_content_source()` added
to `src/domains/optimization/degradation.py` — selects from catalog (lowest-cost via
`CatalogRepository.get_lowest_cost_for_type()`) in degraded mode; raises `CatalogMissError`
in strict mode when catalog is absent.  Full fallback retirement remains gated on
`docs/guidelines/fallback_retirement_criteria.md` (all 9 criteria MET; retirement proceeds
to TCK-20260610-FALLBACK-RESTRICT-MODES). Parity entry: INFRA-028.

---

### 6.7 Content Pack Manifest & Validation `[E]`
**Source:** `src/content/pack_manifest.py`, `src/content/validator.py`,
`src/content/matrix.py`, `src/content/reference_graph.py`, `src/content/warmup.py`

`ContentPackManifest` declares ID, version, dependencies, content families.
`ContentValidator` checks schema and referential integrity.
`ContentUsageMatrix` tracks content family maturity and consumers.
`reference_graph.py` detects circular content dependencies.

---

### 6.8 Content Family Extension Pattern `[E]` (design pattern)
**Source:** `docs/simulation/adventure_contract.md`, `docs/simulation/world_emergence_contract.md`

Canonical pattern: `enum → generator → scorer → mapper → tests`. Proven in adventure
routing and world emergence. All new content types must follow this shape.

---

### 6.9 Namespace Isolation for Content `[E]`
**Source:** `src/worldbuilding/schema.py`, `src/worldmodules/schema.py`

`namespace:id` format prevents collision between content packs and world modules.
Validated at assembly time.

---

### 6.10 World Module Schema & Repository `[E]`
**Source:** `src/worldmodules/schema.py` — `WorldModuleSpec`
`src/worldmodules/repository.py`, `src/worldmodules/normalizer.py`

Declarative schema for world capability modules. Repository loads and indexes all
modules by ID and tag. Normalizer canonicalizes loaded modules.

---

### 6.11 World Assembly Pipeline `[E]`
**Source:** `src/worldassembly/` — `schema.py`, `resolver.py`, `context.py`,
`entity_spawner.py`, `models.py`

Takes `WorldCompositionSpec`, resolves module dependencies, validates constraints, and
produces an assembled world ready for kernel initialization.

---

### 6.12 World Building Compiler `[E]`
**Source:** `src/worldbuilding/compiler.py`, `src/worldbuilding/validator.py`,
`src/worldbuilding/recipe.py`, `src/worldbuilding/repository.py`

Compiles declarative `WorldSpec` YAML into `AssemblyContext`. Validator checks schema,
referential integrity, and constraint satisfaction before compilation.

---

### 6.13 Procedural World Generator `[E]`
**Source:** `src/worldgeneration/generator.py` — `ProceduralCompositionGenerator`
`src/worldgeneration/scorer.py`, `src/worldgeneration/schema.py`

5-stage pipeline: terrain → settlement → budget enforcement → BFS dependency resolution
→ conflict check. Seed-based parameter randomization. Produces YAML for the world
building compiler.

---

## 7. Domain Architecture

**Group Score: 3 / 15** — All 4 items `[E]`; no gaps (updated 2026-06-26: 7.4 resolved)

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 4 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 7.1 Domain Ownership Boundaries `[E]`
**Source:** `docs/simulation/domains/domain_ownership_map.md`

14 domains, all read-only (return typed result records). Maps each domain to owned state
slice, decision-pipeline stage, key responsibility, output type, and interaction rules.

---

### 7.2 No Cross-Domain Import Rule `[E]` (design pattern)
**Source:** `docs/simulation/domains/domain_ownership_map.md` — Prohibited Patterns.
Enforced by architecture tests.

Cross-domain coupling must be mediated through typed core types only. Violation is an
architecture test failure.

---

### 7.3 Feature Flag Gating Model `[E]`
**Source:** `src/domains/optimization/feature_flags.py` — `FeatureFlagManager`, `FeatureMode`

Four modes: `OFF`, `SHADOW`, `ON`, `STRICT`. All 14 domain packages gated through this.
Used to safely roll out new domains.

---

### 7.4 Presenter / Read-Model Separation `[E]`
**Source:** `src/api/presenters/` — `campaigns.py`, `chronicle.py`, `decisions.py`, `economy.py`, `scenarios.py`, `state_presenter.py`; `src/api/read_model_cache.py`

`StatePresenter` shapes `AuthoritativeState` into API-safe read models.

**Status (updated 2026-06-26):** Resolved. Unified presenter layer implemented across 6 dedicated presenter files — campaigns, chronicle, decisions, economy, scenarios, and state. All API routes now shape read models through presenters rather than exposing raw domain objects.

---

## 8. Scheduling & Budget Infrastructure

**Group Score: 3 / 15** — All 5 items `[E]`; no gaps (updated 2026-06-26: 8.5 resolved)

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 5 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 8.1 Tick Budget Allocation `[E]`
**Source:** `src/engine/kernel.py` — phase cost tracking. `src/config/profiles.py`,
`src/config/optimization_profiles.py`, `src/perf/profiles.py`

Per-phase millisecond cost tracking. `RuntimeProfile` defines tick budget limits per
hardware class (A/B/C). Budget overruns are logged; hard limits enforced in certification.

---

### 8.2 Entity / Provider Budget `[E]`
**Source:** `src/engine/governor.py`, `src/config/profiles.py`

Maximum entity count and provider calls per tick bounded by runtime profile. Entities
exceeding budget are deferred.

---

### 8.3 Cache Registry `[E]`
**Source:** `src/engine/cache_registry.py` — `CacheRegistry`, `ICacheable`, `CacheBudgetPolicy`,
`CacheMetrics`

Uniform management of all simulation caches. `ICacheable` protocol. `sweep_caches()`
runs eviction using `CacheBudgetPolicy`. Metrics exposed per-cache.

---

### 8.4 Movement Plan Cache `[E]`
**Source:** `src/engine/movement_cache.py`

Specialized cache registered with `CacheRegistry`. Keyed by
`(entity_id, target_pos, occupancy_version)`. Invalidated by dirty set.

---

### 8.5 Degraded Mode Contract `[E]`
**Source:** `src/domains/optimization/degradation.py` — `GracefulDegradationManager`; `src/domains/optimization/` — degradation level, cache strategy; `docs/engine/known_limitations.md`

**Status (updated 2026-06-26):** Implemented. `GracefulDegradationManager` provides full broker semantics: `update_pressure()`, `get_provider_cap()`, `should_skip_phase()`, `generate_report()`. Recovery semantics and broker behavior are defined and operational.

---

## 9. Observability & Replay Infrastructure

**Group Score: 3 / 15** — All 6 items `[E]`; no gaps.

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 6 items `[E]` — no gaps in this group |
| Impact if Gaps Persist | 1 | No `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | No gaps to protect; all behaviors covered at the implementation boundary |

### 9.1 Typed Event Emission Pipeline `[E]`
**Source:** `src/engine/replay_manager.py` — `ReplayManager.emit()`
`src/engine/observability.py`

Policy-gated typed event emission. Chunked async write strategy.

---

### 9.2 Replay Manager `[E]`
**Source:** `src/engine/replay_manager.py`, `src/engine/replay_buffer.py`,
`src/engine/replay_sink.py`

Full lifecycle: accumulation, chunked rotation, async persistence, finalization.
`finalize()` waits for all async writes before run teardown.

---

### 9.3 Log Compaction `[E]`
**Source:** `src/core/retention.py` — retention policies per event category.
`src/engine/compactor.py` — `StateUpdateCompactor`

Per-category retention policies. Compaction is workflow-driven — no automated background
compactor during a live sim.

---

### 9.4 World Metrics Extraction `[E]`
**Source:** `src/engine/metrics.py` — `MetricsService`, `WorldMetrics`

`extract_metrics()` derives world-level signals from `AuthoritativeState` each tick.
`detect_strategy_shifts()` compares consecutive metrics.

---

### 9.5 Certification Harness `[E]`
**Source:** `src/certification/harness.py`, `src/certification/conformance.py`,
`src/certification/scenarios.py`, `src/certification/recorder.py`

Full pipeline: execute standard scenario set, verify determinism, check hard law
compliance, measure against hardware class thresholds, produce `CertificationReport`.

---

### 9.6 Parity Ledger `[E]`
**Source:** `docs/parity_ledger/*.yaml`

Machine-readable ledger of every verifiable simulation law. P0 entries require a passing
`test_path`.

**Open P0 items (confirmed):**
- `COMB-006` — AoE legality split — `missing`
- `COMB-133`, `COMB-134` — Phase 8/9 ownership doc stubs — `missing`
- `STRAT-164`, `STRAT-177` — Missing parity tests — `missing`
- `SOC-134` — Missing parity test — `missing`

---

## 10. World Dynamics Foundation

**Group Score: 3 / 15** — All 5 items `[E]` (updated 2026-06-22: E21B resolved 10.3 + 10.5); no remaining gaps.

| Dimension | Score | Reason |
|---|---|---|
| Completeness Gap | 1 | All 5 items `[E]` — 10.3 and 10.5 resolved by TCK-20260619-E21B-REGEN-SERVICE |
| Impact if Gaps Persist | 1 | No remaining `[P]` or `[M]` items; no gap impact |
| Test Shield | 1 | 17 tests pass in `tests/unit/world/test_resource_ecology.py`; parity entries verified |

### 10.1 World Dynamics System `[E]`
**Source:** `src/engine/world_dynamics.py` — `WorldDynamicsSystem.resolve_dynamics()`

Orchestrates world-level periodic processes: ecology, spawning, calamities, regional
trauma. Runs on cadence, not every entity tick.

---

### 10.2 Entity Spawn Service `[E]`
**Source:** `src/world/spawn.py` — `SpawnService.process_spawns()`

Density-driven entity spawning. Evaluates regional entity density against thresholds.
Spawns new entities into under-populated regions up to capacity limits.

---

### 10.3 Resource Ecology Service `[E]`
**Source:** `src/world/ecology.py` — `ResourceEcologyService.process_ecology()`

Exists and runs as part of `WorldDynamicsSystem`.

**Status (updated 2026-06-22):** Regen logic implemented by TCK-20260619-E21B-REGEN-SERVICE.
`process_ecology()` now applies seasonal multipliers and per-node recovery rates.
`RESOURCE_DEPLETED` and `RESOURCE_RECOVERED` events emitted via `StateUpdate.world_events_add`.
17 tests pass in `tests/unit/world/test_resource_ecology.py`. Parity entries
TOWN-137/173/174/175 verified. Complex multi-stage ecological cycles (density-dependent
rates, cross-region propagation) remain out of scope.

---

### 10.4 Calamity Service `[E]`
**Source:** `src/world/calamity.py` — `CalamityService`

`process_world_dynamics()` evaluates calamity conditions. `apply_calamity_consequences()`
distributes effects from recent deaths to regional state.

---

### 10.5 Resource Node Regeneration (Ecological Cycles) `[E]`
**Source:** `src/world/ecology.py` — `ResourceEcologyService.process_ecology()`

**Status (updated 2026-06-22):** Implemented by TCK-20260619-E21B-REGEN-SERVICE (2026-06-20).
Seasonal growth curves, depletion cooldown timers, and per-node recovery rates are all
present in the updated `ResourceEcologyService`. The ecology loop now closes properly.
See Finding 5 for detailed implementation evidence.

---

## Summary Table

| # | Feature | Status | Category |
|---|---|---|---|
| 1.1 | Deterministic Tick Loop | `[E]` | Kernel |
| 1.2 | 6-Phase Kernel Ordering | `[E]` | Kernel |
| 1.3 | Phase Dependency Graph | `[E]` | Kernel |
| 1.4 | Deterministic Scheduler | `[E]` | Kernel |
| 1.5 | Cadence Gating | `[E]` | Kernel |
| 1.6 | Level of Detail System | `[E]` | Kernel |
| 1.7 | Governance / Eligibility Gating | `[E]` | Kernel |
| 1.8 | Worker / Concurrency Model | `[E]` | Kernel |
| 1.9 | Per-Phase Read/Write Domain Permissions | `[E]` | Kernel |
| 2.1 | Authoritative State Model | `[E]` | State |
| 2.2 | Immutability Enforcement | `[E]` | State |
| 2.3 | Deterministic RNG | `[E]` | State |
| 2.4 | Canonical State Hashing | `[E]` | State |
| 2.5 | Authoritative vs Non-Auth Partitioning | `[E]` | State |
| 2.6 | State Serialization | `[E]` | State |
| 3.1 | Typed Result Records Pattern | `[E]` | Mutation |
| 3.2 | Authoritative Mutation Pipeline | `[E]` | Mutation |
| 3.3 | State Update Compactor | `[E]` | Mutation |
| 3.4 | Dirty Entity Tracking | `[E]` | Mutation |
| 3.5 | Conflict Resolution (Priority Order) | `[E]` | Mutation |
| 3.6 | Phase Stability Guard | `[E]` | Mutation |
| 3.7 | Resource Conservation Law | `[E]` | Mutation |
| 4.1 | Spatial Grid / Cell-Based Indexing | `[E]` | Spatial |
| 4.2 | Spatial Query Service | `[E]` | Spatial |
| 4.3 | Flow Field Navigation | `[E]` | Spatial |
| 4.4 | Movement System | `[E]` | Spatial |
| 4.5 | Movement Plan Cache | `[E]` | Spatial |
| 4.6 | Occupancy Snapshot | `[E]` | Spatial |
| 4.7 | Legality Checking | `[E]` | Spatial |
| 5.1 | Combat Damage Formula | `[E]` | Math |
| 5.2 | Attribute Cap Enforcement | `[E]` | Math |
| 5.3 | Stamina System | `[E]` | Math |
| 5.4 | Wound System | `[E]` | Math |
| 5.5 | Tactical Decision Scoring | `[E]` | Math |
| 5.6 | Goal / Route Scoring Framework | `[E]` | Math |
| 5.7 | XP / Reward Classification Math | `[E]` | Math |
| 5.8 | Parameter Expression Evaluator | `[E]` | Math |
| 5.9 | Module Scoring System | `[E]` | Math |
| 5.10 | Macro-Economy Health Metrics | `[E]` | Math |
| 6.1 | Entity Anatomy Model | `[E]` | Modelling |
| 6.2 | Entity Lifecycle Model | `[E]` | Modelling |
| 6.3 | Entity Builder | `[E]` | Modelling |
| 6.4 | Typed Durable State Rule | `[E]` | Modelling |
| 6.5 | Content Catalog & Registry | `[E]` | Modelling |
| 6.6 | Hardcoded Fallback Paths | `[P]` | Modelling |
| 6.7 | Content Pack Manifest & Validation | `[E]` | Modelling |
| 6.8 | Content Family Extension Pattern | `[E]` | Modelling |
| 6.9 | Namespace Isolation | `[E]` | Modelling |
| 6.10 | World Module Schema & Repository | `[E]` | Modelling |
| 6.11 | World Assembly Pipeline | `[E]` | Modelling |
| 6.12 | World Building Compiler | `[E]` | Modelling |
| 6.13 | Procedural World Generator | `[E]` | Modelling |
| 7.1 | Domain Ownership Boundaries | `[E]` | Domain Arch |
| 7.2 | No Cross-Domain Import Rule | `[E]` | Domain Arch |
| 7.3 | Feature Flag Gating Model | `[E]` | Domain Arch |
| 7.4 | Presenter / Read-Model Separation | `[E]` | Domain Arch |
| 8.1 | Tick Budget Allocation | `[E]` | Budget |
| 8.2 | Entity / Provider Budget | `[E]` | Budget |
| 8.3 | Cache Registry | `[E]` | Budget |
| 8.4 | Movement Plan Cache | `[E]` | Budget |
| 8.5 | Degraded Mode Contract | `[E]` | Budget |
| 9.1 | Typed Event Emission Pipeline | `[E]` | Observability |
| 9.2 | Replay Manager | `[E]` | Observability |
| 9.3 | Log Compaction | `[E]` | Observability |
| 9.4 | World Metrics Extraction | `[E]` | Observability |
| 9.5 | Certification Harness | `[E]` | Observability |
| 9.6 | Parity Ledger | `[E]` | Observability |
| 10.1 | World Dynamics System | `[E]` | World |
| 10.2 | Entity Spawn Service | `[E]` | World |
| 10.3 | Resource Ecology Service | `[E]` | World |
| 10.4 | Calamity Service | `[E]` | World |
| 10.5 | Resource Node Regeneration | `[E]` | World |

**Totals: 71 Existing · 1 Partial · 0 Missing** _(updated 2026-06-26: 1.8, 1.9, 4.3, 4.7, 5.4, 5.10, 7.4, 8.5 resolved; previous "63 E / 7 P / 2 M" corrected)_

---

## Group Health Summary

| Group | Items | `[P]`/`[M]` | Score |
|---|---|---|---|
| §6 Entity & Content Modelling | 13 | 1 `[P]` (6.6 hardcoded fallbacks) | 9 / 15 |
| §1 Kernel & Execution | 9 | 0 (updated 2026-06-26) | 3 / 15 |
| §2 State Architecture | 6 | 0 | 3 / 15 |
| §3 Mutation Architecture | 7 | 0 | 3 / 15 |
| §4 Spatial & Navigation | 7 | 0 (updated 2026-06-26) | 3 / 15 |
| §5 Mathematical & Formula | 10 | 0 (updated 2026-06-26) | 3 / 15 |
| §7 Domain Architecture | 4 | 0 (updated 2026-06-26) | 3 / 15 |
| §8 Scheduling & Budget | 5 | 0 (updated 2026-06-26) | 3 / 15 |
| §9 Observability & Replay | 6 | 0 | 3 / 15 |
| §10 World Dynamics | 5 | 0 | 3 / 15 |

**Highest-priority group: §6 Entity & Content Modelling (9/15)** — 6.6 hardcoded fallback paths fail silently in non-strict modes.

---

## Key Findings

Risk scores below use the 5-dimension Foundation Risk rubric (max 50).

### Finding 1: AoE Legality parity bug — **RESOLVED: TCK-20260619-PARITY-P0-BUGS (2026-06-19)**

~~`[P]` item 4.7 — `AoELegalityChecker`. Parity entry `COMB-006` was an active P0 bug.~~

Parity entry COMB-006 (`status: verified`) — AoE legality correctly splits impact-center and radius checks. Original score: 43 / 50.

### Finding 2: Flow-Field Navigation local-minima risk — **RESOLVED (2026-06-26)**

~~`[P]` item 4.3 — `FlowFieldService`. Linear stepping; complex obstacle grids cause trapping.~~

A* pathfinding added alongside flow field (`navigation.py:74`). Hybrid routing addresses local-minima risk. Original score: 31 / 50.

### Finding 3: Hardcoded content fallback paths fail silently (Score: 29 / 50)

`[P]` item 6.3 — `ContentFallbackSystem`. Fallback to hardcoded records when catalog unavailable.

| Dimension | Score | Reason |
|---|---|---|
| Gap Severity | 6 | Fallback silently produces wrong entity types — no warning surfaced to caller |
| Downstream Risk | 7 | World assembly, entity spawning, quest generation all depend on content resolution |
| Test Shield | 5 | FallbackRestrictedError tests exist but teardown errors observed (D10 audit) |
| Runtime Impact | 5 | Degraded-mode content, not crash — hard to notice |
| Recurrence Risk | 6 | Triggered any time catalog is unavailable or partially loaded |
| **Total** | **29** | |

### Finding 4: Presenter / Read-Model Separation — **RESOLVED (2026-06-26)**

~~`[P]` item 7.4 — API routes partially expose raw domain models (violates architecture rule).~~

Unified presenter layer implemented in `src/api/presenters/` (`campaigns.py`, `chronicle.py`, `decisions.py`, `economy.py`, `scenarios.py`, `state_presenter.py`). Original score: 20 / 50.

### Finding 5: Resource Ecology Service — regeneration logic absent (Score: 19 / 50) — **RESOLVED: TCK-20260619-E21B-REGEN-SERVICE (2026-06-20)**

`[P]` item 10.3 — `ResourceEcologyService` is wired and tick-live but regeneration cycles not implemented.

**Status: DONE.** TCK-20260619-E21B-REGEN-SERVICE implemented the regen loop (`src/world/ecology.py:process_ecology()`), `RESOURCE_DEPLETED` emitter (`src/engine/economy.py:_apply_world_effects()`), `RESOURCE_RECOVERED` emitter, and `StateUpdate.world_events_add` / `AuthoritativeState.recent_world_events` infrastructure. 17 tests pass in `tests/unit/world/test_resource_ecology.py`. Parity entries TOWN-137/173/174/175 verified.

| Dimension | Score | Reason |
|---|---|---|
| Gap Severity | 5 | Missing: node recharge over time; depletion becomes permanent |
| Downstream Risk | 7 | Economy stagnates without regeneration — quests, faction pressure, trade all affected |
| Test Shield | 2 | Wiring tested; regeneration behavior untested (nothing to test) |
| Runtime Impact | 3 | Nodes don't crash — they simply never refill |
| Recurrence Risk | 2 | Only observable in long-run simulations |
| **Total** | **19** | |

### Partial Items — Ranked Risk Summary

| Rank | ID | Feature | Risk Score |
|---|---|---|---|
| 1 | 6.6 | Content Fallback System | 29 / 50 |
| ~~2~~ | ~~4.7~~ | ~~AoE Legality Checker~~ | ~~43 / 50~~ **RESOLVED** (TCK-20260619-PARITY-P0-BUGS) |
| ~~3~~ | ~~4.3~~ | ~~Flow-Field Navigation~~ | ~~31 / 50~~ **RESOLVED** (2026-06-26) |
| ~~4~~ | ~~7.4~~ | ~~Presenter / Read-Model Separation~~ | ~~20 / 50~~ **RESOLVED** (2026-06-26) |
| ~~5~~ | ~~10.3~~ | ~~Resource Ecology Service~~ | ~~19 / 50~~ **RESOLVED** (E21B) |
| ~~6~~ | ~~8.5~~ | ~~Degraded Mode Contract~~ | ~~12 / 50~~ **RESOLVED** (2026-06-26) |
| ~~7~~ | ~~5.4~~ | ~~Wound System~~ | ~~10 / 50~~ **RESOLVED** (TCK-20260619-PARITY-P0-BUGS) |
| ~~8~~ | ~~1.9~~ | ~~Per-Phase Domain Permissions~~ | ~~8 / 50~~ **RESOLVED** (2026-06-26) |

### Missing Items

All previously missing items resolved (updated 2026-06-26):

| ID | Feature | Status |
|---|---|---|
| ~~1.9~~ | ~~Per-Phase Read/Write Domain Permissions~~ | **RESOLVED** — `src/engine/phase_domain_permissions.py` |
| ~~5.10~~ | ~~Macro-Economy Health Metrics~~ | **RESOLVED** — `GoldSinkSystem` + `GET /economy/health` |
| ~~10.5~~ | ~~Resource Node Regeneration~~ | **RESOLVED** — TCK-20260619-E21B-REGEN-SERVICE (2026-06-20) |

---

## Recommended Follow-Up Tickets

| Priority | Item |
|---|---|
| P1 | Surface warning on hardcoded fallback activation (6.6) |
| ~~P0~~ | ~~Fix `COMB-006` AoE legality parity bug (4.7)~~ — **DONE** (TCK-20260619-PARITY-P0-BUGS) |
| ~~P1~~ | ~~Add obstacle/maze regression tests for Flow-Field Navigation (4.3)~~ — **DONE** (2026-06-26) |
| ~~P1~~ | ~~Complete Presenter / Read-Model Separation (7.4)~~ — **DONE** (2026-06-26) |
| ~~P2~~ | ~~Implement Resource Node Regeneration (10.5)~~ — **DONE** (TCK-20260619-E21B-REGEN-SERVICE) |
| ~~P2~~ | ~~Implement Macro-Economy Health Metrics (5.10)~~ — **DONE** (2026-06-26) |
| ~~P2~~ | ~~Define and enforce Per-Phase Domain Permissions (1.9)~~ — **DONE** (2026-06-26) |

---

## Related Dimensions

- **D01 (RPG Feature Impact)** — Resource Ecology (10.3/10.5) and AoE (3.3) appear
  in D01's top-priority missing/partial features; risk scores here confirm the sequencing
- **D09 (System Wiring)** — verified all 61 `[E]` items are live-wired; corrected the
  D02 count from 53 to 61; found 20+ live domain-phase systems not in this inventory
- **D10 (Test Coverage)** — `[P]` items ranked 1–3 above are the highest regression-risk
  targets; D10 should verify test shield claims made in Key Findings
- **D14 (Coupling Depth)** — item 7.4 (Presenter separation) feeds directly into D14's
  raw-model API surface analysis
- **D17 (Documentation Currency)** — `known_limitations.md` staleness found during
  this audit; D17 confirmed and expanded the list of stale claims
