# Compliance IDs: COMB-028, PERF-009
import pytest
import random
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.core.movement_modes import MovementMode
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.phase_governor import ScanPolicy


@pytest.fixture
def base_state() -> AuthoritativeState:
    # e1: Active, alive, target (20, 20), readiness 15 >= move_cost 10, cadence tick+id (100+1)%3 != 0 -> wait! Let's check cadence:
    # For e1, tick=100, id=1 -> (100+1) = 101 % 3 = 2 != 0.
    # To ensure e1 passes WANDER cadence, let's set e1 movement_mode=MovementMode.PURSUE or make (100+id)%3 == 0. (100+2)%3 == 0.
    # Let's set e1 mode to PURSUE so cadence doesn't skip it.
    e1 = (
        V2EntityBuilder(1)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0), movement_mode=MovementMode.PURSUE)
        .combat(alive=True, readiness=15.0, move_cost=10.0)
        .lifecycle(active=True)
        .build()
    )

    # e2: No target
    e2 = (
        V2EntityBuilder(2)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=None)
        .combat(alive=True, readiness=15.0)
        .lifecycle(active=True)
        .build()
    )

    # e3: Already at target
    e3 = (
        V2EntityBuilder(3)
        .kind("ACTOR")
        .location(30.0, 30.0)
        .navigation(target=(30.0, 30.0))
        .combat(alive=True, readiness=15.0)
        .lifecycle(active=True)
        .build()
    )

    # e4: Dead
    e4 = (
        V2EntityBuilder(4)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0))
        .combat(alive=False)
        .lifecycle(active=True)
        .build()
    )

    # e5: Inactive
    e5 = (
        V2EntityBuilder(5)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0))
        .combat(alive=True)
        .lifecycle(active=False)
        .build()
    )

    # e6: Low readiness (5 < 10)
    e6 = (
        V2EntityBuilder(6)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0), movement_mode=MovementMode.PURSUE)
        .combat(alive=True, readiness=5.0, move_cost=10.0)
        .lifecycle(active=True)
        .build()
    )

    return AuthoritativeState(
        tick=100, seed=42, world_time=100, entities={1: e1, 2: e2, 3: e3, 4: e4, 5: e5, 6: e6}
    )


def test_movement_selector_skips_entity_without_target(base_state: AuthoritativeState):
    update = StateUpdate()
    selected = MovementCandidateSelector.select(base_state, update, [2])
    assert 2 not in selected


def test_movement_selector_skips_entity_already_at_target(base_state: AuthoritativeState):
    update = StateUpdate()
    selected = MovementCandidateSelector.select(base_state, update, [3])
    assert 3 not in selected


def test_movement_selector_skips_inactive_or_dead_entity(base_state: AuthoritativeState):
    update = StateUpdate()
    selected = MovementCandidateSelector.select(base_state, update, [4, 5])
    assert 4 not in selected
    assert 5 not in selected


def test_movement_selector_includes_entity_with_target_and_readiness(
    base_state: AuthoritativeState,
):
    update = StateUpdate()
    selected = MovementCandidateSelector.select(base_state, update, [1])
    assert 1 in selected


def test_movement_selector_includes_entity_when_target_changed(base_state: AuthoritativeState):
    # e6 has low readiness, normally skipped
    update_normal = StateUpdate()
    assert 6 not in MovementCandidateSelector.select(base_state, update_normal, [6])

    # But if update sets a new target, it's included!
    update_changed = StateUpdate(
        entity_updates={
            6: EntityUpdate(
                entity_id=6, navigation=NavigationUpdate(target_set=(40.0, 40.0))
            )
        }
    )
    assert 6 in MovementCandidateSelector.select(base_state, update_changed, [6])


def test_movement_selector_force_full_scan_includes_all_movable_entities(
    base_state: AuthoritativeState,
):
    # e6 has low readiness, but force_full_scan overrides readiness gating
    update = StateUpdate(force_full_scan=True)
    selected = MovementCandidateSelector.select(base_state, update, base_state.entities.keys())
    assert 1 in selected
    assert 6 in selected
    assert 2 not in selected  # No target
    assert 3 not in selected  # Already at target
    assert 4 not in selected  # Dead
    assert 5 not in selected  # Inactive


def test_movement_selector_is_deterministic(base_state: AuthoritativeState):
    update = StateUpdate()
    candidates = list(base_state.entities.keys())

    results = []
    for _ in range(5):
        shuffled = list(candidates)
        random.shuffle(shuffled)
        res = MovementCandidateSelector.select(base_state, update, shuffled)
        results.append(res)

    for r in results[1:]:
        assert r == results[0]


# TCK-20260810-COMBAT-PURSUIT-STALE-TARGET-SNAPSHOT-NEVER-RETARGETS: a pursuing entity that
# "arrived" at a stale, one-time snapshot of its target's OLD position must not be permanently
# excluded from movement candidacy -- it must live-retrack the target's CURRENT position via
# task.payload["target_id"] and remain a candidate as long as it isn't there yet.

def test_resolve_live_tracking_target_returns_live_position_when_target_alive():
    pursuer = (
        V2EntityBuilder(10)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(10.0, 10.0))
        .combat(alive=True)
        .lifecycle(active=True)
        .task(work_kind="ENTITY_MOVE", payload={"target_id": 11, "target_position": (10.0, 10.0)})
        .build()
    )
    target = (
        V2EntityBuilder(11)
        .kind("ACTOR")
        .location(50.0, 50.0)
        .combat(alive=True)
        .lifecycle(active=True)
        .build()
    )
    entities = {10: pursuer, 11: target}
    result = MovementCandidateSelector.resolve_live_tracking_target(
        pursuer, entities, pursuer.navigation.target
    )
    assert result == (50.0, 50.0)


def test_resolve_live_tracking_target_falls_back_when_target_dead():
    pursuer = (
        V2EntityBuilder(10)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(10.0, 10.0))
        .combat(alive=True)
        .lifecycle(active=True)
        .task(work_kind="ENTITY_MOVE", payload={"target_id": 11, "target_position": (10.0, 10.0)})
        .build()
    )
    target = (
        V2EntityBuilder(11)
        .kind("ACTOR")
        .location(50.0, 50.0)
        .combat(alive=False)
        .lifecycle(active=True)
        .build()
    )
    entities = {10: pursuer, 11: target}
    fallback = pursuer.navigation.target
    result = MovementCandidateSelector.resolve_live_tracking_target(pursuer, entities, fallback)
    assert result == fallback


def test_resolve_live_tracking_target_falls_back_when_no_target_id():
    pursuer = (
        V2EntityBuilder(10)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(10.0, 10.0))
        .combat(alive=True)
        .lifecycle(active=True)
        .task(work_kind="ENTITY_MOVE", payload={})
        .build()
    )
    fallback = (99.0, 99.0)
    result = MovementCandidateSelector.resolve_live_tracking_target(pursuer, {}, fallback)
    assert result == fallback


def test_movement_selector_includes_pursuer_arrived_at_stale_snapshot_but_target_moved():
    """The exact bug: a pursuer whose persisted navigation.target equals its own current
    position (it "arrived" at a stale, one-time snapshot) must still be selected if
    task.payload["target_id"] points at a still-alive entity that is no longer at that stale
    position -- confirmed via live corpus trace (dungeon_crawl_seed42_2000t) to otherwise freeze
    two mutually-pursuing entities at a fixed distance for 990+ consecutive ticks."""
    pursuer = (
        V2EntityBuilder(20)
        .kind("ACTOR")
        .location(58.0, 60.0)
        .navigation(target=(58.0, 60.0), movement_mode=MovementMode.PURSUE)
        .combat(alive=True, readiness=100.0, move_cost=10.0)
        .lifecycle(active=True)
        .task(work_kind="ENTITY_MOVE", payload={"target_id": 21, "target_position": (58.0, 60.0)})
        .build()
    )
    target = (
        V2EntityBuilder(21)
        .kind("ACTOR")
        .location(57.0, 59.0)
        .combat(alive=True)
        .lifecycle(active=True)
        .build()
    )
    state = AuthoritativeState(tick=100, seed=42, entities={20: pursuer, 21: target})
    update = StateUpdate()
    selected = MovementCandidateSelector.select(state, update, [20])
    assert 20 in selected


def _starved_style_entity(entity_id: int) -> "EntityState":
    """A non-urgent entity with a real, unreached target and no active goal/interaction/project
    -- the exact TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION precondition. Uses
    PURSUE mode so WANDER's own separate cadence gate never interferes with the EXACT_DIRTY
    assertions below."""
    return (
        V2EntityBuilder(entity_id)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0), movement_mode=MovementMode.PURSUE)
        .combat(alive=True, readiness=100.0, move_cost=10.0)
        .lifecycle(active=True)
        .build()
    )


def test_exact_dirty_excludes_starved_entity_off_its_reduced_cadence_tick():
    entity = _starved_style_entity(1)
    modulo = MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO
    # tick + entity_id chosen deliberately NOT a multiple of the cadence.
    tick = modulo - 1 - 1  # (tick + 1) % modulo == modulo - 1 != 0
    state = AuthoritativeState(tick=tick, seed=42, entities={1: entity})
    update = StateUpdate()
    selected = MovementCandidateSelector.select(
        state, update, [1], scan_policy=ScanPolicy.EXACT_DIRTY
    )
    assert 1 not in selected


def test_exact_dirty_admits_starved_entity_on_its_reduced_cadence_tick():
    """The fix: an entity that can never satisfy any of the 5 urgency conditions on its own
    (a real, unreached target, no dirty/interaction/project/tile-block signal) used to be
    permanently excluded under EXACT_DIRTY -- a genuine starvation loop, not throttling. It must
    now be admitted on its own reduced cadence, guaranteeing eventual movement."""
    entity = _starved_style_entity(1)
    modulo = MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO
    tick = modulo - 1  # (tick + entity_id) % modulo == 0
    state = AuthoritativeState(tick=tick, seed=42, entities={1: entity})
    update = StateUpdate()
    selected = MovementCandidateSelector.select(
        state, update, [1], scan_policy=ScanPolicy.EXACT_DIRTY
    )
    assert 1 in selected


def test_exact_dirty_reduced_cadence_still_respects_real_readiness_gate():
    """The reduced-cadence admission is not a bypass of real gameplay mechanics -- an entity
    that genuinely cannot act this tick (low readiness) stays excluded even on its cadence
    tick."""
    entity = (
        V2EntityBuilder(1)
        .kind("ACTOR")
        .location(10.0, 10.0)
        .navigation(target=(20.0, 20.0), movement_mode=MovementMode.PURSUE)
        .combat(alive=True, readiness=5.0, move_cost=10.0)
        .lifecycle(active=True)
        .build()
    )
    modulo = MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO
    tick = modulo - 1
    state = AuthoritativeState(tick=tick, seed=42, entities={1: entity})
    update = StateUpdate()
    selected = MovementCandidateSelector.select(
        state, update, [1], scan_policy=ScanPolicy.EXACT_DIRTY
    )
    assert 1 not in selected


def test_exact_dirty_still_admits_genuinely_urgent_entities_every_tick():
    """EXACT_DIRTY's own real urgency bypasses (target_changed/is_dirty/tile_blocked/
    interaction_req/strategic_req) are untouched by the reduced-cadence fix -- a genuinely urgent
    entity is still selected every tick, not only on its reduced cadence."""
    entity = _starved_style_entity(1)
    modulo = MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO
    off_cadence_tick = modulo - 1 - 1
    state = AuthoritativeState(tick=off_cadence_tick, seed=42, entities={1: entity})
    update = StateUpdate(
        entity_updates={
            1: EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(40.0, 40.0)))
        }
    )
    selected = MovementCandidateSelector.select(
        state, update, [1], scan_policy=ScanPolicy.EXACT_DIRTY
    )
    assert 1 in selected


def test_exact_dirty_admits_only_a_bounded_fraction_per_tick():
    """The whole point of a reduced cadence rather than full re-admission: under real sustained
    load (many starved entities), only a small, bounded fraction should be admitted on any single
    tick -- not all of them, which would defeat EXACT_DIRTY's own work-shedding purpose."""
    modulo = MovementCandidateSelector.EXACT_DIRTY_STARVED_CADENCE_MODULO
    entities = {i: _starved_style_entity(i) for i in range(1, 201)}
    tick = 1000
    state = AuthoritativeState(tick=tick, seed=42, entities=entities)
    update = StateUpdate()
    selected = MovementCandidateSelector.select(
        state, update, list(entities.keys()), budget=10_000, scan_policy=ScanPolicy.EXACT_DIRTY
    )
    expected = {i for i in entities if (tick + i) % modulo == 0}
    assert set(selected) == expected
    assert 0 < len(selected) < len(entities)
