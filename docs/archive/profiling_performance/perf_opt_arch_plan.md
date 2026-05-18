# Implementation Plan — Performance Optimization Architecture

The correct target is **not** “make current code faster.” The target is:

```text
select less work
scan less state
generate fewer updates
apply fewer replacements
prove semantic equivalence
then measure performance
```

The profiling data clearly shows `apply_generation`, `apply.py:replace`, movement routing, movement legality, and strategic intelligence are the expensive areas. In the movement profile, `apply_generation` takes about `54.664s`, `apply.py:replace` takes about `33.949s`, movement routing takes about `23.014s`, and `resolve_move` takes about `21.074s` across 500 ticks.

---

# Milestone 0 — Profiling and Safety Cleanup

## Purpose

Before adding new optimization mechanisms, clean the measurement environment and remove profiling noise.

Your `BenchHarness` already defaults to `no_replay=True` and `no_frame_pacing=True`, which is correct for compute benchmarking. But `profiling_engine.py` currently creates `Kernel(..., flags={"audit_mode": False})`, so cProfile runs can still include replay/frame pacing noise depending on defaults/profile behavior.

There is also a hot-path `print()` inside final integrity breakdown logic. That pollutes benchmarks and must not stay in engine code.

## Implementation tasks

### M0.1 Add profiling modes

Update `profiling_engine.py`.

Create enum/string modes:

```python
class ProfilingMode:
    PURE = "pure"
    RUNTIME = "runtime"
    AUDIT = "audit"
```

Flag mapping:

```python
PROFILE_FLAGS = {
    "pure": {
        "audit_mode": False,
        "no_replay": True,
        "no_frame_pacing": True,
    },
    "runtime": {
        "audit_mode": False,
        "no_replay": False,
        "no_frame_pacing": False,
    },
    "audit": {
        "audit_mode": True,
        "no_replay": False,
        "no_frame_pacing": True,
    },
}
```

CLI:

```bash
python profiling_engine.py --scenario movement --entities 1000 --ticks 500 --mode pure
```

### M0.2 Add profiling output metadata

Each generated report should include:

```text
scenario
entity_count
ticks_requested
ticks_completed
early_exit_reason
mode
kernel_flags
profile_name
wall_clock_s
cProfile_total_s
phase_cost_summary
```

### M0.3 Add RSS and GC sampling

Add optional per-tick sampling:

```python
rss_mb_by_tick: list[float]
gc_count_by_tick: list[tuple[int, int, int]]
```

This is necessary because the current report makes GC/memory stability claims, but cProfile alone does not prove GC resilience or memory fragmentation stability. The report explicitly claims GC resilience and no memory fragmentation, but the provided artifacts are mostly cProfile data and scenario summaries.

### M0.4 Remove hot-path print

Replace:

```python
print(f"[Tick {state.tick}] final_integrity breakdown...")
```

with:

```python
logger.debug(...)
```

guarded by a profile/audit debug flag.

## New tests

```text
tests/unit/perf/test_profiling_harness_modes.py
tests/static/test_no_hot_path_prints.py
```

Tests:

```python
def test_profiling_pure_mode_sets_clean_compute_flags():
    ...

def test_profiling_runtime_mode_allows_replay_and_frame_pacing():
    ...

def test_profiling_audit_mode_enables_audit_without_frame_pacing():
    ...

def test_profile_output_includes_mode_and_flags():
    ...

def test_profile_report_does_not_claim_gc_resilience_without_gc_metrics():
    ...

def test_no_hot_path_prints_in_engine_or_systems():
    ...
```

## Acceptance criteria

```text
[ ] pure profile has no replay/frame pacing by configuration
[ ] runtime profile is clearly labeled
[ ] audit profile is clearly labeled
[ ] report includes mode and flags
[ ] RSS and GC metrics exist before memory/GC claims are made
[ ] no hot-path print remains under src/engine or src/systems
```

---

# Milestone 1 — CandidateSelector / ScanPolicy

## What this class is

`CandidateSelector` is the central component that decides **which entities a phase should process**.

Right now, different systems can read `update.dirty_set` directly and each phase can accidentally implement different narrowing rules. That is bad architecture. It makes `force_full_scan` unreliable.

`DirtySet` already tracks multiple entity domains such as movement, combat, inventory, strategic, social, lifecycle, town, biological, and attributes, plus world-object domains like groups, regions, resource nodes, buildings, chests, ground items, corpses, and camps.

## Class to implement

File:

```text
src/engine/optimization/candidate_selector.py
```

Class:

```python
class CandidateSelector:
    @staticmethod
    def entities(
        state: AuthoritativeState,
        update: StateUpdate,
        domains: set[str],
        *,
        include_inactive: bool = False,
        require_alive: bool = False,
    ) -> tuple[int, ...]:
        ...
```

## High-level logic

```text
if update.force_full_scan:
    candidates = all state.entities

elif update.dirty_set is None:
    candidates = all state.entities

else:
    candidates = union of requested DirtySet domains

then filter:
    include_inactive=False -> remove inactive entities
    require_alive=True -> remove dead entities

return deterministic sorted tuple
```

Domain mapping:

```python
DOMAIN_TO_DIRTY_FIELD = {
    "movement": "movement_entities",
    "combat": "combat_entities",
    "inventory": "inventory_entities",
    "strategic": "strategic_entities",
    "social": "social_entities",
    "lifecycle": "lifecycle_entities",
    "town": "town_entities",
    "biological": "biological_entities",
    "attribute": "attribute_entities",
}
```

## Where to integrate

Replace direct DirtySet candidate narrowing in:

```text
InteractionPhase
MovementPhase
StrategicIntelligenceSystem
GroupPhase
ShopSystem
CapacityEnforcementPhase
LifecycleSystem if it uses narrowed candidates
```

## New tests

```text
tests/unit/optimization/test_candidate_selector.py
tests/integration/optimization/test_force_full_scan_phase_compliance.py
tests/static/test_no_direct_dirtyset_candidate_selection.py
```

Tests:

```python
def test_candidate_selector_returns_all_entities_when_force_full_scan():
    ...

def test_candidate_selector_returns_all_entities_when_dirty_set_missing():
    ...

def test_candidate_selector_unions_requested_dirty_domains():
    ...

def test_candidate_selector_does_not_include_unrequested_domains():
    ...

def test_candidate_selector_filters_inactive_when_requested():
    ...

def test_candidate_selector_filters_dead_when_requested():
    ...

def test_candidate_selector_result_is_deterministic():
    ...
```

Phase compliance:

```python
def test_interaction_phase_force_full_scan_processes_entity_with_empty_dirty_set():
    ...

def test_movement_phase_force_full_scan_processes_entity_with_target_and_empty_dirty_set():
    ...

def test_strategic_phase_force_full_scan_processes_active_project_entity_with_empty_dirty_set():
    ...

def test_shop_phase_force_full_scan_processes_inventory_entity_with_empty_dirty_set():
    ...

def test_capacity_phase_force_full_scan_processes_all_inventory_entities():
    ...
```

Static guard:

```python
def test_no_direct_dirtyset_candidate_selection_outside_candidate_selector():
    ...
```

## Acceptance criteria

```text
[ ] CandidateSelector exists
[ ] force_full_scan ignores DirtySet narrowing
[ ] dirty_set=None falls back to full scan
[ ] all optimized phases use CandidateSelector
[ ] direct dirty_set candidate narrowing is banned outside approved files
[ ] full-scan parity tests become meaningful
```

---

# Milestone 2 — DirtyDependencyGraph

## What this class is

`DirtyDependencyGraph` expands **direct dirtiness** into **derived dirtiness**.

Example:

```text
entity moved
```

should imply:

```text
movement dirty
interaction dirty
group dirty
town/region membership dirty
occupancy dirty
```

Without this, a phase can update one domain and downstream systems may not run because they are looking at a narrower DirtySet.

## Class to implement

File:

```text
src/engine/optimization/dirty_dependency_graph.py
```

Class:

```python
class DirtyDependencyGraph:
    @staticmethod
    def expand(dirty: DirtySet) -> DirtySet:
        ...
```

## High-level dependency rules

### Movement dependency

```text
movement_entities
    -> movement_entities
    -> strategic_entities
    -> town_entities
    -> lifecycle_entities if movement can trigger hazards
```

### Inventory dependency

```text
inventory_entities
    -> inventory_entities
    -> strategic_entities
    -> town_entities
```

Reason: inventory affects capacity, shop, quest rewards, strategic blockers.

### Combat dependency

```text
combat_entities
    -> combat_entities
    -> lifecycle_entities
    -> strategic_entities
    -> social_entities
```

Reason: damage/death affects lifecycle, quests, group behavior, reputation/social memory.

### Resource node dependency

```text
resource_node_ids
    -> resource_node_ids
```

Additionally, it should mark a global “resource interaction candidate domain” or invalidate world indexes later.

### Corpse / ground item dependency

```text
corpse_ids / ground_item_ids
    -> interaction candidates
    -> inventory candidates
```

## Implementation detail

Do not mutate existing DirtySet. Return a new one.

Dirty expansion must be:

```text
deterministic
idempotent
cheap
```

Idempotent means:

```python
expand(expand(dirty)) == expand(dirty)
```

## Where to integrate

Current `_refresh_dirty_set()` builds/refreshes DirtySet and has special `force_full_scan` handling. Add expansion there:

```python
new_dirty = DirtySet.from_update(state, update, base_dirty=update.dirty_set)
expanded = DirtyDependencyGraph.expand(new_dirty)
return update.replace(dirty_set=expanded)
```

For `force_full_scan=True`, expansion is unnecessary because all entity domains are already full.

## New tests

```text
tests/unit/optimization/test_dirty_dependency_graph.py
tests/integration/optimization/test_dirty_dependency_pipeline.py
```

Tests:

```python
def test_dirty_dependency_movement_marks_interaction_group_and_town():
    ...

def test_dirty_dependency_inventory_marks_capacity_shop_and_strategic():
    ...

def test_dirty_dependency_combat_marks_lifecycle_and_strategic():
    ...

def test_dirty_dependency_resource_node_invalidates_resource_domain():
    ...

def test_dirty_dependency_corpse_marks_interaction_domain():
    ...

def test_dirty_dependency_expansion_is_idempotent():
    ...

def test_dirty_dependency_expansion_is_deterministic():
    ...
```

## Acceptance criteria

```text
[ ] dependency expansion is centralized
[ ] expansion is idempotent
[ ] expansion is deterministic
[ ] pipeline refresh uses expanded dirty set
[ ] downstream systems no longer guess dependent domains locally
```

---

# Milestone 3 — StateUpdateCompactor

## What this class is

`StateUpdateCompactor` reduces noisy updates before `ApplyPath`.

This is the highest-value implementation after CandidateSelector. The profile shows `ApplyPath` and replacement churn dominate across scenarios. `ApplyPath.apply_generation` and custom `replace()` are central to the current apply pipeline.

## Class to implement

File:

```text
src/engine/optimization/state_update_compactor.py
```

Classes:

```python
@dataclass(frozen=True)
class CompactionMetrics:
    raw_entity_updates: int
    compacted_entity_updates: int
    dropped_empty_entity_updates: int
    dropped_zero_delta_updates: int
    dropped_equal_property_updates: int
    merged_entity_updates: int
    raw_world_updates: int
    compacted_world_updates: int


class StateUpdateCompactor:
    @staticmethod
    def compact(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        ...

    @staticmethod
    def compact_with_metrics(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> tuple[StateUpdate, CompactionMetrics]:
        ...
```

## High-level logic

For each `EntityUpdate`:

```text
1. remove empty component updates
2. remove zero-delta component updates
3. remove property_updates that equal current entity value
4. collapse repeated deltas if updates are represented as lists or have already been merged
5. preserve non-commutative operations
6. drop EntityUpdate if nothing remains
```

World update compaction:

```text
groups add then remove same id -> remove both if no final effect
ground item add then remove same id -> remove both
corpse add then remove same id -> remove both
node update with zero charge/cooldown delta -> drop
building update with no inventory/gold change -> drop
```

## Where to integrate

In `Kernel._phase_advancement()` or immediately before `ApplyPath.apply_generation()`:

```python
if self._enable_update_compaction:
    update, metrics = StateUpdateCompactor.compact_with_metrics(self._state, update)
    self._last_compaction_metrics = metrics

self._state = ApplyPath.apply_generation(...)
```

Add flag:

```python
flags={
    "enable_update_compaction": True
}
```

Default:

```text
on for benchmark/prod after parity proves it
off available for reference testing
```

## New tests

```text
tests/unit/optimization/test_state_update_compactor.py
tests/integration/optimization/test_compacted_apply_parity.py
tests/perf/test_apply_compaction_perf.py
```

Unit tests:

```python
def test_compactor_drops_empty_entity_update():
    ...

def test_compactor_drops_zero_delta_combat_update():
    ...

def test_compactor_preserves_nonzero_combat_update():
    ...

def test_compactor_drops_property_update_equal_to_current_value():
    ...

def test_compactor_preserves_property_update_that_changes_value():
    ...

def test_compactor_drops_zero_delta_stamina_update():
    ...

def test_compactor_preserves_resource_transfer_intent():
    ...

def test_compactor_preserves_order_sensitive_updates():
    ...

def test_compactor_reports_reduction_metrics():
    ...
```

Parity tests:

```python
def test_compacted_update_applies_same_as_uncompacted_update_single_entity():
    ...

def test_compacted_update_applies_same_as_uncompacted_update_resource_scenario():
    ...

def test_compacted_update_applies_same_as_uncompacted_update_movement_scenario():
    ...
```

Perf tests:

```python
@pytest.mark.perf
def test_compactor_reduces_entity_update_count_in_movement_1000():
    ...

@pytest.mark.perf
def test_compactor_reduces_apply_generation_time_in_resource_smoke():
    ...
```

## Acceptance criteria

```text
[ ] compacted update produces same final fingerprint as uncompacted update
[ ] raw update count > compacted update count in movement/resource scenarios
[ ] apply_generation p95 decreases or does not regress
[ ] no order-sensitive update is dropped
[ ] compaction metrics appear in benchmark result
```

---

# Milestone 4 — MovementCandidateSelector

## What this class is

`MovementCandidateSelector` narrows the entity set further after `CandidateSelector`.

`CandidateSelector` answers:

```text
which entities are dirty/relevant for this phase?
```

`MovementCandidateSelector` answers:

```text
which of those actually need movement routing?
```

Movement routing is one of the biggest measured costs. In movement profiling, `_route_movement_intent`, `route_movement_intent`, `resolve_move`, and movement legality are major hotspots.

## Class to implement

File:

```text
src/engine/optimization/movement_candidate_selector.py
```

Class:

```python
class MovementCandidateSelector:
    @staticmethod
    def select(
        state: AuthoritativeState,
        update: StateUpdate,
        candidate_ids: Iterable[int],
        *,
        force_full_scan: bool = False,
    ) -> tuple[int, ...]:
        ...
```

## High-level logic

Skip entity if:

```text
entity missing
entity inactive
entity dead
navigation target is None
already at target
readiness/stamina cannot move
entity has blocking interaction that prevents movement
```

Include entity if:

```text
force_full_scan and entity is movable
target changed
movement dirty
strategic target requires movement
interaction target requires proximity
current tile/next tile affected by occupancy change
```

## Where to integrate

In movement phase:

```python
base_candidates = CandidateSelector.entities(
    state,
    update,
    domains={"movement", "strategic", "interaction"},
    require_alive=True,
)

movement_candidates = MovementCandidateSelector.select(
    state,
    update,
    base_candidates,
    force_full_scan=update.force_full_scan,
)
```

Then `route_movement_intent()` processes only `movement_candidates`.

## New tests

```text
tests/unit/optimization/test_movement_candidate_selector.py
tests/integration/optimization/test_movement_candidate_integration.py
tests/perf/test_movement_candidate_perf.py
```

Tests:

```python
def test_movement_selector_skips_entity_without_target():
    ...

def test_movement_selector_skips_entity_already_at_target():
    ...

def test_movement_selector_skips_dead_entity():
    ...

def test_movement_selector_skips_inactive_entity():
    ...

def test_movement_selector_includes_entity_with_target_and_readiness():
    ...

def test_movement_selector_includes_entity_when_target_changed():
    ...

def test_movement_selector_force_full_scan_includes_all_movable_entities():
    ...

def test_movement_selector_result_is_deterministic():
    ...
```

Perf test:

```python
@pytest.mark.perf
def test_movement_candidate_count_less_than_total_in_movement_1000():
    ...
```

## Acceptance criteria

```text
[ ] no-target entities are skipped
[ ] already-at-target entities are skipped
[ ] dead/inactive entities are skipped
[ ] force_full_scan still includes all movable entities
[ ] movement candidate count is measured
[ ] movement routing final state matches full-scan reference
```

---

# Milestone 5 — OccupancySnapshot

## What this class is

`OccupancySnapshot` is a per-tick immutable read model for occupancy and movement legality.

Occupancy lookup itself is not the top bottleneck. The report shows low occupancy timing, and raw profiling shows bigger costs in movement routing and apply. But movement legality repeatedly asks occupancy-related questions, so a snapshot prevents repeated layered recomputation.

## Class to implement

File:

```text
src/engine/optimization/occupancy_snapshot.py
```

Class:

```python
@dataclass(frozen=True)
class OccupancySnapshot:
    tick: int
    occupancy_by_tile: dict[tuple[int, int], int]
    priority_by_entity: dict[int, int]
    engaged_hostiles_by_tile: dict[tuple[int, int], tuple[int, ...]]

    def occupant_at(self, tile: tuple[int, int]) -> int | None:
        ...

    def is_occupied(self, tile: tuple[int, int]) -> bool:
        ...

    def priority_of(self, entity_id: int) -> int:
        ...

class OccupancySnapshotBuilder:
    @staticmethod
    def build(state: AuthoritativeState) -> OccupancySnapshot:
        ...
```

## High-level logic

Build once at phase start:

```text
for each active entity:
    tile = int(position)
    occupancy_by_tile[tile] = entity_id
    priority_by_entity[entity_id] = calculated priority
```

Optional:

```text
precompute engaged_hostiles_by_tile if movement legality frequently asks it
```

## Where to integrate

In pipeline/movement phase:

```python
snapshot = OccupancySnapshotBuilder.build(state)
MovementPhase.route(..., occupancy_snapshot=snapshot)
PositionSwapResolver.resolve(..., occupancy_snapshot=snapshot)
OccupancyConflictResolver.resolve(..., occupancy_snapshot=snapshot)
```

## New tests

```text
tests/unit/optimization/test_occupancy_snapshot.py
tests/integration/optimization/test_occupancy_snapshot_movement_parity.py
```

Tests:

```python
def test_occupancy_snapshot_contains_entity_positions():
    ...

def test_occupancy_snapshot_reports_occupied_tile():
    ...

def test_occupancy_snapshot_reports_empty_tile():
    ...

def test_occupancy_snapshot_is_stable_for_tick():
    ...

def test_occupancy_snapshot_rebuilt_after_apply_changes_position():
    ...

def test_movement_legality_with_snapshot_matches_existing_logic():
    ...
```

## Acceptance criteria

```text
[ ] snapshot matches current state positions
[ ] snapshot is immutable during tick
[ ] snapshot rebuilds after state advances
[ ] snapshot-based legality matches existing legality
[ ] movement legality call path gets simpler, not more complex
```

---

# Milestone 6 — MovementPlanCache

## What this class is

`MovementPlanCache` caches a computed next step when the entity, target, and local occupancy version have not changed.

This is lower priority than MovementCandidateSelector. Do not implement it first.

## Class to implement

File:

```text
src/engine/optimization/movement_plan_cache.py
```

Classes:

```python
@dataclass(frozen=True)
class MovementPlanKey:
    entity_id: int
    current_tile: tuple[int, int]
    target_tile: tuple[int, int]
    occupancy_version: int
    movement_mode: str


@dataclass(frozen=True)
class MovementPlan:
    next_step: tuple[float, float]
    created_tick: int
    valid_until_tick: int


class MovementPlanCache:
    def get(self, key: MovementPlanKey) -> MovementPlan | None:
        ...

    def put(self, key: MovementPlanKey, plan: MovementPlan) -> None:
        ...

    def invalidate_for_dirty(self, dirty: DirtySet) -> None:
        ...
```

## High-level logic

Cache hit is allowed only if:

```text
same entity
same current tile
same target tile
same occupancy version
same movement mode
not expired
```

Invalidate when:

```text
entity moves
target changes
occupancy version changes
terrain/passability changes
entity becomes blocked
```

## Where to integrate

Inside movement route:

```python
key = MovementPlanKey.from_entity(entity, occupancy_snapshot.version)
plan = movement_plan_cache.get(key)

if plan:
    next_step = plan.next_step
else:
    next_step = resolve_move(...)
    movement_plan_cache.put(key, MovementPlan(...))
```

## New tests

```text
tests/unit/optimization/test_movement_plan_cache.py
tests/integration/optimization/test_movement_plan_cache_parity.py
```

Tests:

```python
def test_plan_cache_reuses_plan_when_key_unchanged():
    ...

def test_plan_cache_invalidates_when_entity_moves():
    ...

def test_plan_cache_invalidates_when_target_changes():
    ...

def test_plan_cache_invalidates_when_occupancy_version_changes():
    ...

def test_plan_cache_does_not_reuse_blocked_step():
    ...

def test_cached_movement_plan_matches_uncached_resolution():
    ...
```

## Acceptance criteria

```text
[ ] cache hit equals uncached result
[ ] cache invalidates on movement, target, occupancy change
[ ] cache cannot reuse blocked step
[ ] movement final state remains identical to no-cache mode
```

---

# Milestone 7 — CacheInvalidationPolicy

## What this class is

`CacheInvalidationPolicy` maps DirtySet changes to index/cache invalidation.

This is mandatory before adding a real `WorldIndexService`. Otherwise you will create stale-cache bugs.

## Class to implement

File:

```text
src/engine/optimization/cache_invalidation_policy.py
```

Class:

```python
class CacheInvalidationPolicy:
    @staticmethod
    def invalidated_indexes(dirty: DirtySet) -> set[str]:
        ...
```

## High-level logic

```python
if dirty.resource_node_ids:
    invalidate active_resource_node_index

if dirty.building_ids:
    invalidate building_kind_index

if dirty.movement_entities:
    invalidate entity_position_index
    invalidate occupancy_snapshot
    invalidate movement_plan_cache

if dirty.ground_item_ids:
    invalidate ground_item_index

if dirty.corpse_ids:
    invalidate corpse_index

if dirty.region_ids:
    invalidate region_index
```

## New tests

```text
tests/unit/optimization/test_cache_invalidation_policy.py
```

Tests:

```python
def test_resource_node_dirty_invalidates_resource_index():
    ...

def test_building_dirty_invalidates_building_index():
    ...

def test_movement_dirty_invalidates_occupancy_and_movement_plan_cache():
    ...

def test_ground_item_dirty_invalidates_loot_index():
    ...

def test_corpse_dirty_invalidates_corpse_index():
    ...

def test_empty_dirty_invalidates_nothing():
    ...
```

## Acceptance criteria

```text
[ ] invalidation rules are centralized
[ ] no cache owns private invalidation rules
[ ] empty DirtySet invalidates nothing
[ ] DirtySet world-object domains are respected
```

---

# Milestone 8 — WorldIndexService and SpatialQueryService

## What these classes are

`WorldIndexService` builds reusable indexes over world state.

`SpatialQueryService` uses those indexes for gameplay queries.

This replaces local, ad-hoc state-attached caches in scorers and systems.

## Classes to implement

Files:

```text
src/engine/optimization/world_index_service.py
src/engine/optimization/spatial_query_service.py
```

Classes:

```python
@dataclass(frozen=True)
class WorldIndexes:
    tick: int
    version: int
    active_resource_nodes_by_bucket: dict[tuple[int, int], tuple[int, ...]]
    buildings_by_kind: dict[str, tuple[int, ...]]
    entities_by_tile: dict[tuple[int, int], tuple[int, ...]]
    ground_items_by_tile: dict[tuple[int, int], tuple[int, ...]]
    corpses_by_tile: dict[tuple[int, int], tuple[int, ...]]


class WorldIndexService:
    def get_indexes(
        self,
        state: AuthoritativeState,
        dirty: DirtySet | None,
    ) -> WorldIndexes:
        ...
```

```python
class SpatialQueryService:
    def nearest_resource_node(
        self,
        state: AuthoritativeState,
        indexes: WorldIndexes,
        position: tuple[float, float],
    ) -> ResourceNodeState | None:
        ...

    def nearest_building(
        self,
        state: AuthoritativeState,
        indexes: WorldIndexes,
        position: tuple[float, float],
        kind: str,
    ) -> BuildingState | None:
        ...

    def nearby_entities(
        self,
        state: AuthoritativeState,
        indexes: WorldIndexes,
        position: tuple[float, float],
        radius: float,
    ) -> tuple[int, ...]:
        ...
```

## High-level logic

`WorldIndexService`:

```text
1. keep last indexes
2. inspect dirty_set via CacheInvalidationPolicy
3. rebuild only invalidated index groups
4. reuse unchanged indexes
5. return immutable WorldIndexes
```

`SpatialQueryService`:

```text
1. query nearby buckets
2. calculate exact Manhattan/Euclidean distance depending on game law
3. return deterministic nearest result
4. break ties by id
```

## Where to integrate

Replace scorer-local caches in:

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

## New tests

```text
tests/unit/optimization/test_world_index_service.py
tests/unit/optimization/test_spatial_query_service.py
tests/integration/optimization/test_spatial_query_integration.py
tests/perf/test_world_index_perf.py
```

Tests:

```python
def test_world_index_builds_active_resource_node_index():
    ...

def test_world_index_excludes_depleted_resource_nodes():
    ...

def test_world_index_builds_buildings_by_kind():
    ...

def test_world_index_reuses_index_when_tick_and_dirty_domains_unchanged():
    ...

def test_world_index_invalidates_resource_index_when_resource_node_dirty():
    ...

def test_world_index_invalidates_building_index_when_building_dirty():
    ...

def test_spatial_query_nearest_resource_matches_naive_scan():
    ...

def test_spatial_query_nearest_building_matches_naive_scan():
    ...

def test_spatial_query_nearby_entities_matches_naive_scan():
    ...

@pytest.mark.perf
def test_spatial_query_reduces_resource_goal_scoring_time():
    ...
```

## Acceptance criteria

```text
[ ] spatial queries match naive scan
[ ] tie-breaking is deterministic
[ ] index invalidation follows CacheInvalidationPolicy
[ ] scorers stop attaching hidden caches to state
[ ] resource/eat/sleep scoring gets cheaper or does not regress
```

---

# Milestone 9 — StrategicWorkQueue

## What this class is

`StrategicWorkQueue` decides which entities need strategic intelligence work this tick.

Strategic intelligence is consistently visible in profiling. In the movement profile, `fused_strategic_pass` costs about `12.403s`, and `evaluate_strategic_intent` costs about `7.844s` across 500 ticks.

## Class to implement

File:

```text
src/engine/optimization/strategic_work_queue.py
```

Classes:

```python
@dataclass(frozen=True)
class StrategicQueueConfig:
    max_entities_per_tick: int
    background_sweep_interval: int
    urgent_bypass_budget: int


class StrategicWorkQueue:
    @staticmethod
    def build(
        state: AuthoritativeState,
        update: StateUpdate,
        dirty: DirtySet,
        config: StrategicQueueConfig,
    ) -> tuple[int, ...]:
        ...
```

## High-level priority logic

Priority order:

```text
1. failed action/path entities
2. unresolved blockers
3. active project transition
4. biological emergency
5. contract expiration
6. dirty strategic entities
7. background sweep sample
```

Rules:

```text
urgent entities bypass normal cadence
budget limits routine entities
background sweep prevents starvation
force_full_scan returns all strategic entities
```

## Where to integrate

Inside `fused_strategic_pass`:

```python
candidate_ids = StrategicWorkQueue.build(...)
for entity_id in candidate_ids:
    evaluate_strategic_intent(...)
```

## New tests

```text
tests/unit/optimization/test_strategic_work_queue.py
tests/integration/optimization/test_strategic_queue_integration.py
tests/perf/test_strategic_queue_perf.py
```

Tests:

```python
def test_strategic_queue_prioritizes_failed_action_entity():
    ...

def test_strategic_queue_prioritizes_unresolved_blocker():
    ...

def test_strategic_queue_prioritizes_biological_emergency():
    ...

def test_strategic_queue_includes_dirty_strategic_entities():
    ...

def test_strategic_queue_respects_budget():
    ...

def test_strategic_queue_background_sweep_prevents_starvation():
    ...

def test_strategic_queue_force_full_scan_includes_all_strategic_entities():
    ...

@pytest.mark.perf
def test_strategic_queue_reduces_evaluated_entity_count():
    ...
```

## Acceptance criteria

```text
[ ] urgent strategic entities are processed first
[ ] routine strategic entities respect budget
[ ] background sweep prevents starvation
[ ] force_full_scan bypasses queue narrowing
[ ] strategic candidate count decreases
[ ] strategic semantic outcome remains stable or divergence is documented
```

---

# Milestone 10 — PerfRegressionGate

## What this class is

`PerfRegressionGate` compares current performance against committed baselines.

This prevents future “optimization” from regressing ApplyPath, movement, strategic, or memory behavior.

## Class to implement

File:

```text
src/perf/regression_gate.py
```

Classes:

```python
@dataclass(frozen=True)
class PerfThresholds:
    max_relative_regression: float = 0.15
    max_absolute_ms_regression: float = 3.0
    max_memory_relative_regression: float = 0.10


@dataclass(frozen=True)
class PerfGateResult:
    passed: bool
    failures: tuple[str, ...]


class PerfRegressionGate:
    def compare(
        self,
        baseline: dict[str, Any],
        current: dict[str, Any],
        thresholds: PerfThresholds,
    ) -> PerfGateResult:
        ...
```

## Metrics to compare

```text
p95_tick_compute_ms
p99_tick_compute_ms
phase p95
memory_delta_mb
peak_rss_mb
compute_tps
raw_entity_updates
compacted_entity_updates
movement_candidate_count
strategic_candidate_count
```

## High-level logic

```text
for latency:
    allowed = max(baseline * (1 + relative), baseline + absolute_ms)
    current must be <= allowed

for throughput:
    current must not drop below baseline * (1 - relative)

for memory:
    current must not exceed allowed memory regression

in CI:
    missing baseline = fail

local:
    missing baseline = warn/skip
```

## New tests

```text
tests/unit/perf/test_perf_regression_gate.py
tests/perf/test_perf_baseline_ci_behavior.py
```

Tests:

```python
def test_perf_gate_passes_within_threshold():
    ...

def test_perf_gate_fails_when_p95_regresses_too_much():
    ...

def test_perf_gate_fails_when_phase_regresses_too_much():
    ...

def test_perf_gate_fails_when_memory_regresses_too_much():
    ...

def test_perf_gate_fails_when_compute_tps_drops_too_much():
    ...

def test_perf_gate_ignores_wall_clock_tps_for_compute_regression():
    ...

def test_missing_baseline_fails_in_ci_mode():
    ...

def test_missing_baseline_warns_or_skips_in_local_mode():
    ...
```

## Acceptance criteria

```text
[ ] baseline comparison uses compute metrics, not wall-clock metrics
[ ] missing baseline fails in CI
[ ] phase-level regression is checked
[ ] memory regression is checked
[ ] throughput regression is checked
[ ] optimization metrics are included
```

---

# Recommended implementation order

Do not implement all mechanisms at once.

Use this exact order:

```text
1. Profiling modes and hot-path print cleanup
2. CandidateSelector / ScanPolicy
3. Full-scan compliance tests for all optimized phases
4. DirtyDependencyGraph
5. StateUpdateCompactor
6. MovementCandidateSelector
7. OccupancySnapshot
8. MovementPlanCache
9. CacheInvalidationPolicy
10. WorldIndexService / SpatialQueryService
11. StrategicWorkQueue
12. PerfRegressionGate
```

Reason:

```text
CandidateSelector makes reference mode truthful.
DirtyDependencyGraph makes dirty propagation safe.
StateUpdateCompactor attacks the largest measured cost.
MovementCandidateSelector attacks the second-largest measured cost.
WorldIndexService removes ad-hoc cache risk.
StrategicWorkQueue handles the remaining AI tax.
PerfRegressionGate prevents backsliding.
```

---

# Minimal first implementation slice

Do this first, before touching spatial indexes or strategic queue:

```text
Slice 1:
- CandidateSelector
- InteractionPhase uses CandidateSelector
- MovementPhase uses CandidateSelector
- force_full_scan compliance tests
- static guard against direct DirtySet narrowing

Slice 2:
- StateUpdateCompactor
- compacted-vs-uncompacted parity tests
- apply compaction metrics

Slice 3:
- MovementCandidateSelector
- movement candidate metrics
- movement full-scan parity
```

This gives you the highest risk reduction and performance payoff.

---

# What not to implement yet

Do **not** start with `WorldIndexService`.

It is architecturally important, but it is not the top measured hotspot yet. The top measured hotspot is still ApplyPath/update churn.

Do **not** start with `MovementPlanCache`.

Plan caching is fragile. First reduce the number of movement candidates. Then cache plans.

Do **not** start with `StrategicWorkQueue`.

Strategic is visible, but movement/apply are worse in the 1,000-entity profiles.

---

# Priority Plan

## Mindset change

Stop improving individual functions in isolation. Build an optimization framework that makes wrong optimization hard.

## Immediate actions

```text
1. Implement CandidateSelector and tests.
2. Wire InteractionPhase and MovementPhase through it.
3. Add static guard against direct DirtySet candidate narrowing.
4. Implement StateUpdateCompactor and parity tests.
5. Add compaction metrics to BenchHarness output.
```

## Stop doing

Stop adding local caches inside scorers or systems. That creates hidden invalidation bugs.

## Consequence if ignored

You will keep producing local speedups that are hard to prove globally. The engine will get faster in selected scenarios, but every new optimization will increase the chance of skipping gameplay logic.
