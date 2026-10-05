"""The one position-to-region rule, and every path that must agree with it.

Mechanics Bible 06 (Region Overlap Resolution): regions may overlap. A point resolves to the region with the
smallest area that contains it, membership is inclusive on all four edges, equal areas go to the earlier-declared
region, and a point in no region resolves to None (unclaimed space).

Before the rule, ``get_region_at`` returned the first-declared match with half-open bounds, ``DomainView`` used
closed bounds, and two inline loops did their own thing. These tests pin the rule and the agreement between the
paths that previously disagreed.
"""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.region_resolution import resolve_region_among
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.cadence import SystemCadence
from src.engine.domain.view import DomainView
from src.engine.spatial_query import SpatialQueryService
from src.engine.world_dynamics import WorldDynamicsSystem
from src.systems.social_systems.memory import SocialMemoryService
from src.systems.world_systems.generator import EntityGenerator


def _state(*regions: RegionState, **kw) -> AuthoritativeState:
    return AuthoritativeState(tick=0, seed=42, regions={r.id: r for r in regions}, **kw)


def _r(rid: str, bounds) -> RegionState:
    return RegionState(id=rid, name=rid, bounds=bounds)


def _at(state, x, y):
    region = SpatialQueryService.get_region_at(state, (x, y))
    return region.id if region else None


# ---- the rule ---------------------------------------------------------------------------


@pytest.mark.parametrize("big_first", [True, False])
def test_the_smallest_containing_region_wins_whatever_the_declaration_order(big_first):
    big = _r("bandit_road", (40, 40, 100, 60))      # 60 x 20 = 1200
    mid = _r("near_forest", (45, 10, 90, 55))        # 45 x 45 = 2025 (declared later in one order)
    small = _r("wolf_den", (70, 30, 105, 70))        # 35 x 40 = 1400
    nested_small = _r("den_mouth", (80, 40, 90, 50)) # 10 x 10 = 100
    order = [big, mid, small, nested_small] if big_first else [nested_small, small, mid, big]
    state = _state(*order)
    assert _at(state, 85, 45) == "den_mouth"  # inside all four: smallest area
    assert _at(state, 75, 45) == "bandit_road"  # inside bandit_road (1200), near_forest (2025), wolf_den (1400)
    assert _at(state, 60, 20) == "near_forest"  # only near_forest contains it


def test_equal_areas_go_to_the_earlier_declared_region_and_the_choice_is_stable():
    a = _r("alpha", (0, 0, 10, 10))
    b = _r("beta", (5, 5, 15, 15))  # same 10 x 10 area, overlaps alpha on (5..10, 5..10)
    assert _at(_state(a, b), 7, 7) == "alpha"
    assert _at(_state(b, a), 7, 7) == "beta"
    state = _state(a, b)
    assert {_at(state, 7, 7) for _ in range(200)} == {"alpha"}


def test_the_area_used_is_the_bounds_area_the_codebase_already_uses():
    thin_and_long = _r("thin", (0, 0, 2, 20))   # 2 * 20 = 40
    short_and_wide = _r("fat", (0, 0, 7, 6))    # 7 * 6 = 42
    assert _at(_state(short_and_wide, thin_and_long), 1, 1) == "thin"


def test_edges_are_inclusive_so_a_death_on_a_far_edge_is_in_its_region():
    hometown = _r("hometown", (10, 10, 40, 40))
    state = _state(hometown)
    # (29, 40) is the one measured death that the old half-open lookup credited to no region.
    for x, y in [(29, 40), (40, 40), (10, 10), (40, 10), (10, 40)]:
        assert _at(state, x, y) == "hometown", (x, y)
    for x, y in [(41, 40), (9, 10), (29, 41), (29, 9)]:
        assert _at(state, x, y) is None, (x, y)


def test_a_shared_edge_belongs_to_the_smaller_region_then_the_earlier_one():
    left = _r("left", (0, 0, 10, 10))      # 100
    right = _r("right", (10, 0, 20, 10))   # 100, shares the x = 10 edge
    assert _at(_state(left, right), 10, 5) == "left"
    assert _at(_state(right, left), 10, 5) == "right"
    smaller = _r("small_right", (10, 0, 14, 10))  # 40
    assert _at(_state(left, smaller), 10, 5) == "small_right"


def test_a_point_in_no_region_is_none_not_an_error():
    state = _state(_r("only", (10, 10, 20, 20)))
    assert _at(state, 0, 0) is None
    assert _at(state, 5, 15) is None
    assert _at(state, 1000, 1000) is None
    assert SpatialQueryService.get_region_at(_state(), (5, 5)) is None


def test_a_point_on_a_grid_cell_boundary_is_found():
    # The lookup index buckets by 50-unit cells; a region ending exactly on a cell edge must still match there.
    state = _state(_r("edge", (20, 20, 100, 100)))
    assert _at(state, 100, 100) == "edge"
    assert _at(state, 50, 50) == "edge"


# ---- the paths that must agree with it ---------------------------------------------------


def _overlapping_layout():
    return _state(
        _r("bandit_road", (40, 40, 100, 60)),
        _r("near_forest", (45, 10, 90, 55)),
        _r("wolf_den", (70, 30, 105, 70)),
        _r("hometown", (10, 10, 40, 40)),
    )


def test_domainview_and_spatialquery_agree_on_every_point_including_edges():
    state = _overlapping_layout()
    for x in range(0, 115, 5):
        for y in range(0, 80, 5):
            expected = SpatialQueryService.get_region_at(state, (x, y))
            actual = DomainView.get_region_for_position(state, (x, y))
            assert (actual.id if actual else None) == (expected.id if expected else None), (x, y)


def test_domainview_on_a_state_with_only_a_region_list_uses_the_same_rule():
    regions = [_r("outer", (0, 0, 100, 100)), _r("inner", (40, 40, 60, 60))]
    state = SimpleNamespace(regions={}, region_list=regions)
    assert DomainView.get_region_for_position(state, (50, 50)).id == "inner"
    assert DomainView.get_region_for_position(state, (10, 10)).id == "outer"
    assert DomainView.get_region_for_position(state, (200, 10)) is None


def test_trauma_reads_the_region_trauma_was_credited_to():
    outer = RegionState(id="outer", name="outer", bounds=(0, 0, 100, 100), trauma_score=7.0)
    inner = RegionState(id="inner", name="inner", bounds=(40, 40, 60, 60), trauma_score=3.0)
    state = _state(outer, inner)
    assert DomainView.get_region_trauma(state, (50, 50)) == 3.0
    assert DomainView.get_region_trauma(state, (10, 10)) == 7.0
    assert DomainView.get_region_trauma(state, (500, 500)) == 0.0


def _entity(eid: int, x: float, y: float):
    return V2EntityBuilder(eid).kind("scout").location(x, y).combat(hp=10, max_hp=10, alive=True).build()


def _death_update(eid: int) -> StateUpdate:
    return StateUpdate(entity_updates={eid: EntityUpdate(entity_id=eid, combat=CombatUpdate(alive_set=False, outcome_kind="KILL"))})


def _trauma_after_death(state, entity):
    refined = WorldDynamicsSystem.resolve_dynamics(
        replace(state, entities={entity.id: entity}), _death_update(entity.id), EntityGenerator(42)
    )
    return {rid: w.trauma_delta for rid, w in refined.world_updates.items() if w.trauma_delta}


def test_a_death_in_an_overlap_credits_only_the_smallest_containing_region():
    state = _overlapping_layout()
    # (75, 45) lies inside bandit_road (1200), near_forest (2025) and wolf_den (1400): bandit_road is smallest.
    assert _trauma_after_death(state, _entity(1, 75, 45)) == {"bandit_road": 1.0}
    # (95, 65) lies only inside wolf_den.
    assert _trauma_after_death(state, _entity(2, 95, 65)) == {"wolf_den": 1.0}


def test_a_death_on_a_far_edge_credits_its_region():
    state = _state(_r("hometown", (10, 10, 40, 40)))
    assert _trauma_after_death(state, _entity(3, 29, 40)) == {"hometown": 1.0}


def test_a_death_in_unclaimed_space_adds_no_trauma_anywhere_by_design():
    state = _overlapping_layout()
    assert _trauma_after_death(state, _entity(4, 2, 2)) == {}


def test_a_moved_entitys_region_id_follows_the_rule_not_its_old_region():
    state = _overlapping_layout()
    entity = _entity(5, 50, 20)  # inside near_forest only
    entity = replace(entity, navigation=replace(entity.navigation, region_id="near_forest"))
    state = replace(state, entities={5: entity})
    # Moving to (75, 45) stays inside near_forest, but bandit_road (smaller) now contains the point too.
    changes = ApplyPath._compute_entity_changes(
        entity, EntityUpdate(entity_id=5, new_position=(75.0, 45.0)), 1, SystemCadence(), False, True,
        list(state.regions.values()), state,
    )
    assert changes["navigation"].region_id == "bandit_road"


def test_a_moved_entitys_region_id_clears_when_it_leaves_every_region():
    state = _overlapping_layout()
    entity = _entity(6, 50, 20)
    entity = replace(entity, navigation=replace(entity.navigation, region_id="near_forest"))
    state = replace(state, entities={6: entity})
    changes = ApplyPath._compute_entity_changes(
        entity, EntityUpdate(entity_id=6, new_position=(3.0, 3.0)), 1, SystemCadence(), False, True,
        list(state.regions.values()), state,
    )
    assert changes["navigation"].region_id is None


def test_place_attachment_falls_back_to_the_same_lookup():
    state = _overlapping_layout()
    update = SocialMemoryService.tick_place_attachment(_entity(7, 75, 45), state)
    assert update is not None and set(update.place_attachment_delta) == {"bandit_road"}
    assert SocialMemoryService.tick_place_attachment(_entity(8, 2, 2), state) is None


# ---- the rule itself, over a plain candidate list ----------------------------------------


def test_the_core_rule_is_order_sensitive_only_on_ties():
    small, big = _r("small", (0, 0, 4, 4)), _r("big", (0, 0, 20, 20))
    assert resolve_region_among([big, small], 2, 2).id == "small"
    assert resolve_region_among([small, big], 2, 2).id == "small"
    twin_a, twin_b = _r("a", (0, 0, 5, 5)), _r("b", (0, 0, 5, 5))
    assert resolve_region_among([twin_a, twin_b], 2, 2).id == "a"
    assert resolve_region_among([twin_b, twin_a], 2, 2).id == "b"
    assert resolve_region_among([], 2, 2) is None
    assert resolve_region_among(iter([small]), 9, 9) is None
