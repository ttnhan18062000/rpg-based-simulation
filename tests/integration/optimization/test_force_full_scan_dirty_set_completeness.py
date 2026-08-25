"""
Regression coverage for TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE.

`AuthoritativeApplyPipeline._refresh_dirty_set` was dead code: no live path called it, so a
`force_full_scan=True` tick never widened the *downstream* `StateUpdate.dirty_set` (the one
`Kernel._run_hard_law_checks` copies onto `self._status.dirty_set`, and that
`V2EngineManager._update_latest_state` / `ReadModelCache.compute_tick_delta` consume) to cover
every entity -- even though `force_full_scan` already correctly widened phase-routing candidate
selection. This file proves the fix: the final-dirty-set override at the tail of `refine()`,
gated on `update.force_full_scan`, plus `RuntimeStatus.force_full_scan` actually surfacing the
Kernel's boot-time flag.
"""
from dataclasses import replace

from src.core.state import AuthoritativeState, BuildingState
from src.core.updates import StateUpdate, BuildingUpdate
from src.core.dirty import DirtySet
from src.core.builder import V2EntityBuilder
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.platform.rng import DeterministicRNG
from src.api.read_model_cache import ReadModelCache
from src.observability.config import ObservabilityConfig, ObservabilityMode


def _idle_entities_state() -> AuthoritativeState:
    """Three entities that produce no EntityUpdate on their own during refine()."""
    entities = {}
    for eid in (1, 2, 3):
        entities[eid] = (
            V2EntityBuilder(eid)
            .location(float(eid), 0.0)
            .lifecycle(active=True)
            .combat(alive=True)
            .build()
        )
    building = BuildingState(id=100, kind="shop", position=(0, 0), functional=True)
    state = AuthoritativeState(tick=1, seed=42, entities=entities)
    return replace(state, buildings={100: building})


def _raw_update_with_building_mutation() -> StateUpdate:
    """A raw incoming update with no entity_updates but one real building mutation."""
    return StateUpdate(
        dirty_set=None,
        entity_updates={},
        building_updates={100: BuildingUpdate(building_id=100, hp_delta=-5)},
    )


def test_refine_forces_full_dirty_set_when_force_full_scan_true_with_no_entity_updates():
    """
    Given no entity produces any EntityUpdate this tick, force_full_scan=True must still make
    refine()'s returned dirty_set cover every entity across all nine entity/town domains -- this
    is the crux regression this ticket fixes; before the fix this assertion fails because
    DirtySetBuilder.mark_from_update() only marks entities with real field changes.
    """
    state = _idle_entities_state()
    update = _raw_update_with_building_mutation()

    refined = AuthoritativeApplyPipeline.refine(state, update, force_full_scan=True)

    all_ids = set(state.entities.keys())
    ds = refined.dirty_set
    assert ds.all_dirty_entities == all_ids
    assert ds.movement_entities == all_ids
    assert ds.combat_entities == all_ids
    assert ds.inventory_entities == all_ids
    assert ds.strategic_entities == all_ids
    assert ds.social_entities == all_ids
    assert ds.lifecycle_entities == all_ids
    assert ds.biological_entities == all_ids
    assert ds.attribute_entities == all_ids
    assert ds.town_entities == state.town_entity_ids

    # Correction 2 regression guard: the eight non-entity DirtySet domains that
    # dirty_builder.build() already computed correctly (e.g. building_ids from the real
    # building mutation above) must survive the force_full_scan override verbatim -- a bare
    # DirtySet(...) reconstruction (the original dead _refresh_dirty_set's shape) would have
    # silently zeroed them out instead of preserving them via dataclasses.replace().
    assert 100 in ds.building_ids

    # Folded test 5: force_full_scan widens the *reported* dirty set for downstream consumers,
    # it does not change what actually happened in the tick. With no genuine entity mutation,
    # an equivalent force_full_scan=False run produces a strictly smaller (here, entity-empty)
    # dirty set over the identical unmutated entity population -- documenting that dirty-set
    # completeness and simulation outcome are independent concerns.
    state_2 = _idle_entities_state()
    update_2 = _raw_update_with_building_mutation()
    refined_default = AuthoritativeApplyPipeline.refine(state_2, update_2)
    assert refined_default.dirty_set.all_dirty_entities != all_ids
    assert refined.entity_updates == refined_default.entity_updates


def test_refine_does_not_force_full_dirty_set_when_force_full_scan_false():
    """
    Anti-drift guard: without force_full_scan, refine()'s final dirty set must stay exactly what
    DirtySetBuilder computed from real mutations -- not widened to all entities. This is the
    direct guard against wiring the relocated full-scan logic in unconditionally (or accidentally
    also wiring in the unsafe DirtySet.from_update() branch from the now-deleted
    _refresh_dirty_set, which would reintroduce the documented e_upd.task discrepancy).
    """
    state = _idle_entities_state()
    update = _raw_update_with_building_mutation()

    refined = AuthoritativeApplyPipeline.refine(state, update, force_full_scan=False)

    all_ids = set(state.entities.keys())
    ds = refined.dirty_set
    assert ds.all_dirty_entities != all_ids
    assert ds.all_dirty_entities <= all_ids
    assert ds.movement_entities == set()
    assert ds.combat_entities == set()
    # The building mutation is still real and must still be tracked regardless of force_full_scan.
    assert 100 in ds.building_ids


def test_v2_engine_manager_ws_delta_changed_includes_every_alive_entity_under_force_full_scan():
    """
    AC2/Scope bullet 3: a force_full_scan=True-booted Kernel must produce a WS delta (via
    ReadModelCache.compute_tick_delta, exactly as V2EngineManager._update_latest_state calls it)
    whose `changed` list contains every live entity -- not just widen internal phase routing.

    Before the fix this fails via the RuntimeStatus gap (AC3): getattr(kernel.status,
    "force_full_scan", False) always returned False, so compute_tick_delta never saw
    force_full_scan=True regardless of how the Kernel was booted.

    Observability mode is pinned explicitly (not left at ambient default) so this test exercises
    the real _run_hard_law_checks-populated dirty_set path rather than accidentally passing via
    the `dirty_set is None -> invalidate everything` fallback.
    """
    ObservabilityConfig.clear_all_overrides()
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)
    try:
        profile = RuntimeProfile(
            name="test-force-full-scan-ws",
            hardware_class=HardwareClass.CLASS_B,
            max_ram_mb=1024,
            max_cpu_percent=100.0,
            max_worker_count=1,
            max_queue_depth=100,
            max_replay_buffer_kb=0,
            max_observability_budget_percent=0.0,
            max_tick_budget_ms=16.6,
        )
        state = _idle_entities_state()
        rng = DeterministicRNG(42)
        kernel = Kernel(profile, state, rng, flags={"force_full_scan": True})
        try:
            kernel.tick_once()

            dirty_set = getattr(kernel.status, "dirty_set", None)
            force_full = getattr(kernel.status, "force_full_scan", False)
            assert force_full is True

            payload = ReadModelCache().compute_tick_delta(
                kernel.state, dirty_set, force_full, kernel.state.tick
            )

            alive_ids = {
                eid for eid, ent in kernel.state.entities.items() if ent.combat.alive
            }
            changed_ids = {entry["id"] for entry in payload["changed"]}
            assert changed_ids == alive_ids
        finally:
            kernel.shutdown()
    finally:
        ObservabilityConfig.clear_all_overrides()
