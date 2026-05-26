# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
import os
import tempfile
import json
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler
from src.replay.fingerprint import StateFingerprinter


def create_certification_base_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "cert_valley",
        "name": "Certification Valley",
        "topology": {
            "width": 100,
            "height": 100,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "valley_town", "type": "town", "bounds": [0, 0, 30, 30], "terrain": "GRASS"},
            {"id": "valley_woods", "type": "wilderness", "bounds": [40, 40, 90, 90], "terrain": "FOREST"}
        ],
        "factions": [
            {"id": "locals", "type": "civilian"},
            {"id": "intruders", "type": "hostile"}
        ],
        "entities": [
            {"id": "villagers", "count": 25, "role": "worker", "faction": "locals", "spawn_region": "valley_town"},
            {"id": "monsters", "count": 10, "role": "monster", "faction": "intruders", "spawn_region": "valley_woods"}
        ],
        "resources": [
            {"id": "wood_node", "resource_type": "wood", "count": 200, "region": "valley_woods"},
            {"id": "stone_node", "resource_type": "stone", "count": 150, "region": "valley_town"}
        ],
        "buildings": [
            {"id": "town_hall", "type": "civic", "region": "valley_town"}
        ],
        "quests": []
    }


def test_compiler_seeding_determinism():
    """
    Verify that compiling the same world spec twice with the exact same seed
    produces identical state hashes and entity/resource coordinates.
    """
    raw_spec = create_certification_base_spec()
    spec = WorldSpec.model_validate(raw_spec)
    
    state1, report1 = WorldCompiler.compile(spec, seed=999)
    state2, report2 = WorldCompiler.compile(spec, seed=999)
    
    # 1. State hashes must be exactly the same
    assert report1["state_hash"] == report2["state_hash"]
    
    # 2. Entity count must match
    assert len(state1.entities) == len(state2.entities)
    
    # 3. Every entity's coordinate must match perfectly
    for eid in state1.entities:
        pos1 = state1.entities[eid].navigation.position
        pos2 = state2.entities[eid].navigation.position
        assert pos1 == pos2
        
    # 4. Resource coordinate matching
    for rid in state1.resource_nodes:
        pos1 = state1.resource_nodes[rid].position
        pos2 = state2.resource_nodes[rid].position
        assert pos1 == pos2


def test_compiler_layout_variation_under_different_seeds():
    """
    Verify that compiling the same world spec with two different seeds
    produces distinct spatial coordinates for entities and resources.
    """
    raw_spec = create_certification_base_spec()
    spec = WorldSpec.model_validate(raw_spec)
    
    state_a, report_a = WorldCompiler.compile(spec, seed=42)
    state_b, report_b = WorldCompiler.compile(spec, seed=100)
    
    # 1. State hashes should differ
    assert report_a["state_hash"] != report_b["state_hash"]
    
    # 2. Extract coordinates list
    coords_a = [e.navigation.position for e in state_a.entities.values()]
    coords_b = [e.navigation.position for e in state_b.entities.values()]
    
    # Coordinates layout must be distinct (not identical list)
    assert coords_a != coords_b


def test_compile_report_contents():
    """
    Verify that the generated compile report contains all required metrics.
    """
    raw_spec = create_certification_base_spec()
    spec = WorldSpec.model_validate(raw_spec)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "world_compile_report.json")
        _, report = WorldCompiler.compile(spec, seed=1337, output_report_path=report_path)
        
        # Verify dict keys
        expected_keys = {
            "world_id",
            "seed",
            "entity_count",
            "region_count",
            "resource_node_count",
            "building_count",
            "quest_count",
            "warnings",
            "compile_duration_ms",
            "state_hash"
        }
        assert set(report.keys()) == expected_keys
        
        # Verify JSON saved matches
        assert os.path.exists(report_path)
        with open(report_path) as f:
            saved = json.load(f)
            
        assert saved["world_id"] == "cert_valley"
        assert saved["seed"] == 1337
        assert saved["entity_count"] == 35
        assert saved["region_count"] == 2
        assert saved["resource_node_count"] == 2
        assert saved["building_count"] == 1
        assert saved["quest_count"] == 0
        assert saved["state_hash"] == report["state_hash"]
