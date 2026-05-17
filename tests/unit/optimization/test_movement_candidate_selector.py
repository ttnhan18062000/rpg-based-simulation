# Compliance IDs: COMB-028, PERF-009
import pytest
import random
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.updates import StateUpdate, EntityUpdate, NavigationUpdate
from src.core.movement_modes import MovementMode
from src.engine.candidate_selector import MovementCandidateSelector


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
