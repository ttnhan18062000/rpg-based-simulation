# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
from dataclasses import replace
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler
from src.core.updates import StateUpdate
from src.engine.pipeline import AuthoritativeApplyPipeline
from src.engine.apply import ApplyPath


def create_base_integration_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "integration_valley",
        "name": "Integration Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "village", "type": "town", "bounds": [0, 0, 20, 20], "terrain": "GRASS"},
            {"id": "forest", "type": "wilderness", "bounds": [30, 30, 80, 80], "terrain": "FOREST"}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"},
            {"id": "monsters", "type": "hostile"}
        ],
        "entities": [
            {"id": "worker_group", "count": 2, "role": "worker", "faction": "villagers", "spawn_region": "village"},
            {"id": "monsters_group", "count": 1, "role": "monster", "faction": "monsters", "spawn_region": "forest"}
        ],
        "resources": [
            {"id": "forest_wood", "resource_type": "wood", "count": 100, "region": "forest"}
        ],
        "buildings": [
            {"id": "woodcutter_hut", "type": "industry", "region": "village"}
        ],
        "quests": [
            {
                "id": "collect_wood",
                "name": "Gather Wood",
                "kind": "gather",
                "goal_value": 10.0,
                "reward": {"xp": 50, "gold": 25},
                "target_resource_type": "wood",
                "assignee": "worker"
            }
        ]
    }


def test_compiled_world_ticks_stability():
    """
    Verify that a compiled world can run for 10 ticks in the engine
    without immediate structural failure or crash.
    """
    raw_spec = create_base_integration_spec()
    spec = WorldSpec.model_validate(raw_spec)
    
    state, report = WorldCompiler.compile(spec, seed=42)
    assert len(report["warnings"]) == 0
    assert state.tick == 0
    
    # Tick simulation 10 times
    for t in range(1, 11):
        state = replace(state, tick=t)
        
        # Prepare a empty update
        raw_update = StateUpdate()
        
        # 1. Refine
        refined = AuthoritativeApplyPipeline.refine(state, raw_update)
        
        # 2. Apply
        state = ApplyPath.apply_generation(state, refined)
        
        # Verify tick incremented and structures remain sound
        assert state.tick == t + 1
        assert len(state.entities) == 3
        assert len(state.regions) == 2
        assert len(state.resource_nodes) == 1
        assert len(state.buildings) == 1


def test_compiled_world_quest_warning_validation():
    """
    Verify that invalid references in quests do not crash compilation
    but yield distinct compile warnings.
    """
    raw_spec = create_base_integration_spec()
    # Introduce mismatched target region, faction, role and resource
    raw_spec["quests"].append({
        "id": "invalid_quest_1",
        "name": "Invalid Quest 1",
        "kind": "explore",
        "target_region_id": "nonexistent_region",
        "target_faction": "nonexistent_faction",
        "target_role": "nonexistent_role",
        "target_resource_type": "nonexistent_resource",
        "assignee": "worker"
    })
    
    spec = WorldSpec.model_validate(raw_spec)
    state, report = WorldCompiler.compile(spec, seed=42)
    
    # Compilation must succeed
    assert state is not None
    
    # Warnings must contain detail about each invalid reference
    warnings = report["warnings"]
    assert len(warnings) == 4
    
    # Assert specific warning details exist
    assert any("nonexistent_region" in w for w in warnings)
    assert any("nonexistent_faction" in w for w in warnings)
    assert any("nonexistent_role" in w for w in warnings)
    assert any("nonexistent_resource" in w for w in warnings)
