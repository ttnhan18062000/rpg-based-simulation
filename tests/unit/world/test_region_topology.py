import pytest
from src.core.state import AuthoritativeState, RegionState
from src.world.regions import RegionService

def test_find_region_at_bounds():
    r1 = RegionState(id="r1", name="R1", bounds=(0, 0, 10, 10))
    r2 = RegionState(id="r2", name="R2", bounds=(20, 20, 30, 30))
    state = AuthoritativeState(tick=0, seed=42, regions={"r1": r1, "r2": r2})
    
    # Inside r1
    assert RegionService.find_region_at(state, (5, 5)).id == "r1"
    # Inside r2
    assert RegionService.find_region_at(state, (25, 25)).id == "r2"

def test_find_region_at_fallback_nearest():
    # Only one region at (0,0)
    r1 = RegionState(id="r1", name="R1", bounds=(0, 0, 10, 10))
    state = AuthoritativeState(tick=0, seed=42, regions={"r1": r1})
    
    # Far away, but r1 is only option
    assert RegionService.find_region_at(state, (100, 100)).id == "r1"
    
    # Two regions, pick nearest center
    r2 = RegionState(id="r2", name="R2", bounds=(90, 90, 100, 100))
    state = AuthoritativeState(tick=0, seed=42, regions={"r1": r1, "r2": r2})
    
    # (60, 60) is closer to r2 (95, 95) than r1 (5, 5)
    # dist to r1: (55^2 + 55^2) = 3025 + 3025 = 6050
    # dist to r2: (35^2 + 35^2) = 1225 + 1225 = 2450
    assert RegionService.find_region_at(state, (60, 60)).id == "r2"

def test_difficulty_tier_mapping():
    # Zones: (80, 1), (150, 2), (220, 3), (999, 4)
    assert RegionService.get_difficulty_tier_at((50, 0)) == 1
    assert RegionService.get_difficulty_tier_at((100, 0)) == 2
    assert RegionService.get_difficulty_tier_at((200, 0)) == 3
    assert RegionService.get_difficulty_tier_at((500, 0)) == 4

def test_empty_regions():
    state = AuthoritativeState(tick=0, seed=42, regions={})
    assert RegionService.find_region_at(state, (0, 0)) is None
