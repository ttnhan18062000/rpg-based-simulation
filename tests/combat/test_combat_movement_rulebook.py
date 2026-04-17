import pytest
from src.core.models.vectors import Vector2
from src.core.logic.legality_service import LegalityService
from unittest.mock import MagicMock

def test_manhattan_distance():
    """Verify Manhattan distance calculation."""
    assert LegalityService.get_distance(Vector2(0, 0), Vector2(1, 0)) == 1
    assert LegalityService.get_distance(Vector2(0, 0), Vector2(1, 1)) == 2
    assert LegalityService.get_distance(Vector2(0, 0), Vector2(-2, -3)) == 5

def test_orthogonal_adjacency():
    """Verify that only orthogonal tiles are adjacent."""
    origin = Vector2(5, 5)
    # Orthogonal
    assert LegalityService.is_adjacent(origin, Vector2(6, 5)) is True
    assert LegalityService.is_adjacent(origin, Vector2(5, 4)) is True
    # Diagonal
    assert LegalityService.is_adjacent(origin, Vector2(6, 6)) is False
    # Same tile
    assert LegalityService.is_adjacent(origin, origin) is False
    # Far away
    assert LegalityService.is_adjacent(origin, Vector2(7, 5)) is False

def test_check_range():
    """Verify range enforcement."""
    origin = Vector2(0, 0)
    target = Vector2(2, 1) # Dist 3
    assert LegalityService.check_range(origin, target, 3) is True
    assert LegalityService.check_range(origin, target, 2) is False

def test_check_occupancy():
    """Verify 1-unit-per-tile occupancy rule."""
    world = MagicMock()
    pos = Vector2(10, 10)
    
    # Case: Empty tile
    world.get_entity_at.return_value = None
    assert LegalityService.check_occupancy(pos, world) is True
    
    # Case: Occupied tile
    world.get_entity_at.return_value = 123
    assert LegalityService.check_occupancy(pos, world) is False
    
    # Case: Occupied by self (ignore_entity_id)
    assert LegalityService.check_occupancy(pos, world, ignore_entity_id=123) is True

def test_aoe_legality():
    """Verify AoE impact constraints."""
    world = MagicMock()
    origin = Vector2(0, 0)
    impact = Vector2(2, 0)
    
    # Successful case
    world.grid.has_line_of_sight.return_value = True
    assert LegalityService.check_aoe_legality(origin, impact, 2, world) is True
    
    # Failed case: Range
    assert LegalityService.check_aoe_legality(origin, impact, 1, world) is False
    
    # Failed case: LOS
    world.grid.has_line_of_sight.return_value = False
    assert LegalityService.check_aoe_legality(origin, impact, 2, world) is False

def test_aoe_splash_radius():
    """Verify entities affected by splash radius."""
    world = MagicMock()
    impact = Vector2(5, 5)
    
    e1 = MagicMock(id=1); e1.spatial.pos = Vector2(6, 5) # Dist 1
    e2 = MagicMock(id=2); e2.spatial.pos = Vector2(6, 6) # Dist 2
    e3 = MagicMock(id=3); e3.spatial.pos = Vector2(7, 6) # Dist 3
    
    world.entities_at_radius.return_value = [e1, e2, e3]
    
    # Radius 2 should hit e1 and e2
    affected = LegalityService.get_affected_by_aoe(impact, 2, world)
    assert 1 in affected
    assert 2 in affected
    assert 3 not in affected
