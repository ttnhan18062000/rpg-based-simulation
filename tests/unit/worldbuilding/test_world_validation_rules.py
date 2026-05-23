# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.validator import (
    FactionExistenceRule,
    SpawnRegionExistenceRule,
    ResourceRegionExistenceRule,
    BuildingRegionExistenceRule,
    RegionBoundsWithinTopologyRule,
    NoResourcesWarningRule,
    HighEntityDensityWarningRule
)

def create_valid_base_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "village", "type": "settlement", "bounds": [0, 0, 30, 30]}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"}
        ]
    }

def test_rule_faction_existence():
    data = create_valid_base_spec()
    data["entities"] = [
        {"id": "workers", "count": 10, "role": "worker", "faction": "villagers", "spawn_region": "village"},
        {"id": "rebels", "count": 5, "role": "warrior", "faction": "missing_faction", "spawn_region": "village"}
    ]
    
    spec = WorldSpec.model_validate(data)
    rule = FactionExistenceRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-REF-001"
    assert issues[0].severity == "ERROR"
    assert "missing_faction" in issues[0].message
    assert issues[0].path == "entities.1.faction"

def test_rule_spawn_region_existence():
    data = create_valid_base_spec()
    data["entities"] = [
        {"id": "workers", "count": 10, "role": "worker", "faction": "villagers", "spawn_region": "nonexistent_region"}
    ]
    
    spec = WorldSpec.model_validate(data)
    rule = SpawnRegionExistenceRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-REF-002"
    assert issues[0].severity == "ERROR"
    assert "nonexistent_region" in issues[0].message
    assert issues[0].path == "entities.0.spawn_region"

def test_rule_resource_region_existence():
    data = create_valid_base_spec()
    data["resources"] = [
        {"id": "wood_node", "resource_type": "wood", "count": 10, "region": "nonexistent_region"}
    ]
    
    spec = WorldSpec.model_validate(data)
    rule = ResourceRegionExistenceRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-REF-003"
    assert issues[0].severity == "ERROR"
    assert "nonexistent_region" in issues[0].message
    assert issues[0].path == "resources.0.region"

def test_rule_building_region_existence():
    data = create_valid_base_spec()
    data["buildings"] = [
        {"id": "shop", "type": "shop", "region": "nonexistent_region"}
    ]
    
    spec = WorldSpec.model_validate(data)
    rule = BuildingRegionExistenceRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-REF-004"
    assert issues[0].severity == "ERROR"
    assert "nonexistent_region" in issues[0].message
    assert issues[0].path == "buildings.0.region"

def test_rule_region_bounds_within_topology():
    data = create_valid_base_spec()
    data["regions"] = [
        {"id": "valid_reg", "type": "zone", "bounds": [0, 0, 50, 50]},
        {"id": "out_reg", "type": "zone", "bounds": [0, 0, 105, 50]}  # 105 exceeds width 100
    ]
    
    spec = WorldSpec.model_validate(data)
    rule = RegionBoundsWithinTopologyRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-TOPO-001"
    assert issues[0].severity == "ERROR"
    assert "105" in issues[0].message
    assert issues[0].path == "regions.1.bounds"

def test_rule_no_resources_warning():
    data = create_valid_base_spec()
    # Empty resources
    spec = WorldSpec.model_validate(data)
    rule = NoResourcesWarningRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-WARN-001"
    assert issues[0].severity == "WARNING"
    assert "zero resource nodes" in issues[0].message
    assert issues[0].path == "resources"

def test_rule_high_entity_density_warning():
    data = create_valid_base_spec()
    # area is 100 * 100 = 10000. 50% is 5000. Let's spawn 5001 workers.
    data["entities"] = [
        {"id": "workers", "count": 5001, "role": "worker", "faction": "villagers", "spawn_region": "village"}
    ]
    
    spec = WorldSpec.model_validate(data)
    rule = HighEntityDensityWarningRule()
    issues = rule.validate(spec)
    
    assert len(issues) == 1
    assert issues[0].rule_id == "WORLD-WARN-002"
    assert issues[0].severity == "WARNING"
    assert "density" in issues[0].message
    assert issues[0].path == "entities"
