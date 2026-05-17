# Compliance IDs: PERF-007, PERF-010
import pytest
from src.core.state import AuthoritativeState, ResourceNodeState, BuildingState
from src.engine.spatial_query import SpatialQueryService
from src.ai.goals.scorers import HarvestScorer, SleepScorer, EatScorer
from tests.helpers.entities import make_hero, make_state


@pytest.fixture
def test_world() -> AuthoritativeState:
    hero1 = make_hero(1, pos=(10.0, 10.0), alive=True, active=True, sleep_debt=50.0, hunger=50.0)
    hero2 = make_hero(2, pos=(12.0, 10.0), alive=True, active=True)
    hero3 = make_hero(3, pos=(100.0, 100.0), alive=True, active=True)

    node1 = ResourceNodeState(id=1, kind="tree", position=(15.0, 15.0), yields_item="wood", remaining_charges=5, max_charges=10, required_ticks=5, cooldown_remaining=0)
    node2 = ResourceNodeState(id=2, kind="rock", position=(80.0, 80.0), yields_item="stone", remaining_charges=5, max_charges=10, required_ticks=5, cooldown_remaining=0)

    bldg1 = BuildingState(id=1, kind="inn", position=(20.0, 20.0))
    bldg2 = BuildingState(id=2, kind="tavern", position=(30.0, 30.0))
    bldg3 = BuildingState(id=3, kind="inn", position=(90.0, 90.0))

    state = make_state(entities=[hero1, hero2, hero3], buildings=[bldg1, bldg2, bldg3])
    object.__setattr__(state, "resource_nodes", {1: node1, 2: node2})
    return state


def test_spatial_query_nearest_resource_matches_naive_scan(test_world: AuthoritativeState):
    # Query from (10, 10)
    res = SpatialQueryService.nearest_resource_node(test_world, (10.0, 10.0))
    assert res is not None
    assert res.id == 1

    # Query from (90, 90)
    res2 = SpatialQueryService.nearest_resource_node(test_world, (90.0, 90.0))
    assert res2 is not None
    assert res2.id == 2


def test_spatial_query_nearest_building_matches_naive_scan(test_world: AuthoritativeState):
    # Query inn from (10, 10)
    inn1 = SpatialQueryService.nearest_building(test_world, (10.0, 10.0), "inn")
    assert inn1 is not None
    assert inn1.id == 1

    # Query inn from (100, 100)
    inn2 = SpatialQueryService.nearest_building(test_world, (100.0, 100.0), "inn")
    assert inn2 is not None
    assert inn2.id == 3

    # Query tavern
    tavern = SpatialQueryService.nearest_building(test_world, (10.0, 10.0), "tavern")
    assert tavern is not None
    assert tavern.id == 2


def test_spatial_query_nearby_entities_matches_naive_scan(test_world: AuthoritativeState):
    # Query near (10, 10) with radius 5
    # hero1 is at (10, 10), hero2 is at (12, 10)
    entities = SpatialQueryService.nearby_entities(test_world, (10.0, 10.0), radius=5.0)
    assert set(entities) == {1, 2}

    # Query near (100, 100) with radius 5
    # hero3 is at (100, 100)
    entities2 = SpatialQueryService.nearby_entities(test_world, (100.0, 100.0), radius=5.0)
    assert set(entities2) == {3}


def test_scorers_use_spatial_query_without_attaching_hidden_caches(test_world: AuthoritativeState):
    hero = test_world.entities[1]
    
    harvest_score = HarvestScorer().score(hero, test_world)
    sleep_score = SleepScorer().score(hero, test_world)
    eat_score = EatScorer().score(hero, test_world)

    assert harvest_score.utility > 0
    assert sleep_score.utility > 0
    assert eat_score.utility > 0

    # Ensure no legacy ad-hoc caches were attached to state
    assert getattr(test_world, "_active_nodes_grid") is None
    assert not hasattr(test_world, "_inns_cache")
    assert not hasattr(test_world, "_taverns_cache")
