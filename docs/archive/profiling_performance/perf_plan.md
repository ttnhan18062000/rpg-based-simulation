# Milestone-Based High-Level Design

The roadmap below replaces “Epic” with **Milestone** and adds more implementation detail without going into actual code.

The guiding principle:

```text
Optimization must be a framework, not scattered faster functions.
```

The profiler shows the biggest costs are still systemic: `apply_generation`, `apply.py:replace`, movement routing, movement legality, and strategic evaluation. Movement spends heavy time in `apply_generation`, `apply.py:replace`, `_route_movement_intent`, `route_movement_intent`, and `resolve_move`; resource has the same pattern, with `_phase_resolution`, movement routing, `resolve_move`, `apply_generation`, and replacement churn dominating.

---

# Milestone 0 — Measurement and Profiling Foundation

## Purpose

Before optimizing more, make the measurement path trustworthy.

The current `BenchHarness` already reports compute TPS, wall-clock TPS, phase breakdown, memory, and whether replay/frame pacing are enabled. But the standalone `profiling_engine.py` still creates the kernel with only `audit_mode=False`, so cProfile runs may include replay/frame pacing/persistence noise depending on runtime behavior.

## Components to implement or update

### `ProfilingMode`

A small profiling configuration concept.

Modes:

```text
pure
runtime
audit
```

Behavior:

| Mode      | Purpose                               | Flags                                |
| --------- | ------------------------------------- | ------------------------------------ |
| `pure`    | Measure raw compute cost              | no replay, no frame pacing, no audit |
| `runtime` | Measure realistic production behavior | replay/frame pacing allowed          |
| `audit`   | Measure correctness-heavy execution   | audit on, frame pacing off           |

## Mechanism

The profiler should not just “run scenario and dump cProfile.” It should record:

```text
scenario name
entity count
requested ticks
completed ticks
early-exit reason
profile name
profiling mode
kernel flags
wall-clock duration
cProfile cumulative time
phase p50/p95/p99
RSS samples
GC counters
```

## Key implementation logic

1. Add a mode argument to the profiling harness.
2. Convert mode into kernel flags.
3. Store the chosen mode and flags in the text report.
4. Collect phase cost from runtime status, not only from cProfile.
5. Collect memory/GC data before making GC/memory stability claims.
6. Remove hot-path `print()` calls from engine systems; route them through debug logging or profiling metadata.

The current profiling report claims GC resilience and no memory fragmentation, but the uploaded report mostly shows scenario/cProfile data, not RSS/GC proof.

## Tests to add

```text
tests/unit/perf/test_profiling_harness_modes.py
tests/static/test_no_hot_path_prints.py
```

Test coverage:

```text
pure mode sets no_replay and no_frame_pacing
runtime mode allows replay/frame pacing
audit mode enables audit without frame pacing
profile report includes mode and flags
report cannot claim GC stability without GC/RSS metrics
no print() exists under engine/system hot paths
```

## Acceptance criteria

```text
[ ] cProfile pure mode excludes replay/frame pacing by configuration.
[ ] Profiling report includes mode and kernel flags.
[ ] RSS and GC metrics are recorded.
[ ] Hot-path print statements are removed.
[ ] Future optimization decisions use pure compute profile first.
```

---

# Milestone 1 — Optimization Truth Layer

## Purpose

Make optimized execution and full-scan reference execution share one consistent selection mechanism.

Right now, DirtySet exists and is meant to avoid O(N) scans. It tracks entity domains like movement, combat, inventory, strategic, social, lifecycle, biological, attributes, and world-object domains like groups, regions, resource nodes, buildings, chests, ground items, corpses, and camps.

The risk is that each phase can read DirtySet differently. That makes `force_full_scan` unreliable.

## Components to implement

### `CandidateSelector`

A central component that decides which entities a phase should process.

Responsibilities:

```text
understand force_full_scan
understand dirty_set missing fallback
map requested domains to DirtySet fields
return deterministic entity IDs
apply common filters like alive/active/include inactive
```

### `ScanPolicy`

A policy object or enum that describes how a phase wants to scan.

Possible policies:

```text
FULL_SCAN
DIRTY_ONLY
DIRTY_WITH_PERIODIC_SWEEP
TOP_K_DIRTY
BACKGROUND_SWEEP
```

## Mechanism

Every phase asks:

```text
CandidateSelector, give me entities relevant to these domains under this scan policy.
```

Instead of each phase doing:

```text
dirty_set.movement_entities | dirty_set.strategic_entities
```

## Candidate selection behavior

### Case 1 — `force_full_scan=True`

Return all phase-relevant entities.

This is the reference path. It must ignore DirtySet narrowing.

### Case 2 — `dirty_set is None`

Return all phase-relevant entities.

No DirtySet means unsafe to narrow.

### Case 3 — DirtySet exists

Return the union of requested domains.

Example:

```text
domains = movement + strategic

result =
    dirty_set.movement_entities
    union dirty_set.strategic_entities
```

### Case 4 — filtering

After candidate selection:

```text
remove inactive entities if phase does not process inactive
remove dead entities if phase requires alive entities
sort entity IDs deterministically
```

## Integration targets

Replace local candidate logic in:

```text
InteractionPhase
MovementPhase
StrategicIntelligenceSystem
ShopSystem
CapacityEnforcementPhase
Group/Lifecycle systems where applicable
```

## Tests to add

```text
tests/unit/optimization/test_candidate_selector.py
tests/integration/optimization/test_force_full_scan_phase_compliance.py
tests/static/test_no_direct_dirtyset_candidate_selection.py
```

Required tests:

```text
force_full_scan returns all entities even with empty DirtySet
missing DirtySet falls back to full scan
requested dirty domains are unioned correctly
unrequested domains are excluded
result ordering is deterministic
interaction phase respects force_full_scan
movement phase respects force_full_scan
strategic phase respects force_full_scan
shop/capacity phase respects force_full_scan
static guard blocks direct dirty_set candidate selection
```

## Acceptance criteria

```text
[ ] CandidateSelector owns entity selection.
[ ] DirtySet consumers no longer manually combine dirty fields.
[ ] force_full_scan is proven per optimized phase.
[ ] Full-scan parity tests become meaningful.
```

This is the highest-priority architectural milestone.

---

# Milestone 2 — Dirty Propagation Layer

## Purpose

DirtySet tells you what directly changed. It does not fully describe what must react.

Example:

```text
movement changed
```

should imply:

```text
movement candidate dirty
interaction candidate dirty
group/town/region candidate dirty
occupancy-related candidate dirty
```

Without this layer, downstream systems may miss required work.

## Component to implement

### `DirtyDependencyGraph`

A deterministic component that expands direct dirty domains into derived dirty domains.

Input:

```text
DirtySet from direct StateUpdate
```

Output:

```text
expanded DirtySet
```

## Mechanism

The dependency graph applies semantic rules.

### Movement rules

When movement is dirty:

```text
movement_entities stay dirty
strategic_entities may become dirty
town_entities may need recomputation
group-related candidates may need recomputation
interaction candidates may need recomputation
occupancy caches must be invalidated
```

### Inventory rules

When inventory is dirty:

```text
inventory_entities stay dirty
strategic_entities become dirty
capacity/shop/economy candidates become dirty
quest/reward logic may need reaction
```

### Combat rules

When combat is dirty:

```text
combat_entities stay dirty
lifecycle_entities become dirty
strategic_entities become dirty
social/group consequences may need reaction
corpse/loot generation may be affected
```

### Resource node rules

When resource nodes are dirty:

```text
resource_node_ids stay dirty
resource interaction candidates may need reaction
active node index must be invalidated
```

## Important behavior

Dirty expansion must be:

```text
deterministic
idempotent
cheap
side-effect free
```

Idempotent means:

```text
expanding twice gives the same result as expanding once
```

## Integration point

Use it inside the pipeline dirty refresh path.

Current pipeline already refreshes DirtySet at multiple points and has special force-full-scan behavior. The new flow should become:

```text
build direct dirty set
expand through DirtyDependencyGraph
attach expanded dirty set to StateUpdate
```

## Tests to add

```text
tests/unit/optimization/test_dirty_dependency_graph.py
tests/integration/optimization/test_dirty_dependency_pipeline.py
```

Required tests:

```text
movement expands to interaction/group/town-related domains
inventory expands to capacity/shop/strategic domains
combat expands to lifecycle/strategic/social domains
resource-node dirty invalidates resource interaction/index domains
corpse/ground-item dirty marks interaction/loot domains
expansion is deterministic
expansion is idempotent
pipeline uses expanded dirty set before downstream phases
```

## Acceptance criteria

```text
[ ] Dirty dependencies are explicit.
[ ] Downstream systems do not hide dependency rules locally.
[ ] Dirty expansion is tested independently.
[ ] Dirty expansion is applied in pipeline refresh.
```

---

# Milestone 3 — StateUpdate Compaction and Apply Work Reduction

## Purpose

Attack the largest cross-scenario bottleneck: ApplyPath and replacement churn.

Profiling shows `apply_generation`, `apply.py:replace`, and dataclass replacement are among the largest costs in both movement and resource scenarios.

## Components to implement

### `StateUpdateCompactor`

A pre-ApplyPath component that reduces noisy updates.

### `CompactionMetrics`

A lightweight metrics structure that records what compaction changed.

Suggested metrics:

```text
raw_entity_updates
compacted_entity_updates
dropped_empty_entity_updates
dropped_zero_delta_updates
dropped_equal_property_updates
merged_entity_updates
raw_world_updates
compacted_world_updates
```

### Optional later component: `ApplyWorkPlan`

A prepared internal representation for ApplyPath.

It would group updates by component type:

```text
navigation updates
combat updates
inventory updates
strategic updates
world-object updates
```

This should come after compaction, not before.

## Mechanism

The compactor receives:

```text
current state
raw StateUpdate
```

It produces:

```text
semantically equivalent smaller StateUpdate
metrics
```

## Compaction rules

### Entity update rules

Drop:

```text
empty EntityUpdate
zero-delta combat update
zero-delta stamina/biological update
property update equal to current state
inventory update with no item/gold delta
navigation update that does not change target/path/position
```

Merge:

```text
multiple deltas for same entity and same component
compatible combat deltas
compatible stamina deltas
compatible inventory deltas
```

Preserve:

```text
resource transfer intent
order-sensitive updates
intent results
transaction traces in audit mode
quest reward state transitions
lifecycle/death transitions
```

### World-object update rules

Drop:

```text
node update with no charge/cooldown change
building update with no meaningful delta
add/remove pair that cancels out
duplicate identical add/update
```

Preserve:

```text
anything with transaction/audit meaning
anything that changes ownership, availability, rewards, lifecycle, or identity
```

## Integration point

Before ApplyPath:

```text
pipeline produces update
StateUpdateCompactor compacts update
ApplyPath applies compacted update
metrics are attached to runtime status or benchmark result
```

## Tests to add

```text
tests/unit/optimization/test_state_update_compactor.py
tests/integration/optimization/test_compacted_apply_parity.py
tests/perf/test_apply_compaction_perf.py
```

Required tests:

```text
drops empty entity update
drops zero-delta combat update
preserves non-zero combat update
drops equal property update
preserves changed property update
drops no-op inventory update
preserves resource transfer intent
preserves lifecycle/death transition
preserves quest reward transition
compacted and uncompacted updates produce same final fingerprint
compaction reduces update count in movement/resource scenarios
apply_generation does not regress
```

## Acceptance criteria

```text
[ ] Compacted update is semantically equivalent to raw update.
[ ] Update count decreases in movement/resource.
[ ] ApplyPath replacement count decreases.
[ ] Benchmark output includes compaction metrics.
```

This milestone should produce the first major performance win.

---

# Milestone 4 — Movement Candidate Reduction

## Purpose

Reduce how many entities enter movement routing.

The movement and resource profiles show movement routing and `resolve_move` are major costs. Resource is especially heavy because workers continuously move toward nodes while also interacting.

## Components to implement

### `MovementCandidateSelector`

A movement-specific filter that runs after `CandidateSelector`.

`CandidateSelector` answers:

```text
which entities are relevant to this phase?
```

`MovementCandidateSelector` answers:

```text
which of those actually need movement work?
```

## Mechanism

Input:

```text
state
current update
candidate IDs from CandidateSelector
force_full_scan flag
```

Output:

```text
deterministic tuple of entity IDs that need movement routing
```

## Skip rules

Skip entity when:

```text
entity has no navigation target
entity already reached target
entity is dead
entity is inactive
entity has insufficient readiness/stamina
entity is currently locked by interaction/channeling
entity is not movement-dirty and no target/occupancy condition changed
```

## Include rules

Include entity when:

```text
force_full_scan and entity is movable
target changed
movement dirty
interaction requires moving closer
strategic project requires reaching target
current/next tile affected by occupancy changes
```

## Integration point

Movement phase should become:

```text
CandidateSelector gets broad movement-related candidates
MovementCandidateSelector filters true movement work
Movement routing processes only filtered candidates
```

## Tests to add

```text
tests/unit/optimization/test_movement_candidate_selector.py
tests/integration/optimization/test_movement_candidate_integration.py
tests/perf/test_movement_candidate_perf.py
```

Required tests:

```text
skips entity without target
skips entity already at target
skips dead entity
skips inactive entity
skips insufficient-readiness entity
includes movable entity with target
includes entity when target changed
force_full_scan includes all movable entities
result is deterministic
movement final state matches full-scan reference
movement candidate count is lower than total entity count
```

## Acceptance criteria

```text
[ ] Movement routing receives fewer candidates.
[ ] force_full_scan still checks all movable entities.
[ ] Optimized movement matches full-scan reference.
[ ] resolve_move call count decreases.
[ ] verify_movement_legality call count decreases.
```

---

# Milestone 5 — Occupancy Snapshot and Movement Legality Stabilization

## Purpose

Simplify and stabilize repeated movement legality queries.

Occupancy lookup itself is not the biggest bottleneck; the report claims O(1) occupancy timing is low, and raw data shows bigger costs elsewhere. The problem is that movement legality repeatedly asks related questions through layered services.

## Components to implement

### `OccupancySnapshot`

A per-tick immutable read model for movement legality.

Fields/concepts:

```text
tick
occupancy_by_tile
priority_by_entity
entity_by_tile
engaged_hostiles_by_tile if needed
occupancy version
```

### `OccupancySnapshotBuilder`

Builds the snapshot once per tick or once per resolution phase.

## Mechanism

At phase start:

```text
scan active entities once
build tile occupancy map
build priority lookup
build optional engagement lookup
freeze snapshot for current tick
```

Movement legality then reads from the snapshot instead of repeatedly deriving occupancy data.

## Important behavior

The snapshot is:

```text
immutable during one tick
rebuilt after ApplyPath advances state
not updated mid-phase unless explicitly designed
deterministic
```

## Integration targets

```text
movement legality
position swap resolution
occupancy conflict resolution
engaged-hostile lookup if hot
```

## Tests to add

```text
tests/unit/optimization/test_occupancy_snapshot.py
tests/integration/optimization/test_occupancy_snapshot_movement_parity.py
```

Required tests:

```text
snapshot contains active entity positions
occupied tile returns occupant
empty tile returns none
snapshot remains stable during tick
snapshot rebuilds after movement apply
snapshot-based legality matches current legality
position swap behavior matches previous behavior
```

## Acceptance criteria

```text
[ ] Movement legality can use snapshot.
[ ] Snapshot result matches current state semantics.
[ ] Snapshot does not mutate during tick.
[ ] Movement parity remains stable.
```

---

# Milestone 6 — Movement Plan Cache

## Purpose

Cache repeated next-step decisions only after candidate reduction is proven.

This is lower priority than `MovementCandidateSelector`. Plan caching can easily become wrong if invalidation is weak.

## Components to implement

### `MovementPlanCache`

A cache for entity next-step decisions.

### `MovementPlanKey`

Key should include:

```text
entity id
current tile
target tile
movement mode
occupancy version
terrain/passability version if available
```

### `MovementPlan`

Stored value:

```text
next step
created tick
valid until tick
reason/source metadata for debugging
```

## Mechanism

Before resolving movement:

```text
build key
check cache
if hit and still valid -> use cached next step
if miss -> compute next step and store plan
```

## Invalidation rules

Invalidate when:

```text
entity moves
target changes
occupancy version changes
terrain/passability changes
entity becomes blocked
movement mode changes
```

## Tests to add

```text
tests/unit/optimization/test_movement_plan_cache.py
tests/integration/optimization/test_movement_plan_cache_parity.py
```

Required tests:

```text
reuses plan when key unchanged
invalidates when entity moves
invalidates when target changes
invalidates when occupancy version changes
does not reuse blocked step
cached movement equals uncached movement
cache hit/miss metrics are recorded
```

## Acceptance criteria

```text
[ ] Cache never changes movement semantics.
[ ] Cache invalidation is conservative.
[ ] Movement plan hit rate is measurable.
[ ] Movement profile improves only after parity passes.
```

---

# Milestone 7 — Cache Invalidation Policy

## Purpose

Centralize cache invalidation before adding more indexes.

Without this, each cache will invent its own invalidation rules and stale-cache bugs will multiply.

## Component to implement

### `CacheInvalidationPolicy`

Input:

```text
DirtySet
```

Output:

```text
set of invalidated index/cache names
```

## Mechanism

Mapping examples:

```text
movement_entities
    -> occupancy_snapshot
    -> entity_position_index
    -> movement_plan_cache

resource_node_ids
    -> active_resource_node_index

building_ids
    -> building_kind_index

ground_item_ids
    -> ground_item_index

corpse_ids
    -> corpse_index

region_ids
    -> region_lookup_index

camp_ids
    -> camp_index
```

## Important behavior

Invalidation must be:

```text
centralized
conservative
deterministic
observable
```

Conservative means it is better to invalidate too much than too little.

## Tests to add

```text
tests/unit/optimization/test_cache_invalidation_policy.py
```

Required tests:

```text
resource node dirty invalidates resource index
building dirty invalidates building index
movement dirty invalidates occupancy and movement plan cache
ground item dirty invalidates loot index
corpse dirty invalidates corpse index
region dirty invalidates region index
empty DirtySet invalidates nothing
combined DirtySet invalidates union of indexes
```

## Acceptance criteria

```text
[ ] No cache owns private invalidation rules.
[ ] All index services use CacheInvalidationPolicy.
[ ] Invalidation behavior is tested independently.
```

---

# Milestone 8 — World Index and Spatial Query Service

## Purpose

Replace ad-hoc caches with a real index/query layer.

The current system already has cache-like behavior in places, but attaching hidden caches directly to state/scorers is not a scalable long-term mechanism. The goal is not “make one scorer faster.” The goal is to make spatial/world queries consistent and invalidation-safe.

## Components to implement

### `WorldIndexService`

Owns reusable indexes.

Index groups:

```text
active resource nodes by bucket
buildings by kind
entities by tile
ground items by tile
corpses by tile
regions by tile or bounds
camps by region/tile
```

### `WorldIndexes`

Immutable bundle of indexes for a tick/version.

Concepts:

```text
tick
version
index groups
source dirty version
```

### `SpatialQueryService`

Provides gameplay queries:

```text
nearest resource node
nearest building by kind
nearby entities
nearby ground items
nearby corpses
entities in region
```

## Mechanism

`WorldIndexService`:

```text
receives state + dirty set
asks CacheInvalidationPolicy what changed
reuses unchanged index groups
rebuilds invalidated index groups
returns immutable WorldIndexes
```

`SpatialQueryService`:

```text
uses WorldIndexes
checks nearby buckets first
computes exact distance for candidates
uses deterministic tie-breaking
falls back to naive scan only in debug/reference mode
```

## Integration targets

```text
HarvestScorer
SleepScorer
EatScorer
InteractionPhase
LootAction
HarvestAction
Group formation
Town/shop lookup
```

## Tests to add

```text
tests/unit/optimization/test_world_index_service.py
tests/unit/optimization/test_spatial_query_service.py
tests/integration/optimization/test_spatial_query_integration.py
tests/perf/test_world_index_perf.py
```

Required tests:

```text
builds active resource-node index
excludes depleted resource nodes
builds building-by-kind index
reuses same-tick unchanged indexes
invalidates resource index when resource node dirty
invalidates building index when building dirty
nearest resource query matches naive scan
nearest building query matches naive scan
nearby entity query matches naive scan
tie-breaking is deterministic
scorers no longer attach hidden caches to state
```

## Acceptance criteria

```text
[ ] World queries match naive reference.
[ ] Index reuse is observable.
[ ] Index invalidation follows DirtySet domains.
[ ] Scorers/systems use SpatialQueryService instead of local scans/caches.
```

---

# Milestone 9 — Strategic Work Queue

## Purpose

Reduce strategic evaluation cost without starving important entities.

Strategic evaluation is not the largest bottleneck, but it is consistently visible across profiles. Movement shows `fused_strategic_pass` and `evaluate_strategic_intent` as significant costs.

## Component to implement

### `StrategicWorkQueue`

Builds the ordered list of entities that need strategic work this tick.

## Mechanism

Inputs:

```text
state
current update
expanded DirtySet
strategic budget
current tick
```

Output:

```text
ordered entity IDs
```

Priority groups:

```text
failed action/path
unresolved blockers
active project transition
biological emergency
contract expiration
dirty strategic entities
background sweep sample
```

## Important rules

```text
urgent entities bypass normal cadence
routine entities respect budget
background sweep prevents starvation
force_full_scan returns all strategic entities
result ordering is deterministic
```

## Integration point

Inside `fused_strategic_pass`, replace broad candidate generation with queue output.

## Tests to add

```text
tests/unit/optimization/test_strategic_work_queue.py
tests/integration/optimization/test_strategic_queue_integration.py
tests/perf/test_strategic_queue_perf.py
```

Required tests:

```text
failed action entity is prioritized
unresolved blocker is prioritized
biological emergency is prioritized
dirty strategic entity is included
budget is respected
background sweep prevents starvation
force_full_scan includes all strategic entities
strategic candidate count decreases
strategic final state remains stable or divergence is documented
```

## Acceptance criteria

```text
[ ] Strategic work is priority-driven.
[ ] Urgent entities are not delayed by cadence.
[ ] Background sweep prevents starvation.
[ ] Strategic candidate count becomes observable.
```

---

# Milestone 10 — Optimization Observability

## Purpose

Make it obvious whether an optimization actually reduced work.

Do not only report tick time. Tick time tells you the symptom, not the cause.

## Metrics to add

```text
candidate_selector_full_scan_count
candidate_selector_dirty_count
movement_candidate_count
movement_skipped_no_target_count
movement_skipped_at_target_count
strategic_candidate_count
strategic_urgent_count
raw_entity_update_count
compacted_entity_update_count
dropped_noop_update_count
world_index_cache_hits
world_index_cache_misses
movement_plan_cache_hits
movement_plan_cache_misses
apply_generation_ms
movement_resolution_ms
strategic_pass_ms
```

## Integration targets

```text
PressureSignals
BenchHarness result
profiling report
perf regression baseline
```

The existing benchmark result already includes compute TPS, wall-clock TPS, phase breakdown, replay/frame-pacing flags, and memory fields, so this milestone extends that structure rather than replacing it.

## Tests to add

```text
tests/unit/perf/test_optimization_metrics_schema.py
tests/perf/test_optimization_metrics_present.py
```

Required tests:

```text
benchmark result includes optimization metrics
metrics are zero/default when feature disabled
metrics are nonzero in relevant scenario
schema is stable
```

## Acceptance criteria

```text
[ ] Every optimization exposes before/after work metrics.
[ ] Perf report explains why time changed.
[ ] Regression gate can compare optimization metrics.
```

---

# Milestone 11 — Performance Regression Gate

## Purpose

Prevent future changes from regressing performance.

Current perf tests already assert some thresholds and save reports through fixtures. But you need a formal gate comparing current results with committed baselines.

## Component to implement

### `PerfRegressionGate`

Compares current benchmark result with baseline.

## Metrics to compare

```text
p95_tick_compute_ms
p99_tick_compute_ms
phase p95
memory_delta_mb
peak_rss_mb
compute_tps
raw_entity_update_count
compacted_entity_update_count
movement_candidate_count
strategic_candidate_count
cache hit/miss rates
```

## Regression rules

For latency:

```text
current must not exceed baseline by relative threshold or absolute threshold
```

For throughput:

```text
compute_tps must not drop beyond allowed threshold
```

For memory:

```text
peak RSS and memory delta must not exceed threshold
```

For CI:

```text
missing baseline is failure
```

For local:

```text
missing baseline can warn or skip
```

## Tests to add

```text
tests/unit/perf/test_perf_regression_gate.py
tests/perf/test_perf_baseline_ci_behavior.py
```

Required tests:

```text
passes within threshold
fails when p95 regresses
fails when phase p95 regresses
fails when memory regresses
fails when compute_tps drops
ignores wall_clock_tps for compute regression
missing baseline fails in CI mode
missing baseline warns/skips in local mode
```

## Acceptance criteria

```text
[ ] CI cannot silently skip performance baseline.
[ ] Gate compares compute metrics, not wall-clock metrics.
[ ] Phase-level regression is enforced.
[ ] Memory regression is enforced.
[ ] Optimization work-shape metrics are enforced.
```

---

# Milestone 12 — Read Model / API Projection Optimization

## Purpose

Avoid expensive full-state projection for API/UI paths.

The engine manager already stores a minimal latest snapshot and only builds full snapshots on demand, which is the right direction. The next step is a formal read model cache.

## Components to implement

### `ReadModelCache`

Caches API-facing data:

```text
minimal world summary
entity summary by id
paged entity list
entity detail DTO
full inspect snapshot only on demand
```

### `ReadModelInvalidationPolicy`

Uses DirtySet to invalidate only affected DTOs/pages.

## Mechanism

On every tick:

```text
update minimal summary
invalidate affected entity DTOs by DirtySet
invalidate affected pages only if entity order/page membership changed
do not rebuild full snapshot unless requested
```

## Tests to add

```text
tests/unit/api/test_read_model_cache.py
tests/perf/test_api_projection_perf.py
```

Required tests:

```text
minimal snapshot is cheap and does not scan all entities
single entity dirty invalidates only that entity DTO
paged retrieval does not rebuild all entity DTOs
full snapshot is generated only on demand
API projection performance does not regress
```

## Acceptance criteria

```text
[ ] UI/API does not force full-state projection per tick.
[ ] DirtySet drives DTO invalidation.
[ ] Minimal snapshot remains O(1)-like.
[ ] Full inspect remains available but explicitly expensive.
```

---

# Recommended Milestone Order

Use this order:

```text
0. Measurement and Profiling Foundation
1. Optimization Truth Layer
2. Dirty Propagation Layer
3. StateUpdate Compaction and Apply Work Reduction
4. Movement Candidate Reduction
5. Occupancy Snapshot and Movement Legality Stabilization
6. Movement Plan Cache
7. Cache Invalidation Policy
8. World Index and Spatial Query Service
9. Strategic Work Queue
10. Optimization Observability
11. Performance Regression Gate
12. Read Model / API Projection Optimization
```

The minimum useful implementation slice is:

```text
Milestone 0
Milestone 1
Milestone 3
Milestone 4
Milestone 10
Milestone 11
```

That gives you:

```text
clean measurement
truthful reference path
less apply churn
less movement work
metrics proving the reduction
regression protection
```

---

# What not to do first

Do not start with `WorldIndexService`.

It is important, but the measured hottest cost is ApplyPath/update churn and movement routing, not nearest-node lookup.

Do not start with `MovementPlanCache`.

Plan caching is fragile. First reduce the candidate set, then cache the remaining expensive decisions.

Do not start with more concurrency.

The engine is doing too much work. Parallelizing unnecessary work is not the right first move.

---

# Priority Plan

## Immediate next milestones

```text
1. Measurement and Profiling Foundation
2. Optimization Truth Layer
3. StateUpdate Compaction
4. Movement Candidate Reduction
```

## Key design shift

Move from:

```text
each system optimizes itself
```

to:

```text
central selection
central dirty propagation
central compaction
central invalidation
central measurement
```

## Expected outcome

After these milestones, the engine should be able to prove:

```text
optimized path == full reference path
candidate count is lower
update count is lower
ApplyPath replacement cost is lower
movement resolution cost is lower
performance regression is guarded
```

That is a stronger and cleaner architecture than patching the current solution one function at a time.
