---
status: active
layer: performance
authority: P1
audience: developer
---

# Engine Optimization Architecture

## 0. Status of the statements in this document

Each statement is classified as **verified current behavior**, **target architecture**, or
**superseded/obsolete** (C-15, applied 2026-10-03 from `docs/performance/performance_clause_inventory.md`
§3.5). Unmarked statements describing the five layers and their named classes are verified current
behavior: all the classes named below exist in `src/`. Statements about capacity, memory bounds,
and the governor's trigger are labeled where they are not enforced as written. Pipeline-phase counts
follow `docs/engine/authoritative_pipeline.md` (PERF-D6): this document states none.

## 1. Overview and Design Philosophy

The RPG Simulation Engine is designed to run deterministic simulations at massive scale. **Target, not enforced:** 10,000+ concurrent entities, a 50ms compute latency budget, and a 2GB memory footprint; no check measures any of the three at that scale, and the per-class targets in `docs/engine/performance_contract.md` are the capacity-run targets when a capacity run exists (`PERF-M2-T03`/`T04`). To achieve this without compromising the bit-identical determinism of the simulation laws, the engine implements a 5-layer optimization stack that systematically eliminates $O(N)$ full-world scans, avoids redundant object allocations, and precomputes structural application plans.

```
+-------------------------------------------------------------------------+
|                  LAYER 5: ADAPTIVE GOVERNANCE & PROFILES                |
|      PhaseDependencyGraph | PhaseBudgetGovernor | OptimizationProfile   |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  LAYER 4: PROJECTION & MEMORY BOUNDS                    |
| ReadModelCache | OccupancySnapshot | MovementPlanCache | CacheRegistry  |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  LAYER 3: COMPACTION & PLAN PRECOMPUTATION              |
|        StateUpdateCompactor | ApplyPlanBuilder | ComponentPatch         |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  LAYER 2: DIRTY TRACKING & INVALIDATION                 |
|       DirtyDependencyGraph | Downstream Expansion | Invalidation Policy |
+-------------------------------------------------------------------------+
                                    |
+-------------------------------------------------------------------------+
|                  LAYER 1: CANDIDATE SELECTION & NARROWING               |
| CandidateSelector | ScanPolicy | MovementCandidateSelector | WorkQueue  |
+-------------------------------------------------------------------------+
```

---

## 2. Layer 1: Candidate Selection & Narrowing

In unoptimized simulations, systems iterate over all entities ($O(N)$) every tick to find valid actors for their domain. In the engine, all systems must query the centralized `CandidateSelector`.

### `CandidateSelector` and `ScanPolicy`
The `CandidateSelector` (`src/core/dirty.py`) enforces domain-specific filtering over a fixed set of lower-case domain strings: `movement`, `combat`, `inventory`, `strategic`, `social`, `lifecycle`, `biological`, `attributes`, `town`, `interactions`, `groups`, `shop`, `capacity`, `redirection`, and `all`. (An earlier version of this document named domains such as `LOCOMOTION` and `STRATEGIC_INTELLIGENCE`; those names do not appear in the code and are obsolete.)
- **`ScanPolicy.EXACT_DIRTY`**: Bypasses $O(N)$ scans entirely, returning only entities marked in the specific domain's dirty set.
- **`ScanPolicy.THROTTLED`**: Evaluates entities according to their priority tier and periodic cadence, capping total evaluated candidates per tick to respect the active phase budget.

### `MovementCandidateSelector`
Specifically tailored for the high-frequency Locomotion phase, `MovementCandidateSelector` pre-filters entities based on active path targets, physical readiness (stamina > 0), and lack of hard blocking status effects (e.g., stunned or dead).

### `StrategicWorkQueue`
Strategic cognition evaluations (e.g., project discovery, contract formation) are extremely CPU-intensive. `StrategicWorkQueue` (`src/systems/strategic_systems/work_queue.py`) narrows candidates into seven tiers in priority order: failed action or path, unresolved blockers, active project transition, biological emergency, contract expiration, dirty strategic entities, and a background sweep sample. This prioritizes immediate failures and emergencies while deferring routine capability exploration to background sweep cadences. (The earlier tier names `SURVIVAL`, `COMBAT`, `HAZARD`, `SOCIAL`, `MAINTENANCE`, `CAPABILITY`, `OPPORTUNITY` are obsolete: the count is right, the names are not in the code.)

---

## 3. Layer 2: Dirty Tracking & Invalidation

To maintain $O(\text{Dirty})$ performance across multiple ticks, the engine tracks state mutations via an immutable `DirtySet`.

### `DirtyDependencyGraph`
Because an action in one domain can subtly invalidate assumptions in another (e.g., an equipment change in inventory alters movement speed and combat ratings), the `DirtyDependencyGraph` formalizes downstream expansions.
- **Example Expansion**: When `DIRTY_INVENTORY` is flagged, the graph automatically expands the dirty footprint to flag `DIRTY_ATTRIBUTES` and `DIRTY_MOVEMENT`, guaranteeing that subsequent phases re-evaluate the entity's effective stats and locomotion speed.

### Centralized `CacheInvalidationPolicy`
Instead of scattered cache clearing logic across systems, `CacheInvalidationPolicy` subscribes to the expanded `DirtySet`.
- When `DIRTY_MOVEMENT` or `DIRTY_OCCUPANCY` is flagged for a region, spatial index grids and line-of-sight caches for that tile coordinate are instantly invalidated.
- When `DIRTY_ATTRIBUTES` is flagged, the entity's cached DTO projections in `ReadModelCache` are purged.

---

## 4. Layer 3: Compaction & Plan Precomputation

When hundreds of concurrent worker threads or complex system chains emit state updates, multiple updates frequently target the same entity within the same tick.

### `StateUpdateCompactor`
Before applying updates to the authoritative state, `StateUpdateCompactor` processes the raw collection.
- **No-Op Pruning**: Identifies singletons like `EMPTY_ENTITY_UPDATE` or zero-delta updates and prunes them instantly.
- **Field-Level Compaction**: Merges successive partial updates into a single concise update record, preventing redundant dataclass copying overhead during application.

### `ApplyPlanBuilder` and `ApplyPlan`
In legacy apply pipelines, applying updates required iterating through $O(N)$ world collections multiple times. The `ApplyPlanBuilder` precomputes an immutable `ApplyPlan` containing precise dictionary lookups and pre-sorted mutation lists.

### `ComponentPatch` Model
To decouple monolithic entity updates from brittle initialization logic, `ApplyPlan` decomposes updates into isolated `ComponentPatch` instances (e.g., `CombatPatch`, `InventoryPatch`, `BiologicalPatch`).
- Patches are sorted by execution dependency (e.g., equipment patches apply before combat stat recalculation patches).
- Patches directly mutate pre-allocated dictionary buffers in a single pass before a single fast object allocation reconstructs the immutable `EntityState`.

---

## 5. Layer 4: Projection & Memory Bounds

To prevent memory leaks and garbage collection pauses during multi-thousand tick runs, the engine bounds all read models and internal caches.

### `ReadModelCache`
API presentation endpoints and UI inspectors require complex JSON-serializable DTOs. `ReadModelCache` caches these projections. DTOs are only recomputed when an entity's ID appears in the active `DirtySet`.

### `OccupancySnapshot`
Spatial collision and priority resolution require checking tile occupancy thousands of times per tick. At the start of the Locomotion phase, the engine builds an immutable `OccupancySnapshot` mapping every $(X, Y)$ coordinate to an $O(1)$ lookup set of entity IDs and movement priorities.

### `MovementPlanCache`
Pathfinding across bilinear flow fields is computationally expensive. `MovementPlanCache` caches an entity's next step vector. If the entity's position, target coordinate, and local tile occupancy remain unchanged, pathfinding is bypassed entirely, yielding an immediate cache hit.

### `CacheRegistry` and `CacheBudgetPolicy`
All runtime optimization caches (`MovementPlanCache`, `ReadModelCache`, `WorldIndexService`) must register with the `CacheRegistry`.
- `CacheBudgetPolicy` enforces maximum item retention limits and tick-based FIFO/LRU eviction sweeps.
- **Target, not enforced as written:** this is meant to guarantee bounded memory (RSS) containment, eliminating unbounded heap growth during indefinite continuous simulations. The registry and budget classes exist; the bound itself is checked only by the long-run stability harness (`src/perf/long_run_harness.py`: RSS growth at most 2x or peak at most 512 MB), whose test is `slow`-marked and soft (`tests/certification/test_cert_long_run_stability.py`).

---

## 6. Layer 5: Adaptive Governance & Profiles

Simulation workloads vary wildly between scenarios (e.g., an intense 100-man battlefield vs. a peaceful 10,000-man trading metropolis).

### `OptimizationProfileResolver`
The engine dynamically resolves an `OptimizationProfile` defining scenario-tailored budgets. `src/config/optimization_profiles.py` defines six profiles plus a default (`COMBAT_HEAVY`, `MOVEMENT_HEAVY`, `RESOURCE_HEAVY`, `METROPOLIS`, `LOW_MEMORY`, `DEBUG_REFERENCE`, `DEFAULT_PROFILE`); the four below are described here, and `MOVEMENT_HEAVY`, `RESOURCE_HEAVY` and the default are not:
- **`COMBAT_HEAVY`**: Enforces strict, unthrottled candidate scanning for combat systems and disables optional phase skipping.
- **`METROPOLIS`**: Expands spatial query cache budgets while aggressively throttling routine strategic evaluations.
- **`LOW_MEMORY`**: Constrains cache retention limits and executes aggressive background sweeps to maintain tight memory envelopes.
- **`DEBUG_REFERENCE`**: Disables all unsafe narrowing, compaction, and phase skipping to provide a perfect determinism baseline.

### `PhaseDependencyGraph`
Rather than executing every refinement phase unconditionally, `PhaseDependencyGraph` inspects the expanded `DirtySet` at phase boundaries. If no dirty entities exist for an optional phase (e.g., no active raids or calamities for the Macro Threat phase), the phase is dynamically skipped, conserving substantial compute time. **Coverage caveat:** `PhaseDependencyGraph.PHASES` does not list every refinement phase, and `should_run_phase()` returns `True` for an unknown name, so phases absent from it run every tick with no cadence or dirty-set gating; see `docs/performance/phase_inventory.md` for the generated list and the differences, and `docs/engine/authoritative_pipeline.md` for the counted units (a "refinement phase" is one `run_phase()` call in `refine`). An earlier version of this section said "17 authoritative pipeline phases"; that count is obsolete.

### `PhaseBudgetGovernor`
**Runtime control (governor), not a measurement target.** The `PhaseBudgetGovernor` (`src/engine/phase_governor.py`) acts as an automated safety throttle. As implemented, it lowers candidate evaluation budgets, tightens scan policies to `EXACT_DIRTY`, and widens background sweep intervals from the previous tick's per-phase costs (`locomotion`, `final_integrity`) and, for compaction, when the previous tick's `tick_compute_ms` exceeds 80% of the profile's `max_tick_budget_ms` or work debt exceeds 70% of `max_work_debt`. The trigger is the latest tick, not a p95, and it is relative to the active profile's budget, not a fixed 50ms. These inputs are wall-clock readings; see `docs/engine/deterministic_execution.md` for how they are classified under the Canonical and Live bounded contracts. Crucially, the governor is architecturally prohibited from deferring correctness-critical tasks such as mortality processing, accepted resource transactions, or inventory weight constraints.

---

## 7. Performance Verification Parity

The optimization architecture is verified by the test suites cited in `docs/performance/optimization_invariants.md` (`tests/integration/optimization/` and others), which compare state hashes of optimized runs against full-scan reference runs. One cited suite, `tests/integration/optimization/test_degraded_mode_correctness.py`, does not exist; the degraded-mode correctness claim is covered only by `tests/unit/domains/optimization/test_phase_budget_governor.py` until it does. Parity claims rest on the proof digest, not on the fingerprint (PERF-D5).
