# Engine Foundation Features — Inventory

## Scope

This document lists every **technical enabling capability** that RPG features are built
on top of. It does not list RPG features themselves (combat, economy, quests, etc.) —
it lists the algorithms, mathematical systems, data structures, design patterns, and
infrastructure that those RPG features depend on to function.

Status labels: `[E]` Existing — implemented and verified. `[P]` Partial — implemented
with confirmed gaps. `[M]` Missing — zero or near-zero code.

Scoring framework: see `foundation_feature_framework.md` (6 dimensions, 60 max).

---

## 1. Kernel & Execution

The runtime model: how the engine runs, in what order, with what isolation guarantees.

---

### 1.1 Deterministic Tick Loop `[E]`
**Source:** `src/engine/kernel.py` — `Kernel.tick_once()`, `_tick_once_inner()`

Single-threaded deterministic entry point. Each tick runs a fixed sequence of internal
phases. Phase costs are tracked per-tick. `_guard_stability()` detects isolation
breaches (state mutation during non-resolution phases). The tick loop is the outermost
contract that all other execution guarantees depend on.

---

### 1.2 6-Phase Kernel Ordering `[E]`
**Source:** `src/engine/phases.py` — `TickPhase`, `get_authoritative_phases()`
`src/engine/kernel.py` — `_phase_init/scheduling/collection/resolution/cleanup/advancement/persistence`

Fixed sequence: Init → Scheduling → Collection → Resolution → Cleanup → Advancement →
Persistence. Each phase is a named, timed, isolated step. Order is not configurable at
runtime — it is a law.

---

### 1.3 Phase Dependency Graph `[E]`
**Source:** `src/engine/phase_graph.py` — `PhaseDependencyGraph`, `PhaseMetadata`

Feature-flag-aware phase enabling. Records which phases depend on which other phases.
`should_run_phase()` consults the graph and active feature flags before executing a
phase. Prevents orphaned phase execution when a dependency domain is disabled.

**Gap:** Per-phase declared read/write domain permissions not yet enforced
(`RPG-INFRA-155`, `RPG-INFRA-156`) — the graph exists but permission boundaries within
phases are unchecked.

---

### 1.4 Deterministic Scheduler `[E]`
**Source:** `src/engine/scheduler.py` — `DeterministicScheduler`, `PeriodicDefinition`

Selects work for each tick across three work classes: `CRITICAL` (every tick),
`PERIODIC` (every N ticks), `DEFERRED` (background). Deterministic ordering is
guaranteed — same tick always produces same work selection given same state.

---

### 1.5 Cadence Gating `[E]`
**Source:** `src/engine/cadence.py` — `SystemCadence`, `should_run()`

Per-system, per-entity cadence control. `should_run(tick, entity_id, cadence)` gates
subsystem execution without adding scheduler overhead. Used to run non-critical domain
logic (e.g. world emergence signals) every N ticks instead of every tick.

---

### 1.6 Level of Detail (LOD) System `[E]`
**Source:** `src/engine/lod.py` — `LODService`

Distance-based execution skipping. Entities far from focus points run at reduced
fidelity (`determine_lod()`) or skip execution entirely (`should_execute()`). Enables
large entity populations by concentrating computation near active areas.

---

### 1.7 Governance / Eligibility Gating `[E]`
**Source:** `src/engine/governor.py`, `src/engine/phase_governor.py`, `src/core/governance.py`

Policy-based per-entity eligibility checks before scheduling. Entities that fail
governance rules are excluded from the tick entirely. Prevents invalid or dead entities
from consuming pipeline budget.

---

### 1.8 Worker / Concurrency Model `[P]`
**Source:** `src/engine/worker_manager.py`, `src/engine/worker_logic.py`,
`src/core/worker_protocol.py`, `src/core/concurrency_law.py`

Thread and worker execution modes alongside sequential. `WorkerProtocol` defines the
contract for isolated per-entity execution. `ConcurrencyLaw` enforces isolation rules.

**Gap:** Bit-identical parity is only officially certified for **Sequential** mode.
Thread/worker modes exist and pass functional tests but are not certified for replay
fidelity. Any run requiring deterministic replay must use sequential.

---

### 1.9 Per-Phase Read/Write Domain Permissions `[M]`
**Source:** None — unchecked. `docs/logic_checklist_exhaustive.md` items `RPG-INFRA-155`, `RPG-INFRA-156`.

Each engine phase should declare which state domains it is allowed to read and which it
is allowed to write. Currently the coarse single-mutation-point law is enforced (no
writes outside Resolution) but fine-grained per-phase domain permission declarations
are not implemented or checked.

---

## 2. State Architecture

What authoritative simulation truth is, how it is structured, and what makes it valid.

---

### 2.1 Authoritative State Model `[E]`
**Source:** `src/core/state.py` — `AuthoritativeState`

Central frozen dataclass holding all durable simulation truth: entities, world, regions,
buildings, resource nodes, RNG checkpoint, tick counter. All simulation reads go through
this. It is never directly mutated — only replaced through the apply path.

---

### 2.2 Immutability Enforcement `[E]`
**Source:** `src/core/immutability.py` — `deep_freeze()`, `shallow_freeze()`

Runtime immutability guard over arbitrary Python objects. Converts mutable containers
(dicts, lists) to read-only proxies and verifies dataclasses are frozen before use.
`deep_freeze()` is used at state boundaries to ensure no accidental in-place mutation
escapes the apply path.

---

### 2.3 Deterministic RNG `[E]`
**Source:** Documented in `docs/engine/architecture.md`, `docs/engine/contracts/simulation_kernel_contract.md`.
`src/core/state.py` — `rng_checkpoint` field. `src/engine/checkpoint.py` — RNG state preserved in canonical hash.

Seed-Domain-Identity formula: all randomness flows through a single `DeterministicRNG`
interface seeded per-tick per-entity. No authoritative logic may use `time.time()`,
`random.random()`, or other non-seeded sources. RNG state is checkpointed in
`AuthoritativeState.rng_checkpoint` for replay fidelity.

---

### 2.4 Canonical State Hashing `[E]`
**Source:** `src/engine/checkpoint.py` — `CanonicalStateHasher`, `BudgetedCanonicalHasher`,
`CanonicalHashScheduler`, `HashMode`

Converts `AuthoritativeState` to a canonical JSON representation and SHA-256 hashes it.
`BudgetedCanonicalHasher` applies a subsystem budget to avoid hashing on every tick.
`CanonicalHashScheduler` controls when full hashes fire vs. skipped. Used for replay
verification and determinism certification.

---

### 2.5 Authoritative vs Non-Authoritative State Partitioning `[E]`
**Source:** `docs/core/state.md`, `src/core/state.py`

Hard rule: anything that survives beyond the current tick lives in `AuthoritativeState`.
Non-authoritative state (read caches, observability buffers, transient signals) must
not contain durable simulation truth. Law is enforced by convention and architecture
tests — see Enforcement Gap note in framework.

---

### 2.6 State Serialization `[E]`
**Source:** `src/core/serialization.py` — `StateSerializer`

`serialize()` converts `AuthoritativeState` to a stable JSON string.
`deserialize()` recovers a dict. Used by replay manager for run artifacts and by
certification harness for cross-run comparison. Current implementation uses
`dataclasses.asdict` with JSON encoding.

---

## 3. Mutation Architecture

How state is allowed to change, and the patterns that enforce that.

---

### 3.1 Typed Result Records Pattern `[E]`
**Source:** `src/core/updates.py` — `StateUpdate`, typed sub-update models.
`src/core/update_models/` — `inventory.py`, `quests.py`, `resources.py`.

Domains never write state directly. They return typed `StateUpdate` records that describe
proposed changes. The apply path reads these records and decides whether and how to
commit them. This is the pattern that makes domain logic testable in isolation.

---

### 3.2 Authoritative Mutation Pipeline (Apply Path) `[E]`
**Source:** `src/engine/apply.py` — 17-phase refinement sequence.
`src/engine/apply_plan.py`

The single authoritative path through which all durable state changes flow. Takes a
`StateUpdate` from the Collection phase and applies it through 17 ordered refinement
stages. No state change can become durable except through this path. All conservation
law enforcement, conflict resolution, and integrity checks run here.

---

### 3.3 State Update Compactor `[E]`
**Source:** `src/engine/compactor.py` — `StateUpdateCompactor`, `CompactionMetrics`

Merges redundant fields in a `StateUpdate` before it enters the apply path. Reduces
the number of dataclass `replace()` calls and memory allocation pressure during
high-entity-count ticks. Operates on the update record, not on `AuthoritativeState`
directly.

---

### 3.4 Dirty Entity Tracking `[E]`
**Source:** `src/core/dirty.py` — `DirtySet`, `DirtySetBuilder`, `DirtyDependencyGraph`,
`CandidateSelector`

Rich change-set propagation system. `DirtySet` records which entities changed and with
what semantic tags. `DirtySetBuilder` accumulates marks from `StateUpdate`.
`DirtyDependencyGraph` expands a dirty set to include transitively affected entities.
`CandidateSelector` uses the dirty set to restrict pipeline work to only affected
entities. `DirtySetLeakError` catches dirty sets escaping their intended scope.

---

### 3.5 Conflict Resolution (Deterministic Priority Order) `[E]`
**Source:** `src/engine/kernel.py` — result sorting by `(class_priority, -local_priority, entity_id)`.

When multiple entities produce conflicting updates (e.g. two entities contending for
the same resource node), the apply path resolves them by deterministic ordering.
`class_priority` (entity class) and `local_priority` (within-class rank) determine
which update wins. Tie-breaking by `entity_id` guarantees identical resolution across
replays.

**Gap:** Complex social negotiation or "roll-off" logic not implemented. Contention
is first-come-first-served by deterministic registration order only.

---

### 3.6 Phase Stability Guard (Isolation Breach Detection) `[E]`
**Source:** `src/engine/kernel.py` — `_guard_stability()`

Takes a fingerprint of `AuthoritativeState` at the start of each non-Resolution phase.
Checks fingerprint again at phase end. If the state changed, raises an `IsolationBreach`
error identifying which phase caused the illegal mutation. The primary runtime guard
against domain logic accidentally mutating live state.

---

### 3.7 Resource Conservation Law `[E]`
**Source:** `src/core/conservation.py` — `ResourceTransactionResolver`, `TransactionResult`

Atomic transaction model for resource movements. No resource can be created or destroyed
— only transferred between containers. `resolve()` checks both source and destination
are valid before committing. Returns a typed `TransactionResult` indicating success,
partial fulfillment, or rejection. All harvest, trade, crafting, and loot operations
must go through this.

---

## 4. Spatial & Navigation

The geometric and algorithmic layer that grounds entities in space.

---

### 4.1 Spatial Grid / Cell-Based Indexing `[E]`
**Source:** `src/engine/spatial.py` — `SpatialGrid`

Divides the world into fixed-size cells (default `cell_size=5`). `get_neighbors()`
returns entity IDs within a radius using cell-bucket lookup — O(1) average vs. O(N)
linear scan. `get_in_bounds()` returns all entities within a rectangular region.
Rebuilt each tick from current entity positions.

---

### 4.2 Spatial Query Service `[E]`
**Source:** `src/engine/spatial_query.py` — `SpatialQueryService`

High-level spatial queries over `AuthoritativeState`: `nearest_resource_node()`,
`nearest_building()`, `nearby_entities()`, `get_region_at()`, `get_building_at()`,
`get_node_at()`, `get_corpse_at()`, `get_ground_item_at()`. All queries accept an
optional `dirty` parameter to restrict scope to recently-changed areas.

**Gap:** `get_region_at()` uses a point-in-bounds rectangle check. No proper
geospatial index (R-tree, quadtree) for large region counts. Acceptable at current
world scale; will degrade with many overlapping regions.

---

### 4.3 Flow Field Navigation `[P]`
**Source:** `src/systems/world_systems/navigation.py` — `FlowFieldService`, `NavigationSystem`

`FlowFieldService` builds a flow field toward a target and returns step directions.
`NavigationSystem.get_next_step()` combines flow field with occupancy avoidance to
produce a single movement step per tick.

**Gaps (confirmed in `known_limitations.md`):**
- Linear-stepping only: pathfinding through dynamic obstacles (other entities, newly
  spawned objects) is best-effort.
- Congestion weakness: high-density entity overlaps not hardened against all edge cases.
- No A* or true shortest-path with obstacle avoidance. Current approach is gradient
  descent on a flow field, which can get stuck in local minima.

---

### 4.4 Movement System `[E]`
**Source:** `src/engine/movement.py` — `MovementSystem.resolve_move()`

Applies a single movement step from flow field output. Validates the step against
occupancy and spatial constraints before producing a `StateUpdate`. Integrates with
the legality checker for adjacency and reachability verification.

---

### 4.5 Movement Plan Cache `[E]`
**Source:** `src/engine/movement_cache.py` — `MovementPlanCache`, `MovementPlanKey`, `MovementPlan`

Caches next-step movement decisions keyed by `(entity_id, target_pos, occupancy_version)`.
`invalidate_for_dirty()` clears stale entries when the dirty set indicates relevant
changes. Implements `ICacheable` for integration with the cache registry.
Avoids recomputing flow-field steps when position and occupancy are unchanged.

---

### 4.6 Occupancy Snapshot `[E]`
**Source:** `src/engine/occupancy_snapshot.py`

Point-in-time snapshot of which grid cells are occupied by which entities. Used by the
movement system and legality checker for collision avoidance. Rebuilt or incrementally
updated each tick using the dirty set.

---

### 4.7 Legality Checking `[E]`
**Source:** `src/engine/legality.py` — `LegalityServiceV2`

Validates proposed actions against spatial laws: adjacency check, occupancy verification,
region membership, path connectivity. `get_manhattan_dist()`, `is_adjacent()`,
`verify_occupancy()`, `get_region_for_position()`.

**Gap (P0 parity bug `COMB-006`):** AoE legality uses a unified check — impact-center
legality and radius legality are not split. This means AoE attacks that are legal at
center but not at radius (or vice versa) are not correctly adjudicated.

---

## 5. Mathematical & Formula Systems

The arithmetic, scoring, and probability engines that produce numeric outcomes.

---

### 5.1 Combat Damage Formula `[E]`
**Source:** `src/engine/combat.py` — `CombatResolutionSystem.calculate_damage()`

Formula: `damage = (atk × atk_mult) × ((atk × atk_mult) / ((atk × atk_mult) + (def × def_mult) × 2.0 + 1.0))`

Produces diminishing-return damage curves. Tactical multipliers applied via
`_get_tactical_multipliers()`. Durability decay applied to equipment. Supports single
attack, multi-attack, AoE, opportunity attack, and skill usage variants.

---

### 5.2 Attribute Cap Enforcement `[E]`
**Source:** `src/engine/rpg_depth.py` — `enforce_attribute_caps()`

Clamps all entity attributes to defined min/max bounds after any modification.
Called as part of the stat derivation pass. Prevents runaway attribute stacking.

---

### 5.3 Stamina System (Drain & Regen Math) `[E]`
**Source:** `src/engine/rpg_depth.py` — `StaminaService`

Per-action stamina drain rates: `drain_attack()`, `drain_move()`, `drain_harvest()`,
`drain_skill()`. Regen via `tick_regen()` with rest bonus. `get_exhaustion_multiplier()`
returns a performance penalty scalar when stamina is critically low.

---

### 5.4 Wound System (Threshold & Penalty Math) `[E]`
**Source:** `src/engine/rpg_depth.py` — `WoundService`

`should_inflict_wound()` checks `damage > max_hp * threshold`. `create_wound()` builds
a typed `WoundState` with stat penalties. `get_wound_stat_penalties()` and
`get_scar_stat_penalties()` aggregate active penalties into attack/defense modifiers.

**Gap (P1 parity divergence `COMB-290`):** Wound threshold in source
(`damage > max_hp * 0.25`) may diverge from the Mechanics Bible. Needs reconciliation.

---

### 5.5 Tactical Decision Scoring `[E]`
**Source:** `src/engine/tactical.py` — `TacticalDecisionSystem`, `target_score()`

Multi-factor target selection scoring. `evaluate_entity_intent()` scores all candidate
actions and targets, returning the highest-value intent. `select_best_target()` applies
a separate scoring function for ranged/melee targeting. Both use composite tuple
ordering `(priority, score, distance, id)` for deterministic tie-breaking.

---

### 5.6 Goal / Route Scoring Framework `[E]`
**Source:** `src/ai/goals/scorers.py`, `src/ai/goals/base.py` — `GoalScorer`, scored subclasses
`src/ai/score_modifiers.py` — `ScoreModifierSystem`
`src/ai/personality.py` — `PersonalityService`

Pluggable scoring architecture: each route type has a dedicated `GoalScorer` subclass
(HarvestScorer, CombatEngageScorer, CombatRetreatScorer, RecoverScorer, etc.).
`ScoreModifierSystem.apply_modifiers()` applies personality OCEAN trait weights on top
of base scores. `PersonalityService.get_goal_modifiers()` translates OCEAN values to
per-route weight deltas.

---

### 5.7 XP / Reward Classification Math `[E]`
**Source:** `src/engine/combat.py` — `CombatRewardClassificationService.classify_defeated_target()`
`src/engine/combat_rewards.py`

Classifies defeated targets into reward categories with XP and gold multipliers.
`xp_gain = evolution_level × xp_multiplier`. `gold_gain = evolution_level × gold_multiplier`.
`rebirth_eligible` flag triggers entity recycling vs permanent death.

---

### 5.8 Parameter Expression Evaluator `[E]`
**Source:** `src/worldmodules/evaluator.py` — `ModuleParameterEvaluator`

AST-safe arithmetic evaluator for world module parameter expressions. Evaluates
`Union[int, str]` parameter fields that may contain expressions like
`"base_count * 2 + offset"`. Validates constraint satisfaction after evaluation.
Prevents arbitrary code execution while allowing flexible world parameter authoring.

---

### 5.9 Module Scoring System `[E]`
**Source:** `src/worldgeneration/scorer.py` — `ModuleScorer`, `ModuleScore`

Scores world modules against a generation intent across 4 dimensions. Used by the
procedural composition generator to select the best-fit module set for a given world
archetype. Produces typed `ModuleScore` dataclasses.

---

### 5.10 Macro-Economy Health Metrics `[M]`
**Source:** None.

No system currently monitors gold inflation, resource depletion rates, dead-economy
states, or gold-sink effectiveness at the macro level. The per-transaction conservation
law (`3.7`) proves atomic correctness but cannot detect aggregate failure modes like
infinite shops, frozen supply chains, or gold hyperinflation across many entities over
long runs.

---

## 6. Entity & Content Modelling

The ontology: what entities are, what content means, what persists.

---

### 6.1 Entity Anatomy Model `[E]`
**Source:** `src/core/state.py` (EntityState), `docs/mechanics/01_entity_anatomy.md`

Core attributes (STR, DEX, INT, END, CHA), derived stats, biological pressures (hunger,
fatigue, health), XP scaling, evolution level, identity, personality. The foundational
data model all RPG systems read from.

---

### 6.2 Entity Lifecycle Model `[E]`
**Source:** `src/systems/lifecycle_systems/lifecycle.py`, `src/core/lifecycle.py`
`src/systems/lifecycle_systems/biological.py`

Manages spawn → alive → dead → cleanup transitions. `biological.py` processes hunger,
stamina drain, and aging pressures each tick. Death transitions entities out of the
active set. Cleanup removes dead entities and their resources.

---

### 6.3 Entity Builder `[E]`
**Source:** `src/core/builder.py` — `EntityBuilder`

Fluent builder for assembling `EntityState` from class definitions, traits, and
starting inventory. Used at world assembly time and in test fixtures. Ensures all
required fields are populated before an entity enters the simulation.

---

### 6.4 Typed Durable State Rule `[E]` (pattern, not a system)
**Source:** `docs/core/state.md`, `CLAUDE.md` Architecture Rule.

Pattern: anything that survives beyond the current tick must have a typed model, a
stable location in entity/world/registry state, a defined lifecycle, and tests.
No durable meaning may live in `reason` strings, free-form `metadata`, comments, or
temporary local variables. Enforced by code review and architecture tests — no
automated gate.

---

### 6.5 Content Catalog & Registry `[E]`
**Source:** `src/core/registries.py` — catalog loading, content seeding, hardcoded fallback
`src/content/repository.py`, `src/content/schema.py`, `src/content/resolver.py`

Loads content families (items, recipes, skills, quests, entity classes) from the content
catalog at startup. `ContentResolver` maps symbolic content IDs to concrete definitions.
`ContentRepository` manages the loaded catalog at runtime.

---

### 6.6 Hardcoded Fallback Paths `[P]`
**Source:** `src/core/registries.py` — `runtime_content_source = "legacy_hardcoded"`
`src/core/modes.py` — `HardcodedFallbackForbiddenError`

When the content catalog is missing or incomplete, the registry falls back to hardcoded
seed maps for Phase 1 content. `HardcodedFallbackForbiddenError` is raised in strict
modes that forbid this fallback. A `WARNING` is logged when fallback activates.

**Risk:** Fallback is silent in non-strict modes. Missing catalog entries silently
become old-style hardcoded values instead of validation errors. Any new content type
relying on catalog resolution that has no fallback entry will fail at runtime, not at
content-authoring time.

---

### 6.7 Content Pack Manifest & Validation `[E]`
**Source:** `src/content/pack_manifest.py`, `src/content/validator.py`, `src/content/matrix.py`
`src/content/reference_graph.py`, `src/content/warmup.py`

`ContentPackManifest` declares a content pack's ID, version, dependencies, and content
families. `ContentValidator` checks schema conformance and referential integrity.
`ContentUsageMatrix` tracks which content families have active consumers, documented
schema, and test coverage. `reference_graph.py` tracks dependency edges between content
items for circular-dependency detection.

---

### 6.8 Content Family Extension Pattern `[E]` (pattern)
**Source:** `docs/simulation/adventure_contract.md`, `docs/simulation/world_emergence_contract.md`

Canonical pattern for adding a new content family or route type:
`enum → generator → scorer → mapper → tests`. Proven at small scale in adventure routing
and world emergence. Every new content type must follow this shape. Not enforced
automatically — enforced by ticket convention and review.

---

### 6.9 Namespace Isolation for Content `[E]`
**Source:** `src/worldbuilding/schema.py`, `src/worldmodules/schema.py`

Content IDs use `namespace:id` format to prevent collision between content packs and
world modules. Namespace isolation is validated at assembly time. A region or biome
from pack A cannot silently shadow the same ID from pack B.

---

### 6.10 World Module Schema & Repository `[E]`
**Source:** `src/worldmodules/schema.py` — `WorldModuleSpec`
`src/worldmodules/repository.py`, `src/worldmodules/normalizer.py`, `src/worldmodules/utils.py`

Declarative schema for world capability modules: biomes, ecologies, quest definitions,
relationships, parameterized features, observability tags. `normalizer.py` canonicalizes
loaded modules. Repository loads and indexes all modules by ID and tag.

---

### 6.11 World Assembly Pipeline `[E]`
**Source:** `src/worldassembly/` — `schema.py`, `resolver.py`, `context.py`,
`entity_spawner.py`, `models.py`

Takes a `WorldCompositionSpec` (list of module refs with parameters), resolves module
dependencies, validates constraints, and produces an assembled world ready for kernel
initialization. `entity_spawner.py` materializes the entity population from the
assembled world spec.

---

### 6.12 World Building Compiler `[E]`
**Source:** `src/worldbuilding/compiler.py`, `src/worldbuilding/validator.py`,
`src/worldbuilding/recipe.py`, `src/worldbuilding/repository.py`

Compiles declarative `WorldSpec` YAML into an `AssemblyContext` that the world assembly
pipeline consumes. `validator.py` checks schema, referential integrity, and constraint
satisfaction before compilation. `recipe.py` manages the build recipe format.

---

### 6.13 Procedural World Generator `[E]`
**Source:** `src/worldgeneration/generator.py` — `ProceduralCompositionGenerator`
`src/worldgeneration/scorer.py`, `src/worldgeneration/schema.py`

Generates a `WorldCompositionSpec` from a generation intent using a 5-stage pipeline:
terrain selection → settlement selection → budget enforcement → BFS dependency resolution
→ conflict check. Seed-based parameter randomization (`param_rng`) ensures
reproducibility. Produces YAML output compatible with the world building compiler.

---

## 7. Domain Architecture

How the 14 simulation domains are separated, bounded, and composed.

---

### 7.1 Domain Ownership Boundaries `[E]`
**Source:** `docs/simulation/domains/domain_ownership_map.md`
`docs/architecture/cognition_domain_ownership.md`

Maps each of the 14 domains to its owned state slice, decision-pipeline stage, key
responsibility, output type, and detailed contract. Establishes the interaction rules:
domains read state, they do not write it. No domain imports from another domain package.
Cross-domain concerns flow through `src/core/` types only.

---

### 7.2 No Cross-Domain Import Rule `[E]` (pattern)
**Source:** `docs/simulation/domains/domain_ownership_map.md` — Prohibited Patterns.
Enforced by architecture tests.

`combat_engagement` must not import from `information`. `cooperation` must not import
from `adventure`. Cross-domain coupling must be mediated through typed core types
(`KnowledgeFact`, `LeadState`, `SourceTrustEntry`). Violation is an architecture test
failure.

---

### 7.3 Feature Flag Gating Model `[E]`
**Source:** `src/domains/optimization/feature_flags.py` — `FeatureFlagManager`, `FeatureMode`

Four modes per flag: `OFF` (domain not called), `SHADOW` (called but output ignored),
`ON` (fully active), `STRICT` (active, errors on violation). All 14 domain packages
are gated through this. A domain in `OFF` mode must not be called on the tick path.
Used to safely roll out new domains and to disable experimental features in production
profiles.

---

### 7.4 Presenter / Read-Model Separation `[P]`
**Source:** `src/api/presenters/state_presenter.py`, `src/api/read_model_cache.py`

`StatePresenter` shapes `AuthoritativeState` into API-safe read models. Raw domain
objects are not exposed from API routes.

**Gap:** Confirmed fragmented. Cognition history, live-status, and behavior APIs each
have their own projection logic without a unified presenter layer. As more read surfaces
are added (faction, campaign, history, population), API shape will diverge further.

---

## 8. Scheduling & Budget Infrastructure

How computation is allocated across entities and ticks.

---

### 8.1 Tick Budget Allocation `[E]`
**Source:** `src/engine/kernel.py` — phase cost tracking. `src/config/profiles.py` — `RuntimeProfile`
`src/config/optimization_profiles.py`, `src/perf/profiles.py`

Per-phase millisecond cost tracking via `_phase_costs`. `RuntimeProfile` defines tick
budget limits per hardware class (A/B/C). `OptimizationProfile` resolves scenario-aware
performance settings. Budget overruns are logged; hard limits are enforced in
certification mode.

---

### 8.2 Entity / Provider Budget `[E]`
**Source:** `src/engine/governor.py`, `src/config/profiles.py`

Maximum entity count and maximum provider calls per tick are bounded by the runtime
profile. Entities exceeding budget are deferred. Provider call counts are tracked and
budget exceeded states are reported as degraded mode triggers.

---

### 8.3 Cache Registry `[E]`
**Source:** `src/engine/cache_registry.py` — `CacheRegistry`, `ICacheable`, `CacheBudgetPolicy`, `CacheMetrics`

Uniform management of all simulation caches. Any cache implements `ICacheable`
(get_metrics, evict_expired, clear). `CacheRegistry.sweep_caches()` runs eviction
across all registered caches using a `CacheBudgetPolicy`. Metrics (hits, misses, size)
are exposed per-cache. Prevents unbounded cache growth under long runs.

---

### 8.4 Movement Plan Cache `[E]`
**Source:** `src/engine/movement_cache.py`

Specialized cache for movement next-step decisions. Registered with `CacheRegistry`.
Keyed by `(entity_id, target_pos, occupancy_version)`. Invalidated when dirty set
signals positional or occupancy changes. Avoids re-running flow field calculation for
stationary or unchallenged paths.

---

### 8.5 Degraded Mode Contract `[P]`
**Source:** `src/domains/optimization/` — degradation level, cache strategy
`docs/engine/known_limitations.md`

`DegradationLevel` enum and `CacheStrategy` exist. Domains can check degradation level
and reduce their computational effort accordingly.

**Gap (`known_limitations.md`):** Missing broker behavior, recovery semantics, and
simulation step behavior when brokers are absent are undocumented and unimplemented.
It is unclear whether degraded operation is a supported mode or an undesigned fallback.

---

## 9. Observability & Replay Infrastructure

How the engine records what it did and proves it did it correctly.

---

### 9.1 Typed Event Emission Pipeline `[E]`
**Source:** `src/engine/replay_manager.py` — `ReplayManager.emit()`
`src/engine/observability.py`

Events emitted through `emit(event, policy)`. Policy gates control which event types are
recorded under which observation modes. All events are typed (not free-form strings).
Chunked write strategy: events accumulate in memory then flush asynchronously at chunk
boundaries (`_rotate_chunk()`).

---

### 9.2 Replay Manager `[E]`
**Source:** `src/engine/replay_manager.py` — `ReplayManager`, `on_tick_end()`, `finalize()`
`src/engine/replay_buffer.py`, `src/engine/replay_sink.py`

Manages the full lifecycle of a run's event stream: accumulation, chunked rotation,
async persistence, and finalization. `replay_buffer.py` holds in-memory events.
`replay_sink.py` handles disk I/O. `finalize()` waits for all async writes to complete
before run teardown.

---

### 9.3 Log Compaction `[E]`
**Source:** `src/core/retention.py` — retention policies per event category
`src/engine/compactor.py` — `StateUpdateCompactor` (update-level, not log-level)

Per-category retention policies define which event types are kept long-term (anomalies,
state transitions, death/birth, WARN/ERROR) vs compacted (routine move events, routine
scoring events). Compaction is workflow-driven — no automated background compactor runs
during a live sim.

---

### 9.4 World Metrics Extraction `[E]`
**Source:** `src/engine/metrics.py` — `MetricsService`, `WorldMetrics`

`extract_metrics()` derives world-level signals from `AuthoritativeState` each tick:
alive count, dead count, resource state, regional pressure, strategy distribution.
`detect_strategy_shifts()` compares consecutive metrics for behavioral change signals.
Feeds the observability and anomaly detection layers.

---

### 9.5 Certification Harness `[E]`
**Source:** `src/certification/harness.py`, `src/certification/conformance.py`,
`src/certification/scenarios.py`, `src/certification/recorder.py`

Full pipeline for producing a certification run: execute a standard scenario set,
verify determinism (cross-run hash comparison), check hard law compliance, measure
performance against hardware class thresholds, and produce a `CertificationReport`.
Used for release gating and parity verification.

---

### 9.6 Parity Ledger `[E]`
**Source:** `docs/parity_ledger/*.yaml` — one file per subsystem

Machine-readable ledger of every verifiable simulation law. Each entry: `id`, `text`,
`status` (verified/divergent/missing/unsupported/legacy_verified), `priority` (P0/P1/P2),
`v2_evidence`, `test_path`, `divergence_note`. P0 entries require a passing `test_path`.
Updated whenever behavior changes. The authoritative record of what the engine
guarantees vs. what is known to be wrong or missing.

**Open P0 items (confirmed in scan):**
- `COMB-006`: AoE legality split — `missing`
- `COMB-133`, `COMB-134`: Phase 8/9 ownership doc stubs — `missing`
- `STRAT-164`, `STRAT-177`: Missing parity tests — `missing`
- `SOC-134`: Missing parity test — `missing`

---

## 10. World Dynamics Foundation

The world-level processes that run independently of individual entity actions.

---

### 10.1 World Dynamics System `[E]`
**Source:** `src/engine/world_dynamics.py` — `WorldDynamicsSystem.resolve_dynamics()`

Orchestrates world-level periodic processes: ecology, spawning, calamities, regional
trauma. Runs on a cadence (not every entity tick). Produces a `StateUpdate` covering
world-scale changes. Region lookup (`_get_region_for_pos()`) maps positions to region
state for pressure calculations.

---

### 10.2 Entity Spawn Service `[E]`
**Source:** `src/world/spawn.py` — `SpawnService.process_spawns()`
`src/world/spawn_config.py`

Density-driven entity spawning. Evaluates regional entity density against configured
thresholds. Spawns new entities into under-populated regions up to capacity limits.
Uses `EntityGenerator` for entity materialization.

---

### 10.3 Resource Ecology Service `[P]`
**Source:** `src/world/ecology.py` — `ResourceEcologyService.process_ecology()`

Exists and runs as part of `WorldDynamicsSystem`. Processes entity generator passes
over resource ecology.

**Gap (confirmed in `known_limitations.md`):** Resource nodes do not support complex
regeneration logic — no seasonal growth, depletion cooldowns, or ecology-driven
recovery curves. Nodes are **static or reset on scenario reload**. This is the
single highest-leverage missing foundation feature by simulation impact score.

---

### 10.4 Calamity Service `[E]`
**Source:** `src/world/calamity.py` — `CalamityService`

`process_world_dynamics()` evaluates calamity conditions (disease, disaster, environmental
event) and applies consequences. `apply_calamity_consequences()` distributes effects
from recent deaths to regional state. Feeds regional trauma signals consumed by
`WorldEmergencePhase`.

---

### 10.5 Resource Node Regeneration (Ecological Cycles) `[M]`
**Source:** None.

The specific capability missing from `10.3`: seasonal growth curves, depletion
cooldown timers, per-node recovery rates, ecology-linked regeneration (forest regrows
slower after fire, mine depletes permanently). This is a distinct missing feature from
the `ResourceEcologyService` wrapper that exists — the service scaffolding is there but
the regeneration logic inside it is not.

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
| 1.8 | Worker / Concurrency Model | `[P]` | Kernel |
| 1.9 | Per-Phase Read/Write Domain Permissions | `[M]` | Kernel |
| 2.1 | Authoritative State Model | `[E]` | State |
| 2.2 | Immutability Enforcement | `[E]` | State |
| 2.3 | Deterministic RNG | `[E]` | State |
| 2.4 | Canonical State Hashing | `[E]` | State |
| 2.5 | Authoritative vs Non-Authoritative Partitioning | `[E]` | State |
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
| 4.3 | Flow Field Navigation | `[P]` | Spatial |
| 4.4 | Movement System | `[E]` | Spatial |
| 4.5 | Movement Plan Cache | `[E]` | Spatial |
| 4.6 | Occupancy Snapshot | `[E]` | Spatial |
| 4.7 | Legality Checking | `[P]` | Spatial |
| 5.1 | Combat Damage Formula | `[E]` | Math |
| 5.2 | Attribute Cap Enforcement | `[E]` | Math |
| 5.3 | Stamina System (Drain & Regen) | `[E]` | Math |
| 5.4 | Wound System (Threshold & Penalty) | `[P]` | Math |
| 5.5 | Tactical Decision Scoring | `[E]` | Math |
| 5.6 | Goal / Route Scoring Framework | `[E]` | Math |
| 5.7 | XP / Reward Classification Math | `[E]` | Math |
| 5.8 | Parameter Expression Evaluator | `[E]` | Math |
| 5.9 | Module Scoring System | `[E]` | Math |
| 5.10 | Macro-Economy Health Metrics | `[M]` | Math |
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
| 7.4 | Presenter / Read-Model Separation | `[P]` | Domain Arch |
| 8.1 | Tick Budget Allocation | `[E]` | Budget |
| 8.2 | Entity / Provider Budget | `[E]` | Budget |
| 8.3 | Cache Registry | `[E]` | Budget |
| 8.4 | Movement Plan Cache | `[E]` | Budget |
| 8.5 | Degraded Mode Contract | `[P]` | Budget |
| 9.1 | Typed Event Emission Pipeline | `[E]` | Observability |
| 9.2 | Replay Manager | `[E]` | Observability |
| 9.3 | Log Compaction | `[E]` | Observability |
| 9.4 | World Metrics Extraction | `[E]` | Observability |
| 9.5 | Certification Harness | `[E]` | Observability |
| 9.6 | Parity Ledger | `[E]` | Observability |
| 10.1 | World Dynamics System | `[E]` | World |
| 10.2 | Entity Spawn Service | `[E]` | World |
| 10.3 | Resource Ecology Service | `[P]` | World |
| 10.4 | Calamity Service | `[E]` | World |
| 10.5 | Resource Node Regeneration (Ecological Cycles) | `[M]` | World |

**Totals:** 53 Existing · 9 Partial · 3 Missing