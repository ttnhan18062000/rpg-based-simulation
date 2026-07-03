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
                "required_location_tags": ["wilderness"],  # matches region type='wilderness'
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


def test_compiler_seeds_faction_tension_from_spec():
    """WorldCompiler.compile() seeds FactionState.tension_level from FactionSpec.initial_tension_level (TCK-20260702-SIMQ-UPLIFT2-FACTION)."""
    data = create_base_valid_spec()
    data["factions"] = [
        {"id": "a", "type": "x", "initial_tension_level": 0.5},
        {"id": "b", "type": "y"},
    ]
    data["entities"] = []
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert set(state.factions.keys()) == {"a", "b"}
    assert state.factions["a"].tension_level == 0.5
    assert state.factions["b"].tension_level == 0.0


def test_compiler_seeds_full_faction_roster_at_zero_tension_by_default():
    """Every declared FactionSpec produces a FactionState entry even with no initial_tension_level set."""
    data = create_base_valid_spec()
    data["entities"] = []
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert set(state.factions.keys()) == {"villagers", "monsters"}
    assert all(f.tension_level == 0.0 for f in state.factions.values())


def test_compiler_no_factions_declared_yields_empty_factions_dict():
    """spec.factions == [] compiles to state.factions == {} (schema-level regression guard)."""
    data = create_base_valid_spec()
    data["factions"] = []
    data["entities"] = []
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.factions == {}


def test_compiler_seeds_information_source_profiles_from_spec():
    """WorldCompiler.compile() constructs InformationSourceProfile domain objects from
    spec.information_source_profiles and passes them into AuthoritativeState
    (TCK-20260702-SIMQ-UPLIFT2-INFORMATION)."""
    from src.domains.information.schema import InformationSourceProfile

    data = create_base_valid_spec()
    data["entities"] = []
    data["information_source_profiles"] = [
        {
            "source_id": "town_notice_board",
            "source_kind": "guide",
            "knowledge_scopes": ["regional_danger", "common_resource_sources"],
            "accuracy": 0.4,
            "freshness": 0.6,
            "bias": 0.1,
            "cost_gold": 0,
            "max_answers_per_query": 2,
        },
        {
            "source_id": "traveling_merchant_rumors",
            "source_kind": "traveler",
            "knowledge_scopes": ["common_resource_sources", "recipe_requirements"],
            "accuracy": 0.65,
            "freshness": 0.8,
            "bias": 0.2,
            "cost_gold": 5,
            "max_answers_per_query": 3,
        },
    ]
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.information_source_profiles) == 2
    by_id = {p.source_id: p for p in state.information_source_profiles}

    board = by_id["town_notice_board"]
    assert isinstance(board, InformationSourceProfile)
    assert board.source_kind == "guide"
    assert board.knowledge_scopes == ("regional_danger", "common_resource_sources")
    assert board.accuracy == 0.4
    assert board.freshness == 0.6
    assert board.bias == 0.1
    assert board.cost_gold == 0
    assert board.max_answers_per_query == 2

    merchant = by_id["traveling_merchant_rumors"]
    assert merchant.source_kind == "traveler"
    assert merchant.knowledge_scopes == ("common_resource_sources", "recipe_requirements")
    assert merchant.accuracy == 0.65
    assert merchant.freshness == 0.8
    assert merchant.bias == 0.2
    assert merchant.cost_gold == 5
    assert merchant.max_answers_per_query == 3


def test_compiler_no_information_sources_declared_yields_empty_list():
    """spec.information_source_profiles == [] compiles to state.information_source_profiles == []
    (schema-level regression guard, mirrors test_compiler_no_factions_declared_yields_empty_factions_dict)."""
    data = create_base_valid_spec()
    data["entities"] = []
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.information_source_profiles == []


def test_compiler_seeds_pending_information_responses_from_spec():
    """WorldCompiler.compile() resolves target_population_id -> compiled actor_id and
    constructs a pending_information_responses dict entry on AuthoritativeState
    (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)."""
    data = create_base_valid_spec()
    data["entities"] = [
        {"id": "pop_test", "count": 1, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"},
    ]
    data["pending_information_responses"] = [
        {
            "target_population_id": "pop_test",
            "subject": "bandit_road_danger",
            "query_kind": "danger_rating",
            "source_id": "town_notice_board",
            "answer_kind": "KNOWN_FACT",
            "certainty": 0.8,
            "details": {"danger_level": "elevated", "region": "bandit_road"},
            "cost_paid": 0,
        },
    ]
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.pending_information_responses) == 1
    entry = state.pending_information_responses[0]
    compiled_actor_id = next(
        eid for eid, e in state.entities.items()
        if e.properties.get("population_id") == "pop_test"
    )
    assert entry["actor_id"] == compiled_actor_id
    assert entry["subject"] == "bandit_road_danger"
    assert entry["query_kind"] == "danger_rating"
    assert entry["source_id"] == "town_notice_board"
    assert entry["raw_response"] == {
        "answer_kind": "KNOWN_FACT",
        "certainty": 0.8,
        "details": {"danger_level": "elevated", "region": "bandit_road"},
        "reason": None,
    }
    assert entry["cost_paid"] == 0


def test_compiler_pending_information_response_unmatched_population_is_skipped_with_warning():
    """A target_population_id referencing no compiled entity is skipped, and a warning is recorded."""
    data = create_base_valid_spec()
    data["pending_information_responses"] = [
        {
            "target_population_id": "does_not_exist",
            "subject": "bandit_road_danger",
            "query_kind": "danger_rating",
            "source_id": "town_notice_board",
            "answer_kind": "KNOWN_FACT",
            "certainty": 0.8,
        },
    ]
    spec = WorldSpec.model_validate(data)

    state, report = WorldCompiler.compile(spec, seed=42)

    assert state.pending_information_responses == []
    assert any("does_not_exist" in w for w in report["warnings"])


def test_compiler_no_pending_information_responses_declared_yields_empty_list():
    """spec.pending_information_responses == [] compiles to state.pending_information_responses == []
    (schema-level regression guard)."""
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.pending_information_responses == []


def test_urban_political_resolved_world_seeds_one_pending_information_response():
    """urban_political's resolved world spec compiles with the seeded pending_information_responses
    entry targeting pop_0 (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)."""
    from src.worldbuilding.schema import load_world_spec_from_yaml

    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.pending_information_responses) == 1
    entry = state.pending_information_responses[0]
    assert state.entities[entry["actor_id"]].properties["population_id"] == "pop_0"
    assert entry["subject"] == "bandit_road_danger"
    assert entry["query_kind"] == "danger_rating"
    assert entry["source_id"] == "town_notice_board"
    assert entry["raw_response"] == {
        "answer_kind": "KNOWN_FACT",
        "certainty": 0.8,
        "details": {"danger_level": "elevated", "region": "bandit_road"},
        "reason": None,
    }
    assert entry["cost_paid"] == 0


def test_urban_political_resolved_world_seeds_two_information_sources():
    """urban_political's resolved world spec compiles with the two corrected
    InformationSourceProfile entries (TCK-20260702-SIMQ-UPLIFT2-INFORMATION)."""
    from src.worldbuilding.schema import load_world_spec_from_yaml

    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.information_source_profiles) == 2
    by_id = {p.source_id: p for p in state.information_source_profiles}

    board = by_id["town_notice_board"]
    assert board.source_kind == "guide"
    assert board.knowledge_scopes == ("regional_danger", "common_resource_sources")
    assert board.accuracy == 0.4
    assert board.freshness == 0.6
    assert board.bias == 0.1
    assert board.cost_gold == 0
    assert board.max_answers_per_query == 2

    merchant = by_id["traveling_merchant_rumors"]
    assert merchant.source_kind == "traveler"
    assert merchant.knowledge_scopes == ("common_resource_sources", "recipe_requirements")
    assert merchant.accuracy == 0.65
    assert merchant.freshness == 0.8
    assert merchant.bias == 0.2
    assert merchant.cost_gold == 5
    assert merchant.max_answers_per_query == 3


def test_urban_political_resolved_world_seeds_bandit_town_council_tension():
    """urban_political's resolved world spec compiles with bandit_company/town_council at
    tension_level=0.5 via composition-level faction_tension_overrides (TCK-20260702-SIMQ-UPLIFT2-FACTION)."""
    from src.worldbuilding.schema import load_world_spec_from_yaml

    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.factions["bandit_company"].tension_level == 0.5
    assert state.factions["town_council"].tension_level == 0.5


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


def test_compiler_resource_node_regen_rate():
    """Compiler-seeded nodes default to regen_rate_per_tick=1 (TOWN-186)."""
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    node = list(state.resource_nodes.values())[0]
    assert node.regen_rate_per_tick == 1, (
        "Compiler-seeded nodes must default to regen_rate_per_tick=1 so ecology "
        "cycles can restore depleted charges (TCK-20260628-E21C-COMPILER-REGEN)"
    )


def test_compiler_resource_node_explicit_zero_regen():
    """regen_rate: 0 in spec produces a static (non-regenerating) node."""
    data = create_base_valid_spec()
    data["resources"] = [
        {"id": "static_ore", "resource_type": "ore", "count": 3, "region": "wilds", "regen_rate": 0}
    ]
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    node = list(state.resource_nodes.values())[0]
    assert node.regen_rate_per_tick == 0


def test_quest_location_tag_matches_region_type():
    """required_location_tag that equals a region's type produces zero warnings (TCK-20260630-WORLD-QUEST-LOCATION)."""
    data = create_base_valid_spec()
    # Quest needs 'wilderness' — region 'wilds' has type='wilderness'
    data["quest_definitions"] = [
        {
            "id": "survey_wilds",
            "type": "explore",
            "required_location_tags": ["wilderness"],
            "reward_budget": 80,
        }
    ]
    spec = WorldSpec.model_validate(data)
    _, report = WorldCompiler.compile(spec, seed=42)
    assert report["warnings"] == [], (
        "Quest tag 'wilderness' should be satisfied by region with type='wilderness'"
    )


def test_quest_location_tag_matches_region_explicit_tag():
    """required_location_tag matched against region.tags (not just type) produces zero warnings (TCK-20260630-WORLD-QUEST-LOCATION)."""
    data = create_base_valid_spec()
    # Add mine region with explicit tags
    data["regions"] = [
        {"id": "old_mine", "type": "wilderness", "bounds": [0, 0, 20, 20], "terrain": "cave",
         "tags": ["mine", "underground"]},
    ]
    data["entities"] = [
        {"id": "spider_group", "count": 3, "role": "monster", "faction": "monsters", "spawn_region": "old_mine"}
    ]
    data["resources"] = [
        {"id": "iron_vein", "resource_type": "ore", "count": 5, "region": "old_mine"}
    ]
    data["buildings"] = []
    data["factions"] = [{"id": "monsters", "type": "hostile"}]
    data["quest_definitions"] = [
        {
            "id": "mine_fetch_ore",
            "type": "fetch",
            "required_location_tags": ["mine", "underground"],
            "reward_budget": 80,
        }
    ]
    spec = WorldSpec.model_validate(data)
    _, report = WorldCompiler.compile(spec, seed=42)
    assert report["warnings"] == [], (
        "Quest tags 'mine' and 'underground' should be satisfied by region with tags=['mine','underground']"
    )


def test_quest_location_tag_warns_on_genuine_mismatch():
    """Quest with a required_location_tag that matches no region type or tag still warns (regression guard, TCK-20260630-WORLD-QUEST-LOCATION)."""
    data = create_base_valid_spec()
    # Base spec has regions 'town_square' (type=town) and 'wilds' (type=wilderness), no tags
    data["quest_definitions"] = [
        {
            "id": "find_settlement",
            "type": "explore",
            "required_location_tags": ["settlement"],  # no region has type='settlement' or tag='settlement'
            "reward_budget": 80,
        }
    ]
    spec = WorldSpec.model_validate(data)
    _, report = WorldCompiler.compile(spec, seed=42)
    assert len(report["warnings"]) >= 1, "Should warn when tag matches no region type or tags"
    assert "settlement" in report["warnings"][0], (
        "Warning message should name the unmatched tag"
    )
