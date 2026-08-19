# Compliance IDs: PERF-010, PERF-011
import pytest
from src.core.state import AuthoritativeState, ResourceNodeState, BuildingState
from src.core.dirty import DirtySet
from src.engine.world_index import WorldIndexService


@pytest.fixture
def mock_state() -> AuthoritativeState:
    node1 = ResourceNodeState(id=1, kind="tree", position=(10.0, 10.0), yields_item="wood", remaining_charges=5, max_charges=10, required_ticks=5, cooldown_remaining=0)
    node2 = ResourceNodeState(id=2, kind="tree", position=(50.0, 50.0), yields_item="wood", remaining_charges=0, max_charges=10, required_ticks=5, cooldown_remaining=0) # depleted
    node3 = ResourceNodeState(id=3, kind="tree", position=(90.0, 90.0), yields_item="wood", remaining_charges=5, max_charges=10, required_ticks=5, cooldown_remaining=10) # on cooldown

    bldg1 = BuildingState(id=1, kind="inn", position=(15.0, 15.0))
    bldg2 = BuildingState(id=2, kind="tavern", position=(25.0, 25.0))
    bldg3 = BuildingState(id=3, kind="inn", position=(35.0, 35.0))

    return AuthoritativeState(
        tick=100,
        seed=42,
        world_time=1000,
        resource_nodes={1: node1, 2: node2, 3: node3},
        buildings={1: bldg1, 2: bldg2, 3: bldg3}
    )


def test_world_index_builds_active_resource_node_index(mock_state: AuthoritativeState):
    indexes = WorldIndexService.get_indexes(mock_state)
    
    # Node 1 is at (10, 10), chunk is (0, 0)
    assert (0, 0) in indexes.active_resource_nodes.grid
    assert 1 in indexes.active_resource_nodes.grid[(0, 0)]


def test_world_index_excludes_depleted_resource_nodes(mock_state: AuthoritativeState):
    indexes = WorldIndexService.get_indexes(mock_state)
    
    # Node 2 is depleted (50, 50 -> chunk 2, 2)
    # Node 3 is cooling down (90, 90 -> chunk 4, 4)
    all_indexed_nodes = set()
    for n_ids in indexes.active_resource_nodes.grid.values():
        all_indexed_nodes.update(n_ids)
        
    assert 2 not in all_indexed_nodes
    assert 3 not in all_indexed_nodes
    assert 1 in all_indexed_nodes


def test_world_index_builds_buildings_by_kind(mock_state: AuthoritativeState):
    indexes = WorldIndexService.get_indexes(mock_state)
    
    assert set(indexes.buildings_by_kind["inn"]) == {1, 3}
    assert set(indexes.buildings_by_kind["tavern"]) == {2}


def test_world_index_reuses_index_when_tick_and_dirty_domains_unchanged(mock_state: AuthoritativeState):
    idx1 = WorldIndexService.get_indexes(mock_state)
    idx2 = WorldIndexService.get_indexes(mock_state)
    assert idx1 is idx2


def test_world_index_invalidates_resource_index_when_resource_node_dirty(mock_state: AuthoritativeState):
    idx1 = WorldIndexService.get_indexes(mock_state)
    res_grid1 = idx1.active_resource_nodes

    # Advance tick, but dirty set only has resource nodes
    dirty = DirtySet(resource_node_ids={1})
    next_state = AuthoritativeState(
        tick=101, seed=mock_state.seed, world_time=1001,
        resource_nodes=mock_state.resource_nodes, buildings=mock_state.buildings,
        world_indexes=idx1
    )
    
    idx2 = WorldIndexService.get_indexes(next_state, dirty)
    assert idx2.tick == 101
    assert idx2.active_resource_nodes is not res_grid1
    # Building index should be reused since buildings weren't dirty
    assert idx2.buildings_by_kind is idx1.buildings_by_kind


def test_world_index_invalidates_building_index_when_building_dirty(mock_state: AuthoritativeState):
    idx1 = WorldIndexService.get_indexes(mock_state)

    dirty = DirtySet(building_ids={1})
    next_state = AuthoritativeState(
        tick=101, seed=mock_state.seed, world_time=1001,
        resource_nodes=mock_state.resource_nodes, buildings=mock_state.buildings,
        world_indexes=idx1
    )
    
    idx2 = WorldIndexService.get_indexes(next_state, dirty)
    assert idx2.buildings_by_kind is not idx1.buildings_by_kind
    # Resource index should be reused since resources weren't dirty
    assert idx2.active_resource_nodes is idx1.active_resource_nodes
