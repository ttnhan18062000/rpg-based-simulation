# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
import os
import tempfile
import json
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler, get_role_enum, get_faction_enum, get_quest_kind
from src.core.enums import EntityRole, Faction
from src.core.quests import QuestKind


def create_base_valid_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "test_valley",
        "name": "Test Valley",
        "topology": {
            "width": 50,
            "height": 50,
            "coordinate_system": "grid"
        },
        "regions": [
            {"id": "town_square", "type": "town", "bounds": [0, 0, 10, 10], "terrain": "GRASS"},
            {"id": "wilds", "type": "wilderness", "bounds": [15, 15, 40, 40], "terrain": "FOREST"}
        ],
        "factions": [
            {"id": "villagers", "type": "civilian"},
            {"id": "monsters", "type": "hostile"}
        ],
        "entities": [
            {"id": "citizen_group", "count": 5, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"},
            {"id": "horde", "count": 2, "role": "monster", "faction": "monsters", "spawn_region": "wilds"}
        ],
        "resources": [
            {"id": "ore_node", "resource_type": "ore", "count": 5, "region": "wilds"}
        ],
        "buildings": [
            {"id": "tavern", "type": "inn", "region": "town_square"}
        ],
        "quest_definitions": [
            {
                "id": "hunt_beasts",
                "type": "hunt",
                "required_participant_tags": ["monster"],
                "required_location_tags": ["wilds"],
                "reward_budget": 100,
            }
        ]
    }


def test_compiler_minimal_world():
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)
    
    state, report = WorldCompiler.compile(spec, seed=42)
    
    assert state.tick == 0
    assert state.seed == 42
    
    # Check regions
    assert "town_square" in state.regions
    assert "wilds" in state.regions
    assert state.regions["town_square"].kind == "TOWN"
    assert state.regions["wilds"].kind == "WILDERNESS"
    
    # Check entities count (5 citizens + 2 monsters = 7 entities)
    assert len(state.entities) == 7
    
    # Check faction starting vaults initialized in global_resources
    assert "faction_hero_guild_gold" in state.global_resources or "faction_villagers_gold" in state.global_resources
    
    # Check resources
    assert len(state.resource_nodes) == 1
    node = list(state.resource_nodes.values())[0]
    assert node.kind == "ore"
    assert node.remaining_charges == 5
    
    # Check buildings
    assert len(state.buildings) == 1
    building = list(state.buildings.values())[0]
    assert building.kind == "inn"
    
    # Verify compile report format
    assert report["world_id"] == "test_valley"
    assert report["seed"] == 42
    assert report["entity_count"] == 7
    assert report["region_count"] == 2
    assert report["resource_node_count"] == 1
    assert report["building_count"] == 1
    assert report["quest_count"] == 1
    assert report["warnings"] == []
    assert isinstance(report["state_hash"], str)


def test_compiler_entity_mappings():
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)
    
    state, _ = WorldCompiler.compile(spec, seed=42)
    
    # Verify entity components mapping
    for ent in state.entities.values():
        if ent.kind == "citizen":
            assert ent.identity.role == EntityRole.CITIZEN
            assert ent.identity.faction == Faction.HERO_GUILD
        elif ent.kind == "monster":
            assert ent.identity.role == EntityRole.MONSTER
            assert ent.identity.faction == Faction.MONSTER_HORDE


def test_compiler_placement_bounds():
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)
    
    state, _ = WorldCompiler.compile(spec, seed=99)
    
    # Check that citizens are placed inside town_square [0, 0, 10, 10]
    for ent in state.entities.values():
        if ent.kind == "citizen":
            x, y = ent.navigation.position
            assert 0 <= x <= 10
            assert 0 <= y <= 10
        elif ent.kind == "monster":
            x, y = ent.navigation.position
            assert 15 <= x <= 40
            assert 15 <= y <= 40



def test_compiler_report_write():
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = os.path.join(tmpdir, "report.json")
        WorldCompiler.compile(spec, seed=123, output_report_path=report_path)
        
        assert os.path.exists(report_path)
        with open(report_path) as f:
            saved_report = json.load(f)
        
        assert saved_report["world_id"] == "test_valley"
        assert saved_report["seed"] == 123
        assert saved_report["entity_count"] == 7


def test_compiler_quest_referential_warnings():
    data = create_base_valid_spec()
    # Introduce an unknown location tag in quest_definitions to trigger a referential warning
    data["quest_definitions"][0]["required_location_tags"] = ["unknown_forest"]

    spec = WorldSpec.model_validate(data)
    _, report = WorldCompiler.compile(spec, seed=42)

    assert len(report["warnings"]) >= 1
    assert "unknown_forest" in report["warnings"][0]


def test_helper_enum_mappers():
    assert get_role_enum("hero") == EntityRole.HERO
    assert get_role_enum("worker") == EntityRole.WORKER
    assert get_role_enum("unknown_role") == EntityRole.CITIZEN
    
    assert get_faction_enum("villagers") == Faction.HERO_GUILD
    assert get_faction_enum("monsters") == Faction.MONSTER_HORDE
    assert get_faction_enum("neutral") == Faction.NEUTRAL
    
    assert get_quest_kind("hunt") == QuestKind.HUNT
    assert get_quest_kind("gather") == QuestKind.GATHER
    assert get_quest_kind("explore") == QuestKind.EXPLORE
