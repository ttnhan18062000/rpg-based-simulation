"""World extent, the intercept lead and a held pursuit target (TCK-20261009-PURSUING-GUARDS-OFF-THE-MAP).

Bible 06 (topology): the world is its declared regions; a tile outside them is not part of the world.
"""
from src.core.builder import V2EntityBuilder
from src.core.dirty import DirtySet
from src.core.enums import ReasonCode
from src.core.state import AuthoritativeState, RegionState
from src.engine.legality import LegalityServiceV2
from src.engine.positioning import PositioningService
from src.core.region_resolution import is_inside_world, world_extent
from src.engine.tactical import _target_still_perceived
from src.observability.hard_law_monitor import HardLawMonitor


def _state(entities=None) -> AuthoritativeState:
    region = RegionState(id="r1", name="r1", bounds=(10, 10, 100, 60))
    return AuthoritativeState(tick=1, seed=42, entities=entities or {}, regions={"r1": region})


def test_world_extent_is_the_union_of_declared_regions():
    state = _state()
    state.regions["r2"] = RegionState(id="r2", name="r2", bounds=(100, 0, 140, 60))
    assert world_extent(state) == (10, 0, 140, 60)
    assert is_inside_world(state, (120.0, 5.0))
    assert not is_inside_world(state, (9.0, 30.0))


def test_a_world_without_declared_regions_has_no_extent_to_violate():
    state = AuthoritativeState(tick=1, seed=42)
    assert world_extent(state) is None
    assert is_inside_world(state, (-500.0, 9999.0))


def test_occupancy_refuses_a_tile_outside_the_world_with_a_typed_reason():
    state = _state()
    ok, reason = LegalityServiceV2.verify_occupancy((30.0, 9.0), state)
    assert not ok and reason == ReasonCode.OUT_OF_BOUNDS
    ok, _ = LegalityServiceV2.verify_occupancy((30.0, 10.0), state)
    assert ok


def test_hard_law_names_an_entity_committed_outside_the_world():
    outside = V2EntityBuilder(1).location(36.0, 9.0).build()
    inside = V2EntityBuilder(2).location(36.0, 12.0).build()
    state = _state({1: outside, 2: inside})
    violations = HardLawMonitor.check_entities(state, DirtySet(combat_entities={1, 2}))
    assert [(v.law_id, v.entity_id) for v in violations] == [("LAW-POSITION-IN-WORLD", 1)]


def test_a_chaser_aims_at_where_a_pursuing_target_is_not_ahead_of_it():
    # The target's own aim point is another intercept point; leading it leads a lead that stays ahead for ever.
    chaser = V2EntityBuilder(1).location(40.0, 30.0).build()
    pursuing = (
        V2EntityBuilder(2).location(36.0, 20.0)
        .navigation(target=(36.0, 14.0))
        .task(work_kind="ENTITY_MOVE", payload={"target_id": 1, "reason": "INTERCEPTING"})
        .build()
    )
    assert PositioningService.find_intercept_position(chaser, pursuing, _state({1: chaser, 2: pursuing})) == (36.0, 20.0)


def test_a_chaser_still_leads_a_target_walking_to_a_destination():
    chaser = V2EntityBuilder(1).location(40.0, 30.0).build()
    walker = V2EntityBuilder(2).location(36.0, 20.0).navigation(target=(36.0, 14.0)).build()
    assert PositioningService.find_intercept_position(chaser, walker, _state({1: chaser, 2: walker})) == (36.0, 18.0)


def test_a_held_pursuit_target_is_kept_in_view_and_let_go_beyond_it():
    chaser = V2EntityBuilder(1).location(40.0, 30.0).build()
    near = V2EntityBuilder(2).location(42.0, 30.0).build()
    far = V2EntityBuilder(3).location(40.0, 3000.0).build()
    assert _target_still_perceived(chaser, near)
    assert not _target_still_perceived(chaser, far)
