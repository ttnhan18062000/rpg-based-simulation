# tests/engine/test_spatial_index.py
import pytest
from src.engine.spatial import SpatialIndexV2

def test_spatial_index_basic_query():
    idx = SpatialIndexV2(cell_size=10)
    idx.update_entity(1, (5, 5))
    idx.update_entity(2, (15, 15))
    idx.update_entity(3, (50, 50))

    # Query near entity 1
    nearby = idx.query_radius((0, 0), 10)
    assert 1 in nearby
    assert 2 not in nearby
    assert 3 not in nearby

    # Query near entity 2
    nearby = idx.query_radius((20, 20), 10)
    assert 2 in nearby
    assert 1 not in nearby
    assert 3 not in nearby

def test_spatial_index_update_removal():
    idx = SpatialIndexV2(cell_size=10)
    idx.update_entity(1, (5, 5))
    
    # Move entity 1
    idx.update_entity(1, (100, 100))
    assert not idx.query_radius((5, 5), 5)
    assert 1 in idx.query_radius((100, 100), 5)

    # Remove entity 1
    idx.remove_entity(1)
    assert not idx.query_radius((100, 100), 5)
