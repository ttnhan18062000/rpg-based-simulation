import pytest
from src.core.cognition import SpatialMemory, RegionVisitMemory
from src.domains.memory.spatial_update import SpatialMemoryUpdateService

def test_region_visit_updates_visit_count():
    spatial = SpatialMemory()
    
    spatial = SpatialMemoryUpdateService.update_region_visit(spatial, "forest")
    assert spatial.visited_regions["forest"].visit_count == 1
    assert spatial.visited_regions["forest"].familiarity == 0.2

    spatial = SpatialMemoryUpdateService.update_region_visit(spatial, "forest")
    assert spatial.visited_regions["forest"].visit_count == 2
    assert spatial.visited_regions["forest"].familiarity == 0.35

def test_near_death_marks_region_dangerous():
    spatial = SpatialMemory()
    # Add visit first
    spatial = SpatialMemoryUpdateService.update_region_visit(spatial, "swamp")
    spatial = SpatialMemoryUpdateService.mark_region_danger(spatial, "swamp", is_dangerous=True)

    assert spatial.visited_regions["swamp"].is_dangerous is True

def test_resource_observation_records_resource_site():
    spatial = SpatialMemory()
    spatial = SpatialMemoryUpdateService.record_resource_site(spatial, "ore_1", "iron_ore", (4.5, 6.7))

    assert "ore_1" in spatial.known_resource_sites
    assert spatial.known_resource_sites["ore_1"].resource_kind == "iron_ore"
    assert spatial.known_resource_sites["ore_1"].position == (4.5, 6.7)
