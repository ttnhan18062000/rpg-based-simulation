# tests/engine/test_spatial_index.py
import pytest
from src_legacy.engine.spatial import SpatialIndexV2

def test_spatial_index_point_query():
    index = SpatialIndexV2()
    index.add(1, (10, 10))
    index.add(2, (10, 10)) # Two entities on same tile
    index.add(3, (11, 11))
    
    assert index.get_occupants((10, 10)) == {1, 2}
    assert index.get_occupants((11, 11)) == {3}
    assert index.get_occupants((12, 12)) == set()

def test_spatial_index_remove():
    index = SpatialIndexV2()
    index.add(1, (10, 10))
    index.remove(1)
    assert index.get_occupants((10, 10)) == set()

def test_spatial_index_move():
    index = SpatialIndexV2()
    index.add(1, (10, 10))
    index.update(1, (11, 11))
    assert index.get_occupants((10, 10)) == set()
    assert index.get_occupants((11, 11)) == {1}

def test_spatial_index_query_radius():
    index = SpatialIndexV2()
    index.add(1, (10, 10))
    index.add(2, (11, 10)) # Dist 1
    index.add(3, (10, 12)) # Dist 2
    index.add(4, (12, 12)) # Dist 4
    
    # Radius 1
    results = index.query_radius((10, 10), 1)
    assert set(results) == {1, 2}
    
    # Radius 2
    results = index.query_radius((10, 10), 2)
    assert set(results) == {1, 2, 3}
    
    # Radius 5
    results = index.query_radius((10, 10), 5)
    assert set(results) == {1, 2, 3, 4}

def test_spatial_index_bounding_box_optimization():
    # Verify that query_radius doesn't check the entire world
    # This is more of an implementation detail but good to check coverage
    index = SpatialIndexV2()
    index.add(1, (100, 100))
    
    # Query far away
    results = index.query_radius((0, 0), 10)
    assert results == []
