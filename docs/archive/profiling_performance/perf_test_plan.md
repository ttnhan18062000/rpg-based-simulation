---
status: archive
authority: P2
audience: historical
layer: performance
original_date: unknown
---

# Test Implementation Plan First

Your current test suite has useful pieces already: `StateUpdate` has `force_full_scan`, the pipeline has a `_refresh_dirty_set()` rule that expands dirty domains to all entities when full-scan is enabled, and there is already an optimized-vs-full-scan parity test.

But the next optimization work needs a stronger test structure. Otherwise you will add mechanisms that look faster but silently skip logic.

The test plan should be built around this contract:

```text
Optimized path must produce the same semantic result as the full-reference path, while doing measurably less work.
```

---

# 1. Test Suite: CandidateSelector / ScanPolicy

## What this class is

`CandidateSelector` is the central class that decides **which entities a phase should process**.

Right now, each phase can accidentally decide this differently by reading `update.dirty_set` directly. That is the root cause of fake full-scan reference risk.

## Proposed class

```python
class CandidateSelector:
    @staticmethod
    def entities(
        state: AuthoritativeState,
        update: StateUpdate,
        domains: set[str],
        *,
        include_inactive: bool = False,
    ) -> tuple[int, ...]:
        ...
```

## High-level logic

```text
if update.force_full_scan:
    return all relevant entity ids from state

if update.dirty_set is None:
    return all relevant entity ids from state

else:
    return union of requested dirty domains
```

Example:

```python
CandidateSelector.entities(
    state,
    update,
    domains={"movement", "strategic"},
)
```

Should return:

```text
dirty_set.movement_entities | dirty_set.strategic_entities
```

But if `force_full_scan=True`, it must return all relevant entities.

## Test file

```text
tests/unit/optimization/test_candidate_selector.py
```

## Tests to implement

```python
def test_candidate_selector_returns_all_entities_when_force_full_scan():
    """
    Given:
        state has 3 entities
        update.force_full_scan=True
        update.dirty_set is empty

    Expect:
        all 3 entity ids are returned
    """
```

```python
def test_candidate_selector_returns_all_entities_when_dirty_set_missing():
    """
    Given:
        update.dirty_set is None

    Expect:
        all entity ids are returned because no safe narrowing exists.
    """
```

```python
def test_candidate_selector_unions_requested_dirty_domains():
    """
    Given:
        movement dirty = {1, 2}
        strategic dirty = {2, 3}
        domains={"movement", "strategic"}

    Expect:
        {1, 2, 3}
    """
```

```python
def test_candidate_selector_does_not_include_unrequested_domains():
    """
    Given:
        movement dirty = {1}
        combat dirty = {2}
        domains={"movement"}

    Expect:
        only {1}
    """
```

```python
def test_candidate_selector_result_is_deterministic():
    """
    Expect:
        repeated calls return the same ordered tuple.
    """
```

## Acceptance criteria

```text
[x] CandidateSelector exists.
[x] force_full_scan=True ignores DirtySet narrowing.
[x] dirty_set=None falls back to full scan.
[x] dirty_set with domains returns only requested dirty domains.
[x] result order is deterministic.
[x] phases stop implementing their own dirty-set narrowing logic.
```

---

# 2. Test Suite: Full-Scan Phase Compliance

## What this protects

This makes sure every optimized phase respects the reference path.

The existing parity test runs optimized mode and `force_full_scan=True` mode, then compares fingerprints. That is good, but it is not enough unless every phase actually honors full-scan mode.

## Test file

```text
tests/integration/optimization/test_force_full_scan_phase_compliance.py
```

## Phases to cover

```text
InteractionPhase
MovementPhase
StrategicIntelligenceSystem
GroupPhase
ShopSystem
CapacityEnforcementPhase
LifecycleSystem
```

## Tests to implement

### 2.1 Interaction full-scan

```python
def test_interaction_phase_force_full_scan_processes_entity_with_empty_dirty_set():
    """
    Given:
        entity has navigation.target pointing to a resource node
        update.force_full_scan=True
        update.dirty_set is empty

    Expect:
        InteractionPhase still evaluates the entity.
    """
```

Expected check:

```python
assert entity_id in refined.entity_updates
assert refined.entity_updates[entity_id].interaction is not None
```

### 2.2 Movement full-scan

```python
def test_movement_phase_force_full_scan_processes_entity_with_target_and_empty_dirty_set():
    """
    Given:
        entity has navigation.target
        update.force_full_scan=True
        dirty_set empty

    Expect:
        MovementPhase creates movement update.
    """
```

Expected check:

```python
assert refined.entity_updates[entity_id].new_position is not None
```

### 2.3 Strategic full-scan

```python
def test_strategic_phase_force_full_scan_processes_active_project_entity_with_empty_dirty_set():
    """
    Given:
        entity has active strategic project
        update.force_full_scan=True
        dirty_set empty

    Expect:
        strategic phase evaluates the entity.
    """
```

### 2.4 Shop full-scan

You already have tests where `ShopSystem` reacts to `StateUpdate(force_full_scan=True)` and produces inventory changes. Keep that, but move/duplicate one into optimization compliance so it explicitly documents the full-scan contract.

```python
def test_shop_phase_force_full_scan_processes_inventory_entity_with_empty_dirty_set():
    ...
```

### 2.5 Capacity full-scan

```python
def test_capacity_phase_force_full_scan_processes_all_inventory_entities():
    """
    Given:
        entity inventory exceeds max slots
        dirty_set empty
        force_full_scan=True

    Expect:
        capacity enforcement runs.
    """
```

## Acceptance criteria

```text
[x] Every DirtySet-optimized phase has a full-scan compliance test.
[x] Empty DirtySet cannot suppress work in force_full_scan mode.
[x] Optimized-vs-full-scan parity test becomes meaningful.
```

---

# 3. Test Suite: Static Guard Against Direct DirtySet Usage

## What this protects

Once `CandidateSelector` exists, phases should not directly do this:

```python
update.dirty_set.movement_entities
```

That is how optimization becomes inconsistent.

## Test file

```text
tests/static/test_no_direct_dirtyset_candidate_selection.py
```

## Test logic

Scan selected source directories:

```text
src/engine/pipeline_phases
src/systems
src/ai
```

Allow direct DirtySet use only in:

```text
src/core/dirty.py
src/engine/candidate_selector.py
src/engine/pipeline.py
tests/
```

## Test

```python
def test_no_direct_dirtyset_candidate_selection_outside_selector():
    forbidden_patterns = [
        ".dirty_set.movement_entities",
        ".dirty_set.combat_entities",
        ".dirty_set.inventory_entities",
        ".dirty_set.strategic_entities",
        ".dirty_set.lifecycle_entities",
    ]

    allowed_files = {
        "src/core/dirty.py",
        "src/engine/candidate_selector.py",
    }

    ...
```

## Acceptance criteria

```text
[x] DirtySet candidate selection is centralized.
[x] New systems cannot bypass CandidateSelector silently.
```

This sounds strict because it needs to be strict.

---

# 4. Test Suite: DirtyDependencyGraph

## What this class is

`DirtyDependencyGraph` expands **direct dirtiness** into **derived dirtiness**.

Example:

```text
movement changed
```

should imply:

```text
movement dirty
occupancy dirty
interaction dirty
group dirty
town/region membership dirty
```

DirtySet currently tracks many domains: movement, combat, inventory, strategic, social, lifecycle, town, biological, attributes, groups, regions, resource nodes, buildings, chests, ground items, corpses, and camps.

But tracking changed domains is not the same as knowing which downstream systems must react.

## Proposed class

```python
class DirtyDependencyGraph:
    @staticmethod
    def expand(dirty: DirtySet) -> DirtySet:
        ...
```

## High-level logic

```text
input:
    DirtySet from direct StateUpdate

output:
    DirtySet with derived dependent domains added
```

## Test file

```text
tests/unit/optimization/test_dirty_dependency_graph.py
```

## Tests to implement

```python
def test_dirty_dependency_movement_marks_interaction_group_and_town():
    """
    movement dirty should imply systems affected by position.
    """
```

Expected:

```python
expanded.movement_entities == {1}
expanded.interaction_entities == {1}
expanded.group_entities == {1}
expanded.town_entities includes entity 1 or relevant domain marker
```

```python
def test_dirty_dependency_inventory_marks_capacity_shop_and_strategic():
    """
    inventory dirty should trigger systems depending on inventory state.
    """
```

```python
def test_dirty_dependency_combat_marks_lifecycle_group_and_quest():
    """
    combat dirty should trigger lifecycle/death/quest/group consequences.
    """
```

```python
def test_dirty_dependency_resource_node_marks_interaction_candidates():
    """
    resource node dirty should invalidate resource interaction candidate logic.
    """
```

```python
def test_dirty_dependency_expansion_is_idempotent():
    """
    expand(expand(dirty)) must equal expand(dirty).
    """
```

```python
def test_dirty_dependency_expansion_is_deterministic():
    """
    Same input must always produce same output.
    """
```

## Acceptance criteria

```text
[x] Dependency rules are explicit.
[x] Expansion is deterministic.
[x] Expansion is idempotent.
[x] Phase triggering uses expanded dirty state, not only direct dirty state.
```

---

# 5. Test Suite: StateUpdateCompactor

## What this class is

`StateUpdateCompactor` reduces noisy updates before `ApplyPath`.

The profiler says this should be a top priority. In movement profiling, `apply_generation` costs about `54.664s`, `apply.py:replace` costs about `33.949s`, and `dataclasses.replace` is also visible. In resource profiling, `apply_generation` costs about `54.759s`, `apply.py:replace` about `34.710s`, and `_apply_entity_update_to_dict` about `23.848s`.

That means you need to reduce update volume before applying state.

## Proposed class

```python
class StateUpdateCompactor:
    @staticmethod
    def compact(
        state: AuthoritativeState,
        update: StateUpdate,
    ) -> StateUpdate:
        ...
```

## High-level logic

```text
drop empty EntityUpdate
drop zero-delta component updates
merge repeated updates for same entity
remove property updates that equal current state
collapse repeated deltas
deduplicate world-object operations
preserve order where order matters
```

## Test file

```text
tests/unit/optimization/test_state_update_compactor.py
```

## Tests to implement

### 5.1 Drop no-op entity update

```python
def test_compactor_drops_empty_entity_update():
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1)
        }
    )

    compacted = StateUpdateCompactor.compact(state, update)

    assert 1 not in compacted.entity_updates
```

### 5.2 Drop zero-delta combat update

```python
def test_compactor_drops_zero_delta_combat_update():
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                combat=CombatUpdate(hp_delta=0)
            )
        }
    )

    compacted = StateUpdateCompactor.compact(state, update)

    assert 1 not in compacted.entity_updates
```

### 5.3 Preserve meaningful combat update

```python
def test_compactor_preserves_nonzero_combat_update():
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                combat=CombatUpdate(hp_delta=-10)
            )
        }
    )

    compacted = StateUpdateCompactor.compact(state, update)

    assert compacted.entity_updates[1].combat.hp_delta == -10
```

### 5.4 Drop property update equal to current value

```python
def test_compactor_drops_property_update_equal_to_current_value():
    entity = state.entities[1]

    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(
                entity_id=1,
                property_updates={
                    "kind": entity.kind
                }
            )
        }
    )

    compacted = StateUpdateCompactor.compact(state, update)

    assert 1 not in compacted.entity_updates
```

### 5.5 Compacted apply equals uncompacted apply

```python
def test_compacted_update_applies_same_as_uncompacted_update():
    uncompacted_state = ApplyPath.apply_generation(state, update)
    compacted = StateUpdateCompactor.compact(state, update)
    compacted_state = ApplyPath.apply_generation(state, compacted)

    assert fingerprint(uncompacted_state) == fingerprint(compacted_state)
```

### 5.6 Compactor reports metrics

```python
def test_compactor_reports_reduction_metrics():
    compacted, metrics = StateUpdateCompactor.compact_with_metrics(state, update)

    assert metrics.raw_entity_updates >= metrics.compacted_entity_updates
    assert metrics.dropped_noop_updates >= 0
```

## Acceptance criteria

```text
[x] Compactor never changes final semantic state.
[x] Compactor drops empty updates.
[x] Compactor drops zero-delta updates.
[x] Compactor drops property updates equal to current state.
[x] Compactor emits before/after metrics.
[x] Movement/resource scenario shows reduced update count.
```

---

# 6. Test Suite: ApplyPath Performance Regression

## What this protects

This proves the compactor actually attacks the measured hotspot.

## Test file

```text
tests/perf/test_apply_compaction_perf.py
```

## Tests to implement

```python
@pytest.mark.perf
def test_compactor_reduces_entity_update_count_in_movement_1000():
    """
    Build movement scenario.
    Run one tick or several ticks with instrumentation.
    Assert compacted update count < raw update count.
    """
```

```python
@pytest.mark.perf
def test_compactor_reduces_apply_generation_time_in_resource_smoke():
    """
    Compare baseline vs compaction-enabled run.
    Assert apply_generation p95 improves or stays under threshold.
    """
```

## Required metrics

Add these to kernel or bench result:

```text
raw_entity_update_count
compacted_entity_update_count
dropped_noop_update_count
apply_generation_ms
dataclass_replace_count if possible
```

## Acceptance criteria

```text
[x] Compaction reduces update count in movement/resource scenarios.
[x] ApplyPath time does not regress.
[x] Final hash remains identical.
```

---

# 7. Test Suite: MovementCandidateSelector

## What this class is

`MovementCandidateSelector` decides which entities need movement routing.

The profiler shows movement routing is a major bottleneck: movement profile has `_route_movement_intent` at about `23.058s`, `route_movement_intent` at about `23.014s`, and `resolve_move` at about `21.074s`. Resource profile is even heavier: `_route_movement_intent` about `39.881s`, `route_movement_intent` about `35.713s`, and `resolve_move` about `37.233s`.

## Proposed class

```python
class MovementCandidateSelector:
    @staticmethod
    def select(
        state: AuthoritativeState,
        update: StateUpdate,
        candidates: Iterable[int],
    ) -> tuple[int, ...]:
        ...
```

## High-level logic

Skip entity if:

```text
no navigation target
already at target
not alive / inactive
readiness too low
movement cadence says skip
not movement-dirty and no relevant occupancy/target change
```

Include entity if:

```text
force_full_scan
target changed
current tile blocked
movement dirty
interaction requires movement
strategic project requires movement
```

## Test file

```text
tests/unit/optimization/test_movement_candidate_selector.py
```

## Tests to implement

```python
def test_movement_selector_skips_entity_without_target():
    ...
```

```python
def test_movement_selector_skips_entity_already_at_target():
    ...
```

```python
def test_movement_selector_skips_inactive_or_dead_entity():
    ...
```

```python
def test_movement_selector_includes_entity_with_target_and_readiness():
    ...
```

```python
def test_movement_selector_includes_entity_when_target_changed():
    ...
```

```python
def test_movement_selector_force_full_scan_includes_all_movable_entities():
    ...
```

```python
def test_movement_selector_is_deterministic():
    ...
```

## Acceptance criteria

```text
[x] Movement selector excludes obvious no-work entities.
[x] force_full_scan still processes all movable entities.
[x] Movement selector result is deterministic.
[x] Movement phase candidate count is observable.
```

---

# 8. Test Suite: OccupancySnapshot

## What this class is

`OccupancySnapshot` is a per-tick read model for occupancy and movement legality.

The profile shows occupancy lookup itself is not your main bottleneck, but movement legality repeatedly calls occupancy/priority checks. So the goal is not just “cache occupancy”; it is to give movement logic one stable snapshot for the whole tick.

## Proposed class

```python
@dataclass(frozen=True)
class OccupancySnapshot:
    tick: int
    occupancy_by_tile: dict[tuple[int, int], int]
    priority_by_entity: dict[int, int]

    def occupant_at(self, tile: tuple[int, int]) -> int | None:
        ...

    def is_occupied(self, tile: tuple[int, int]) -> bool:
        ...
```

## Test file

```text
tests/unit/optimization/test_occupancy_snapshot.py
```

## Tests to implement

```python
def test_occupancy_snapshot_contains_entity_positions():
    ...
```

```python
def test_occupancy_snapshot_reports_occupied_tile():
    ...
```

```python
def test_occupancy_snapshot_reports_empty_tile():
    ...
```

```python
def test_occupancy_snapshot_is_stable_for_tick():
    ...
```

```python
def test_occupancy_snapshot_rebuilt_after_apply_changes_position():
    ...
```

```python
def test_movement_legality_uses_snapshot_result_equivalent_to_current_logic():
    ...
```

## Acceptance criteria

```text
[x] Snapshot matches current state positions.
[x] Snapshot is immutable for the tick.
[x] Snapshot rebuilds after state advances.
[x] Movement legality using snapshot matches existing legality result.
```

---

# 9. Test Suite: MovementPlanCache

## What this class is

`MovementPlanCache` caches the next movement decision when the entity, target, and local occupancy conditions have not changed.

## Proposed class

```python
@dataclass(frozen=True)
class MovementPlanKey:
    entity_id: int
    current_tile: tuple[int, int]
    target_tile: tuple[int, int]
    occupancy_version: int

@dataclass(frozen=True)
class MovementPlan:
    next_step: tuple[float, float]
    valid_until_tick: int

class MovementPlanCache:
    def get(self, key: MovementPlanKey) -> MovementPlan | None:
        ...

    def put(self, key: MovementPlanKey, plan: MovementPlan) -> None:
        ...

    def invalidate_for_dirty(self, dirty: DirtySet) -> None:
        ...
```

## Test file

```text
tests/unit/optimization/test_movement_plan_cache.py
```

## Tests to implement

```python
def test_plan_cache_reuses_plan_when_key_unchanged():
    ...
```

```python
def test_plan_cache_invalidates_when_entity_moves():
    ...
```

```python
def test_plan_cache_invalidates_when_target_changes():
    ...
```

```python
def test_plan_cache_invalidates_when_occupancy_version_changes():
    ...
```

```python
def test_plan_cache_does_not_reuse_blocked_step():
    ...
```

```python
def test_cached_movement_plan_matches_uncached_resolution():
    ...
```

## Acceptance criteria

```text
[x] Cache hit produces same next step as uncached logic.
[x] Cache invalidates on movement, target change, and occupancy change.
[x] Cache cannot reuse blocked movement.
```

---

# 10. Test Suite: WorldIndexService / SpatialQueryService

## What these classes are

`WorldIndexService` builds reusable indexes over world state.

`SpatialQueryService` uses those indexes to answer gameplay queries:

```text
nearest resource node
nearest tavern
nearest inn
nearby entities
nearby loot
nearby corpse
```

This replaces ad-hoc caches in scorers. Current scorer code has state-attached caches like active resource nodes and building caches; that is a short-term speedup but a long-term correctness risk.

## Proposed classes

```python
class WorldIndexService:
    def get_indexes(
        self,
        state: AuthoritativeState,
        dirty: DirtySet | None,
    ) -> WorldIndexes:
        ...
```

```python
@dataclass(frozen=True)
class WorldIndexes:
    tick: int
    active_resource_nodes: SpatialIndex
    buildings_by_kind: dict[str, tuple[int, ...]]
    entities_by_tile: dict[tuple[int, int], tuple[int, ...]]
    ground_items_by_tile: dict[tuple[int, int], tuple[int, ...]]
    corpses_by_tile: dict[tuple[int, int], tuple[int, ...]]
```

```python
class SpatialQueryService:
    def nearest_resource_node(...):
        ...

    def nearest_building(...):
        ...

    def nearby_entities(...):
        ...
```

## Test file

```text
tests/unit/optimization/test_world_index_service.py
tests/unit/optimization/test_spatial_query_service.py
```

## Tests to implement

```python
def test_world_index_builds_active_resource_node_index():
    ...
```

```python
def test_world_index_excludes_depleted_resource_nodes():
    ...
```

```python
def test_world_index_builds_buildings_by_kind():
    ...
```

```python
def test_world_index_reuses_index_when_tick_and_dirty_domains_unchanged():
    ...
```

```python
def test_world_index_invalidates_resource_index_when_resource_node_dirty():
    ...
```

```python
def test_world_index_invalidates_building_index_when_building_dirty():
    ...
```

```python
def test_spatial_query_nearest_resource_matches_naive_scan():
    ...
```

```python
def test_spatial_query_nearest_building_matches_naive_scan():
    ...
```

```python
def test_spatial_query_nearby_entities_matches_naive_scan():
    ...
```

## Acceptance criteria

```text
[x] Spatial queries match naive scan.
[x] Index invalidation is dirty-domain based.
[x] Same-tick repeated query reuses index.
[x] Scorers no longer attach hidden caches to state.
```

---

# 11. Test Suite: CacheInvalidationPolicy

## What this class is

`CacheInvalidationPolicy` tells indexes and caches what to invalidate based on DirtySet.

## Proposed class

```python
class CacheInvalidationPolicy:
    @staticmethod
    def invalidated_indexes(dirty: DirtySet) -> set[str]:
        ...
```

## High-level logic

```text
resource_node_ids dirty -> active_resource_node_index
building_ids dirty -> building_kind_index
movement_entities dirty -> entity_position_index, occupancy_snapshot
ground_item_ids dirty -> ground_item_index
corpse_ids dirty -> corpse_index
region_ids dirty -> region_index
```

## Test file

```text
tests/unit/optimization/test_cache_invalidation_policy.py
```

## Tests

```python
def test_resource_node_dirty_invalidates_resource_index():
    ...
```

```python
def test_building_dirty_invalidates_building_index():
    ...
```

```python
def test_movement_dirty_invalidates_occupancy_and_entity_position_index():
    ...
```

```python
def test_ground_item_dirty_invalidates_loot_index():
    ...
```

```python
def test_corpse_dirty_invalidates_corpse_index():
    ...
```

```python
def test_empty_dirty_invalidates_nothing():
    ...
```

## Acceptance criteria

```text
[x] Invalidation rules are centralized.
[x] No cache owns private invalidation logic.
[x] WorldIndexService uses this policy.
```

---

# 12. Test Suite: StrategicWorkQueue

## What this class is

`StrategicWorkQueue` decides which entities need strategic intelligence work this tick.

Strategic intelligence is visible in all profiles: for example, movement has `fused_strategic_pass` around `12.403s` and `evaluate_strategic_intent` around `7.844s` across 500 ticks. Mixed has `fused_strategic_pass` around `1.459s` across 50 ticks.

## Proposed class

```python
class StrategicWorkQueue:
    @staticmethod
    def build(
        state: AuthoritativeState,
        update: StateUpdate,
        dirty: DirtySet,
        budget: int,
    ) -> tuple[int, ...]:
        ...
```

## Priority logic

```text
1. failed action/path entities
2. unresolved blockers
3. active project transition
4. biological emergency
5. contract expiration
6. dirty strategic entities
7. background sweep sample
```

## Test file

```text
tests/unit/optimization/test_strategic_work_queue.py
```

## Tests

```python
def test_strategic_queue_prioritizes_failed_action_entity():
    ...
```

```python
def test_strategic_queue_prioritizes_unresolved_blocker():
    ...
```

```python
def test_strategic_queue_prioritizes_biological_emergency():
    ...
```

```python
def test_strategic_queue_includes_dirty_strategic_entities():
    ...
```

```python
def test_strategic_queue_respects_budget():
    ...
```

```python
def test_strategic_queue_background_sweep_prevents_starvation():
    ...
```

```python
def test_strategic_queue_force_full_scan_includes_all_strategic_entities():
    ...
```

## Acceptance criteria

```text
[x] Queue order is deterministic.
[x] Urgent entities are processed before routine entities.
[x] Budget is respected.
[x] Starvation prevention exists.
[x] force_full_scan bypasses queue narrowing.
```

---

# 13. Test Suite: Profiling Harness Modes

## What this protects

Your profiling harness currently creates a kernel with:

```python
flags={"audit_mode": False}
```

It does not explicitly set `no_replay=True` or `no_frame_pacing=True`. That is why profiling data can include `time.sleep`, replay persistence, and `dataclasses.asdict`.

## Proposed modes

```text
pure:
    no_replay=True
    no_frame_pacing=True
    audit_mode=False

runtime:
    no_replay=False
    no_frame_pacing=False
    audit_mode=False

audit:
    no_replay=False
    no_frame_pacing=True
    audit_mode=True
```

## Test file

```text
tests/unit/perf/test_profiling_harness_modes.py
```

## Tests

```python
def test_profiling_pure_mode_sets_clean_compute_flags():
    ...
```

```python
def test_profiling_runtime_mode_allows_replay_and_frame_pacing():
    ...
```

```python
def test_profiling_audit_mode_enables_audit_without_frame_pacing():
    ...
```

```python
def test_profile_output_includes_mode_and_flags():
    ...
```

```python
def test_profile_report_does_not_claim_gc_resilience_without_gc_metrics():
    ...
```

The last test matters because the report currently claims GC resilience and no memory fragmentation, but the report content shown is mostly cProfile and scenario matrix, not real GC/RSS proof.

## Acceptance criteria

```text
[x] Pure profile excludes replay and frame pacing.
[x] Runtime profile is labeled separately.
[x] Audit profile is labeled separately.
[x] Report includes flags used.
[x] Report cannot claim GC/memory stability without GC/RSS data.
```

---

# 14. Test Suite: Perf Regression Gate

## What this class is

`PerfRegressionGate` compares current metrics to committed baselines.

`BenchHarness` already exists and is the right foundation for benchmark runs. It is designed for RSS monitoring, percentiles, and phase-specific cost distribution.

## Proposed class

```python
class PerfRegressionGate:
    def compare(
        self,
        baseline: PerfBaseline,
        current: PerfResult,
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
```

## Test file

```text
tests/unit/perf/test_perf_regression_gate.py
```

## Tests

```python
def test_perf_gate_passes_within_threshold():
    ...
```

```python
def test_perf_gate_fails_when_p95_regresses_too_much():
    ...
```

```python
def test_perf_gate_fails_when_phase_regresses_too_much():
    ...
```

```python
def test_perf_gate_fails_when_memory_regresses_too_much():
    ...
```

```python
def test_perf_gate_ignores_wall_clock_tps_for_compute_regression():
    ...
```

```python
def test_missing_baseline_fails_in_ci_mode():
    ...
```

```python
def test_missing_baseline_warns_or_skips_in_local_mode():
    ...
```

## Acceptance criteria

```text
[x] CI cannot silently skip missing baseline.
[x] Gate compares compute metrics, not wall-clock metrics.
[x] Gate includes phase-level regression.
[x] Gate includes memory regression.
```

---

# Recommended Test Implementation Order

Do this in this order.

```text
1. [x] CandidateSelector unit tests
2. [x] Full-scan phase compliance tests
3. [x] Static guard against direct DirtySet selection
4. [x] DirtyDependencyGraph tests
5. [x] StateUpdateCompactor unit tests
6. [x] Compacted-vs-uncompacted ApplyPath parity tests
7. [x] MovementCandidateSelector tests
8. [x] OccupancySnapshot tests
9. [x] MovementPlanCache tests
10. [x] WorldIndexService / SpatialQueryService tests
11. [x] CacheInvalidationPolicy tests
12. [x] StrategicWorkQueue tests
13. [x] Profiling harness mode tests
14. [x] PerfRegressionGate tests
```

Do not start with performance assertions first. First make semantic equivalence impossible to fake.

---

# Test Directory Structure

Recommended structure:

```text
tests/
  unit/
    optimization/
      test_candidate_selector.py
      test_dirty_dependency_graph.py
      test_state_update_compactor.py
      test_movement_candidate_selector.py
      test_occupancy_snapshot.py
      test_movement_plan_cache.py
      test_world_index_service.py
      test_spatial_query_service.py
      test_cache_invalidation_policy.py
      test_strategic_work_queue.py

    perf/
      test_profiling_harness_modes.py
      test_perf_regression_gate.py

  integration/
    optimization/
      test_force_full_scan_phase_compliance.py
      test_compacted_apply_parity.py
      test_movement_optimized_vs_full_scan.py
      test_spatial_query_integration.py
      test_strategic_queue_integration.py

  perf/
    test_apply_compaction_perf.py
    test_movement_optimization_perf.py
    test_world_index_perf.py
    test_strategic_queue_perf.py

  static/
    test_no_direct_dirtyset_candidate_selection.py
    test_no_hot_path_prints.py
```

---

# Definition of Done for the Test Plan

```text
[x] Every optimization mechanism has unit tests.
[x] Every mechanism has at least one integration parity test.
[x] Every performance optimization has a before/after metric.
[x] Full-scan reference mode is tested per phase.
[x] Optimized path and full-scan path produce identical final fingerprints unless divergence is intentional and documented.
[x] No phase can bypass CandidateSelector for entity candidate narrowing.
[x] Profiling reports are mode-labeled and cannot make unsupported memory/GC claims.
[x] CI has strict perf-regression behavior.
```
