# tests/engine/test_spatial_index.py
import pytest
from src.engine.spatial import SpatialGrid
from src.core.builder import V2EntityBuilder

def create_mock_entity(eid, pos):
    return (V2EntityBuilder(eid)
            .at(pos)
            .build())

def test_spatial_grid_coarse_filtering():
    entities = {
        1: create_mock_entity(1, (5, 5)),
        2: create_mock_entity(2, (15, 15)),
        3: create_mock_entity(3, (50, 50))
    }
    grid = SpatialGrid(entities, cell_size=10)

    # Query near (0,0) with radius 10
    # SpatialGrid returns all entities in cells covered by radius + 1 cell buffer
    candidates = grid.get_neighbors((0, 0), 10)
    assert 1 in candidates
    assert 2 in candidates # Coarse filtering includes cell (1,1)
    assert 3 not in candidates # Far away in cell (5,5)

def test_spatial_grid_rebuild_logic():
    # Initial state
    entities = {1: create_mock_entity(1, (5, 5))}
    grid = SpatialGrid(entities, cell_size=10)
    assert 1 in grid.get_neighbors((5, 5), 5)

    # Move entity 1 (rebuild grid)
    entities[1] = (V2EntityBuilder(1)
                   .at((100, 100))
                   .build())
    grid_moved = SpatialGrid(entities, cell_size=10)
    assert not grid_moved.get_neighbors((5, 5), 5)
    assert 1 in grid_moved.get_neighbors((100, 100), 5)

    # Remove entity 1 (rebuild grid)
    entities_empty = {}
    grid_empty = SpatialGrid(entities_empty, cell_size=10)
    assert not grid_empty.get_neighbors((100, 100), 5)
