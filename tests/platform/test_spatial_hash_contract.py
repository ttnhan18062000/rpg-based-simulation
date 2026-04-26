# tests/platform/test_spatial_hash_contract.py
import pytest
from src.platform.spatial_hash import SpatialHashV2

def test_spatial_hash_contract():
    idx = SpatialHashV2(cell_size=10)
    idx.update_entity(1, (5, 5))
    idx.update_entity(2, (15, 15))
    
    # Radius query
    assert idx.query_radius((0, 0), 10) == [1]
    assert idx.query_radius((20, 20), 10) == [2]
    
    # Move entity
    idx.update_entity(1, (100, 100))
    assert idx.query_radius((5, 5), 5) == []
    assert idx.query_radius((100, 100), 5) == [1]
    
    # Remove
    idx.remove_entity(1)
    assert idx.query_radius((100, 100), 5) == []
