# Compliance IDs: WORLD-070, WORLD-071, WORLD-072
import pytest
import os
import tempfile
import json
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler, get_role_enum, get_faction_enum, get_quest_kind, get_bravery_bias, get_action_style_for_bravery
from src.core.enums import EntityRole, Faction, ActionStyle
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


def test_compiler_seeds_pending_self_model_information_events_from_spec():
    """WorldCompiler.compile() resolves target_population_id -> compiled actor_id and
    constructs a real InformationResponse instance inside a
    pending_self_model_information_events dict entry on AuthoritativeState
    (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B)."""
    from src.world.providers.information import InformationResponse

    data = create_base_valid_spec()
    data["entities"] = [
        {"id": "pop_test", "count": 1, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"},
    ]
    data["pending_self_model_information_events"] = [
        {
            "target_population_id": "pop_test",
            "answer_kind": "unknown",
            "unknowns": ["material.moon_resin.source"],
        },
    ]
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.pending_self_model_information_events) == 1
    entry = state.pending_self_model_information_events[0]
    compiled_actor_id = next(
        eid for eid, e in state.entities.items()
        if e.properties.get("population_id") == "pop_test"
    )
    assert entry["actor_id"] == compiled_actor_id
    event = entry["event"]
    assert isinstance(event, InformationResponse)
    assert event.answer_kind == "unknown"
    assert event.unknowns == ("material.moon_resin.source",)
    assert event.facts == ()
    assert event.suggested_leads == ()


def test_compiler_pending_self_model_information_event_unmatched_population_is_skipped_with_warning():
    """A target_population_id referencing no compiled entity is skipped, and a warning is recorded."""
    data = create_base_valid_spec()
    data["pending_self_model_information_events"] = [
        {
            "target_population_id": "does_not_exist",
            "answer_kind": "unknown",
            "unknowns": ["material.moon_resin.source"],
        },
    ]
    spec = WorldSpec.model_validate(data)

    state, report = WorldCompiler.compile(spec, seed=42)

    assert state.pending_self_model_information_events == []
    assert any("does_not_exist" in w for w in report["warnings"])


def test_compiler_no_pending_self_model_information_events_declared_yields_empty_list():
    """spec.pending_self_model_information_events == [] compiles to
    state.pending_self_model_information_events == [] (schema-level regression guard)."""
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert state.pending_self_model_information_events == []


def test_urban_political_resolved_world_seeds_one_pending_self_model_information_event():
    """urban_political's resolved world spec compiles with the seeded
    pending_self_model_information_events entry targeting pop_1
    (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B)."""
    from src.worldbuilding.schema import load_world_spec_from_yaml
    from src.world.providers.information import InformationResponse

    spec = load_world_spec_from_yaml("data/worlds/urban_political/resolved/world.resolved.yaml")
    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.pending_self_model_information_events) == 1
    entry = state.pending_self_model_information_events[0]
    assert state.entities[entry["actor_id"]].properties["population_id"] == "pop_1"
    event = entry["event"]
    assert isinstance(event, InformationResponse)
    assert event.answer_kind == "unknown"
    assert event.unknowns == ("material.moon_resin.source",)


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


def test_urban_political_resolved_bandit_road_hazard_kind_matches_source():
    """urban_political's resolved bandit_road region must carry the hazard_kind its
    source module (bandit_road_trade_pressure.yaml) declares, not a stale default from
    an out-of-date recompile (TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE)."""
    import yaml

    resolved = yaml.safe_load(
        open("data/worlds/urban_political/resolved/world.resolved.yaml").read()
    )
    regions_by_id = {r["id"]: r for r in resolved["regions"]}
    assert regions_by_id["bandit_road"]["hazard_kind"] == "NATURAL_TERRAIN", (
        "urban_political's resolved bandit_road region is stale relative to "
        "bandit_road_trade_pressure.yaml's source — re-run "
        "`worldbuilding.cli resolve` + `compile --from-resolved` for urban_political."
    )
    assert regions_by_id["trading_hometown"]["hazard_kind"] == "NATURAL_TERRAIN", (
        "urban_political's resolved trading_hometown region is stale relative to "
        "trading_company_hub.yaml's source — re-run "
        "`worldbuilding.cli resolve` + `compile --from-resolved` for urban_political."
    )


def test_compile_sets_real_town_center_from_town_region():
    """WorldCompiler.compile() derives AuthoritativeState.town_center as the centroid of the
    town-type region's own bounds, instead of leaving it at the dataclass default (0.0, 0.0)
    (TCK-20260824-TOWN-CENTER-POINTER-FIX)."""
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    # town_square region bounds = [0, 0, 10, 10] -> centroid (5.0, 5.0)
    assert state.town_center == (5.0, 5.0)
    assert state.town_center != (0.0, 0.0)


def test_compile_town_center_derivation_with_multiple_town_regions():
    """With more than one type=='town' region compiled into a world (mirroring
    urban_political.yaml's real two-town-region shape), town_center is the centroid of the
    FIRST town-type region in spec.regions declaration order -- not a union/average across
    every town region, and not the last one declared."""
    data = create_base_valid_spec()
    data["regions"] = [
        {"id": "town_square", "type": "town", "bounds": [0, 0, 10, 10], "terrain": "GRASS"},
        {"id": "trading_post", "type": "town", "bounds": [45, 10, 80, 45], "terrain": "GRASS"},
        {"id": "wilds", "type": "wilderness", "bounds": [15, 15, 40, 40], "terrain": "FOREST"},
    ]
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    # First-declared town region (town_square, bounds [0,0,10,10]) centroid -> (5.0, 5.0).
    # trading_post's own centroid would be (62.5, 27.5) -- asserting against that value would
    # catch a regression that picked the second/last region instead of the first.
    assert state.town_center == (5.0, 5.0)


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
    assert get_quest_kind("escort") == QuestKind.ESCORT


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


def test_get_bravery_bias_by_real_alignment_bucket():
    """TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION: bravery bias values are real, external
    data (data/content/social/personality_bias.yaml), keyed by the real, content-defined
    alignment_bucket (data/content/social/factions.yaml) -- not hardcoded per-faction in code, so
    a designer can retune values or a new faction's alignment_bucket inherits a sensible bias
    with no code change required."""
    assert get_bravery_bias("wild_beast_pack") == 0.35   # alignment_bucket: wild
    assert get_bravery_bias("goblin_warband") == 0.25    # alignment_bucket: invader
    assert get_bravery_bias("orc_clan") == 0.15          # alignment_bucket: rival
    assert get_bravery_bias("hero_guild") == 0.05        # alignment_bucket: defender
    assert get_bravery_bias("merchant_league") == 0.0    # alignment_bucket: neutral
    assert get_bravery_bias("nonexistent_faction_xyz") == 0.0  # no crash, no real content match


# test_personality_bias_config_loads_from_real_data_file and
# test_personality_bias_config_falls_back_safely_on_bad_file moved to
# tests/unit/content_semantics/test_personality.py -- _load_personality_bias_config,
# _PERSONALITY_BIAS_FALLBACK, and _personality_bias_cache moved to
# src/content_semantics/personality.py (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY),
# shared with ArchetypeEntityFactory's own entity-construction path. get_bravery_bias/
# get_action_style_for_bravery are re-exported from this module (compiler.py) for backward
# compatibility with this file's own remaining tests below.


def test_compiler_faction_bravery_bias_produces_real_population_skew():
    """A predator faction's real, compiled population should show a measurably higher average
    bravery than a neutral civilian faction's, while individual per-entity RNG variance is
    preserved (not every entity identical)."""
    data = create_base_valid_spec()
    data["regions"].append({"id": "predator_zone", "type": "wilderness", "bounds": [20, 20, 40, 40], "terrain": "FOREST"})
    data["factions"] = [
        {"id": "wild_beast_pack", "type": "hostile"},
        {"id": "merchant_league", "type": "civilian"},
    ]
    data["entities"] = [
        {"id": "predators", "count": 30, "role": "monster", "faction": "wild_beast_pack", "spawn_region": "predator_zone"},
        {"id": "merchants", "count": 30, "role": "citizen", "faction": "merchant_league", "spawn_region": "town_square"},
    ]
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    predator_bravery = [
        e.identity.personality.bravery for e in state.entities.values()
        if e.identity.properties.get("faction_id") == "wild_beast_pack"
    ]
    merchant_bravery = [
        e.identity.personality.bravery for e in state.entities.values()
        if e.identity.properties.get("faction_id") == "merchant_league"
    ]
    assert len(predator_bravery) == 30
    assert len(merchant_bravery) == 30

    avg_predator = sum(predator_bravery) / len(predator_bravery)
    avg_merchant = sum(merchant_bravery) / len(merchant_bravery)
    assert avg_predator > avg_merchant + 0.2, (
        f"predator faction avg bravery ({avg_predator:.3f}) should be measurably higher than "
        f"merchant faction avg bravery ({avg_merchant:.3f})"
    )
    # Individual variance preserved within the faction -- not every predator identical.
    assert len(set(predator_bravery)) > 1


def test_get_action_style_for_bravery_thresholds():
    """TCK-20260809-COMBAT-ACTIONSTYLE-WIRING: ActionStyle is derived from bravery via real,
    data-driven thresholds (personality_bias.yaml), not hardcoded per-entity."""
    assert get_action_style_for_bravery(0.9) == ActionStyle.AGGRESSIVE
    assert get_action_style_for_bravery(0.65) == ActionStyle.AGGRESSIVE  # boundary, inclusive
    assert get_action_style_for_bravery(0.5) == ActionStyle.BALANCED
    assert get_action_style_for_bravery(0.35) == ActionStyle.EVASIVE  # boundary, inclusive
    assert get_action_style_for_bravery(0.1) == ActionStyle.EVASIVE


def test_compiler_terrain_variants_declared_produces_per_tile_variation():
    """A region with >=2 terrain_variants produces real per-tile terrain variation,
    not a degenerate single-value fill (TCK-20260821-COMPILER-NOISE-FILL)."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    region_terrains = {state.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    assert len(region_terrains) > 1, (
        "terrain_variants should produce real per-tile terrain variation, not a single flat value"
    )


def test_compiler_terrain_variants_deterministic_same_seed():
    """Compiling the same terrain_variants-declaring spec twice with the same seed produces
    an identical per-tile terrain dict within the region's bounds, and an identical
    report["state_hash"] as one additional signal (mirroring test_compiler_seeding_determinism)."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)

    state1, report1 = WorldCompiler.compile(spec, seed=42)
    state2, report2 = WorldCompiler.compile(spec, seed=42)

    assert report1["state_hash"] == report2["state_hash"]

    region_tiles_1 = {(x, y): state1.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    region_tiles_2 = {(x, y): state2.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    assert region_tiles_1 == region_tiles_2


def test_compiler_terrain_variants_different_seed_differs():
    """Compiling the same terrain_variants-declaring spec with two different seeds produces a
    measurably different per-tile terrain distribution within the same bounds."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)

    state1, _ = WorldCompiler.compile(spec, seed=42)
    state2, _ = WorldCompiler.compile(spec, seed=99)

    tiles = [(x, y) for x in range(15, 41) for y in range(15, 41)]
    diff_count = sum(1 for t in tiles if state1.terrain[t] != state2.terrain[t])
    assert diff_count / len(tiles) > 0.10, (
        f"different seeds should produce a measurably different terrain distribution "
        f"({diff_count}/{len(tiles)} tiles differ)"
    )


def test_compiler_terrain_variants_never_writes_outside_bounds():
    """The existing 0 <= x < width and 0 <= y < height clamp continues to gate the new
    noise-fill write path exactly as it does the flat-fill path."""
    data = create_base_valid_spec()
    data["regions"] = [
        {"id": "town_square", "type": "town", "bounds": [0, 0, 10, 10], "terrain": "GRASS"},
        {
            "id": "edge_region", "type": "wilderness", "bounds": [45, 45, 60, 60], "terrain": "FOREST",
            "terrain_variants": [
                {"terrain": "FOREST", "weight": 1.0},
                {"terrain": "SWAMP", "weight": 1.0},
            ],
        },
    ]
    data["entities"] = [
        {"id": "citizen_group", "count": 5, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"},
    ]
    data["resources"] = []
    data["buildings"] = []
    data["quest_definitions"] = []
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    assert len(state.terrain) == spec.topology.width * spec.topology.height, (
        "terrain dict must contain exactly one entry per topology tile, none outside bounds"
    )
    assert all(
        0 <= x < spec.topology.width and 0 <= y < spec.topology.height
        for (x, y) in state.terrain.keys()
    )


def test_compiler_terrain_variants_town_tiles_membership_unaffected_by_terrain_choice():
    """A town region declaring terrain_variants still produces town_tiles covering exactly the
    same tile set as the flat-fill path -- membership is driven solely by r_spec.type == 'town',
    independent of which terrain string each tile is painted with."""
    data = create_base_valid_spec()
    data["regions"][0]["terrain_variants"] = [
        {"terrain": "GRASS", "weight": 1.0},
        {"terrain": "DIRT", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)

    state, _ = WorldCompiler.compile(spec, seed=42)

    expected_town_tiles = {(x, y) for x in range(0, 11) for y in range(0, 11)}
    assert state.town_tiles == expected_town_tiles


def test_compiler_no_terrain_variants_declared_produces_byte_identical_terrain_dict():
    """Load-bearing anti-regression guard: for regions that do not declare terrain_variants,
    state.terrain must equal the flat-fill r_spec.terrain string for every in-bounds tile,
    asserted by direct per-tile content -- not state_hash equality, since StateFingerprinter
    does not read state.terrain at all and cannot detect a terrain-painting regression."""
    data = create_base_valid_spec()
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    for r_spec in spec.regions:
        min_x, min_y, max_x, max_y = r_spec.bounds
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                if 0 <= x < spec.topology.width and 0 <= y < spec.topology.height:
                    assert state.terrain[(x, y)] == r_spec.terrain


def test_compiler_terrain_variants_reuses_weighted_choice_respects_weight():
    """A region declaring two variants with a heavily skewed weight (99:1) produces a per-tile
    terrain distribution dominated by the heavily-weighted terrain -- proves `weight` is
    actually consumed by rng.weighted_choice, not ignored/uniform."""
    data = create_base_valid_spec()
    data["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 99.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    tiles = [(x, y) for x in range(15, 41) for y in range(15, 41)]
    forest_count = sum(1 for t in tiles if state.terrain[t] == "FOREST")
    assert forest_count / len(tiles) > 0.8, (
        f"heavily weighted terrain (99:1) should dominate the fill ({forest_count}/{len(tiles)})"
    )


def test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration():
    """Compiling the same spec with terrain_variants populated vs. None must produce identical
    entity/resource/building positions at the same seed -- proves the new noise-fill draw
    (Domain.INIT) cannot perturb Domain.WORLD's existing entity/resource/building draw
    sequence, regardless of draw order."""
    data_without = create_base_valid_spec()
    data_with = create_base_valid_spec()
    data_with["regions"][1]["terrain_variants"] = [
        {"terrain": "FOREST", "weight": 1.0},
        {"terrain": "SWAMP", "weight": 1.0},
    ]

    spec_without = WorldSpec.model_validate(data_without)
    spec_with = WorldSpec.model_validate(data_with)

    state_without, _ = WorldCompiler.compile(spec_without, seed=42)
    state_with, _ = WorldCompiler.compile(spec_with, seed=42)

    assert set(state_without.entities.keys()) == set(state_with.entities.keys())
    for eid, ent in state_without.entities.items():
        assert ent.navigation.position == state_with.entities[eid].navigation.position

    assert set(state_without.resource_nodes.keys()) == set(state_with.resource_nodes.keys())
    for rid, node in state_without.resource_nodes.items():
        assert node.position == state_with.resource_nodes[rid].position

    assert set(state_without.buildings.keys()) == set(state_with.buildings.keys())
    for bid, bld in state_without.buildings.items():
        assert bld.position == state_with.buildings[bid].position


def test_compiler_terrain_variants_empty_list_behaves_as_not_declared():
    """terrain_variants=[] (empty list, distinct from None at the schema level) behaves
    identically to not declaring variants at all -- Python truthiness on `if
    r_spec.terrain_variants:` already treats [] as falsy, no special-casing needed."""
    data_empty = create_base_valid_spec()
    data_empty["regions"][1]["terrain_variants"] = []
    data_none = create_base_valid_spec()
    data_none["regions"][1]["terrain_variants"] = None

    spec_empty = WorldSpec.model_validate(data_empty)
    spec_none = WorldSpec.model_validate(data_none)

    state_empty, _ = WorldCompiler.compile(spec_empty, seed=42)
    state_none, _ = WorldCompiler.compile(spec_none, seed=42)

    region_tiles_empty = {(x, y): state_empty.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    region_tiles_none = {(x, y): state_none.terrain[(x, y)] for x in range(15, 41) for y in range(15, 41)}
    assert region_tiles_empty == region_tiles_none


def test_compiler_terrain_variants_tile_offset_injective_across_wide_regions():
    """The corrected tile_offset encoding (16 bits per axis) is collision-free for y >= 256 --
    the original 8-bit-y-packing scheme (x << 8) | y collided on e.g. (x=0, y=256) vs.
    (x=1, y=0), both producing offset 256. Added during Review to close that bug directly
    (TCK-20260821-COMPILER-NOISE-FILL).

    Spies on DeterministicRNG.weighted_choice to capture the real entity_id argument compiler.py
    actually computes and passes for every tile -- a standalone recomputation of the formula in
    the test body (the original version of this test) would pass unchanged even if compiler.py
    regressed to the buggy (x << 8) | y encoding, since it never exercises the code under test.
    This version fails if compiler.py's real per-tile entity_id computation collides."""
    from unittest.mock import patch
    from src.platform.rng import DeterministicRNG

    data = create_base_valid_spec()
    data["topology"]["width"] = 10
    data["topology"]["height"] = 305
    data["regions"] = [
        {
            "id": "wide_region", "type": "wilderness", "bounds": [0, 0, 5, 300], "terrain": "FOREST",
            "terrain_variants": [
                {"terrain": "FOREST", "weight": 1.0},
                {"terrain": "SWAMP", "weight": 1.0},
            ],
        },
    ]
    data["entities"] = []
    data["resources"] = []
    data["buildings"] = []
    data["quest_definitions"] = []
    spec = WorldSpec.model_validate(data)

    captured_entity_ids = []
    original_weighted_choice = DeterministicRNG.weighted_choice

    def spying_weighted_choice(self, domain, tick, entity_id, seq, weights, sub_id=0):
        captured_entity_ids.append(entity_id)
        return original_weighted_choice(self, domain, tick, entity_id, seq, weights, sub_id=sub_id)

    with patch.object(DeterministicRNG, "weighted_choice", spying_weighted_choice):
        WorldCompiler.compile(spec, seed=42)

    # 6 * 301 in-bounds tiles in the region (x: 0-5, y: 0-300); every tile must have triggered
    # exactly one weighted_choice call with a distinct entity_id -- a collision would mean two
    # different tiles produced the same entity_id and therefore drew from the same seeded random
    # source, silently correlating their terrain assignment.
    assert len(captured_entity_ids) == 6 * 301
    assert len(set(captured_entity_ids)) == len(captured_entity_ids), (
        "compiler.py's real per-tile entity_id computation produced a duplicate for at least one "
        "(x, y) pair -- this is exactly the class of collision the corrected 16-bits-per-axis "
        "tile_offset encoding exists to eliminate"
    )


def test_compiler_faction_bravery_bias_produces_real_action_style_skew():
    """A predator faction's real, compiled population should skew toward AGGRESSIVE ActionStyle
    (previously every entity defaulted to BALANCED regardless of faction) -- the real mechanism
    that activates dormant kiting-distance and opportunity-attack-escape differentiation."""
    data = create_base_valid_spec()
    data["regions"].append({"id": "predator_zone", "type": "wilderness", "bounds": [20, 20, 40, 40], "terrain": "FOREST"})
    data["factions"] = [{"id": "wild_beast_pack", "type": "hostile"}]
    data["entities"] = [
        {"id": "predators", "count": 30, "role": "monster", "faction": "wild_beast_pack", "spawn_region": "predator_zone"},
    ]
    spec = WorldSpec.model_validate(data)
    state, _ = WorldCompiler.compile(spec, seed=42)

    styles = [e.combat.action_style for e in state.entities.values()]
    assert len(styles) == 30
    # Not every entity is the class default (BALANCED=0) -- action_style is real, not dormant.
    assert any(s != 0 for s in styles)
    aggressive_count = sum(1 for s in styles if s == ActionStyle.AGGRESSIVE)
    assert aggressive_count > len(styles) / 2, (
        "wild_beast_pack's high bravery bias (+0.35) should skew most entities AGGRESSIVE"
    )
