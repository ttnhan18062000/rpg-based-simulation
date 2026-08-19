# Compliance IDs: COMB-002, COMB-003, PERF-008
import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, ReasonCode
from src.engine.occupancy_snapshot import OccupancySnapshot
from src.engine.legality import LegalityServiceV2


@pytest.fixture
def base_state() -> AuthoritativeState:
    e1 = (
        V2EntityBuilder(1)
        .kind("ACTOR")
        .location(10.0, 15.0)
        .identity(role=EntityRole.HERO)
        .combat(alive=True, hp=100.0, max_hp=100.0)
        .lifecycle(active=True)
        .build()
    )

    e2 = (
        V2EntityBuilder(2)
        .kind("ACTOR")
        .location(20.0, 25.0)
        .identity(role=EntityRole.MONSTER)
        .combat(alive=True, hp=10.0, max_hp=100.0) # hp < 30% -> +100 priority!
        .lifecycle(active=True)
        .build()
    )

    e3 = (
        V2EntityBuilder(3) # Dead entity
        .kind("ACTOR")
        .location(30.0, 35.0)
        .combat(alive=False)
        .lifecycle(active=True)
        .build()
    )

    e4 = (
        V2EntityBuilder(4) # Inactive entity
        .kind("ACTOR")
        .location(40.0, 45.0)
        .combat(alive=True)
        .lifecycle(active=False)
        .build()
    )

    state = AuthoritativeState(
        tick=100, seed=42, world_time=100, entities={1: e1, 2: e2, 3: e3, 4: e4}
    )
    snapshot = OccupancySnapshot.from_state(state)
    object.__setattr__(state, "occupancy_snapshot", snapshot)
    return state


def test_occupancy_snapshot_contains_entity_positions(base_state: AuthoritativeState):
    snap = base_state.occupancy_snapshot
    assert snap.tick == 100
    assert (10, 15) in snap.occupancy_by_tile
    assert snap.occupancy_by_tile[(10, 15)] == 1
    assert (20, 25) in snap.occupancy_by_tile
    assert snap.occupancy_by_tile[(20, 25)] == 2
    # Dead/Inactive should NOT be in occupancy
    assert (30, 35) not in snap.occupancy_by_tile
    assert (40, 45) not in snap.occupancy_by_tile


def test_occupancy_snapshot_reports_occupied_tile(base_state: AuthoritativeState):
    snap = base_state.occupancy_snapshot
    assert snap.is_occupied((10, 15)) is True
    assert snap.occupant_at((10, 15)) == 1


def test_occupancy_snapshot_reports_empty_tile(base_state: AuthoritativeState):
    snap = base_state.occupancy_snapshot
    assert snap.is_occupied((99, 99)) is False
    assert snap.occupant_at((99, 99)) is None


def test_occupancy_snapshot_is_stable_for_tick(base_state: AuthoritativeState):
    snap = base_state.occupancy_snapshot
    # Modify e1 position in state
    e1_mod = replace(base_state.entities[1], navigation=replace(base_state.entities[1].navigation, position=(50.0, 50.0)))
    state_mod = replace(base_state, entities={**base_state.entities, 1: e1_mod})
    object.__setattr__(state_mod, "occupancy_snapshot", snap)

    # Verify snapshot still reports original position
    assert snap.occupant_at((10, 15)) == 1
    assert snap.occupant_at((50, 50)) is None


def test_occupancy_snapshot_rebuilt_after_apply_changes_position(base_state: AuthoritativeState):
    e1_mod = replace(base_state.entities[1], navigation=replace(base_state.entities[1].navigation, position=(50.0, 50.0)))
    state_next = replace(base_state, tick=101, entities={**base_state.entities, 1: e1_mod})
    
    snap_next = OccupancySnapshot.from_state(state_next)
    object.__setattr__(state_next, "occupancy_snapshot", snap_next)

    assert snap_next.tick == 101
    assert snap_next.occupant_at((10, 15)) is None
    assert snap_next.occupant_at((50, 50)) == 1


def test_movement_legality_uses_snapshot_result_equivalent_to_current_logic(base_state: AuthoritativeState):
    # Verify occupancy check via LegalityServiceV2
    ok_occ, reason_occ = LegalityServiceV2.verify_occupancy((10, 15), base_state)
    assert ok_occ is False
    assert reason_occ == ReasonCode.OCCUPANCY_VIOLATION

    ok_empty, reason_empty = LegalityServiceV2.verify_occupancy((99, 99), base_state)
    assert ok_empty is True
    assert reason_empty == ReasonCode.LEGAL

    # Verify priority calculations
    prio_1 = LegalityServiceV2.get_entity_priority(base_state.entities[1], base_state)
    # e1: HERO (100) + full hp (0) = 100
    assert prio_1 == 100

    prio_2 = LegalityServiceV2.get_entity_priority(base_state.entities[2], base_state)
    # e2: MONSTER (50) + hp < 0.3 (100) = 150
    assert prio_2 == 150
