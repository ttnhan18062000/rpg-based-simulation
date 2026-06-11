# Compliance IDs: WORLD-073, WORLD-074, WORLD-075
import pytest
from src.worldbuilding.schema import WorldSpec
from src.worldbuilding.compiler import WorldCompiler
from src.worldassembly.context import CompileContext
from src.worldassembly.models import (
    ResolvedEntityProfile,
    ResolvedBuildingProfile,
    ResolvedResourceProfile,
    ResolvedFactionEconomyProfile,
)
from src.core.enums import EntityRole, Faction


def create_base_spec() -> dict:
    return {
        "schema_version": "worldspec.v1",
        "world_id": "test_context_valley",
        "name": "Context Valley",
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
            {"id": "citizen_group", "count": 2, "role": "citizen", "faction": "villagers", "spawn_region": "town_square"},
            {"id": "horde", "count": 1, "role": "monster", "faction": "monsters", "spawn_region": "wilds"}
        ],
        "resources": [
            {"id": "ore_node", "resource_type": "ore", "count": 5, "region": "wilds"}
        ],
        "buildings": [
            {"id": "tavern", "type": "inn", "region": "town_square"}
        ],
        "quests": []
    }


def test_compiler_with_no_context():
    """Verify that compiling without context matches the legacy defaults exactly."""
    data = create_base_spec()
    spec = WorldSpec.model_validate(data)

    state, report = WorldCompiler.compile(spec, seed=42, context=None)

    # Validate legacy defaults
    citizen = state.entities[1]
    assert citizen.combat.hp == 100
    assert citizen.combat.max_hp == 100
    assert citizen.combat.atk == 10
    assert citizen.combat.range == 1
    assert citizen.combat.readiness == 100.0
    assert citizen.combat.def_stat == 0

    node = state.resource_nodes[10000]
    assert node.required_ticks == 10

    building = state.buildings[20000]
    assert building.hp == 500
    assert building.max_hp == 500

    assert state.global_resources.get("faction_hero_guild_gold") == 1000.0


def test_compiler_with_full_context():
    """Verify that specifying a fully populated context overrides all compiler values correctly."""
    data = create_base_spec()
    spec = WorldSpec.model_validate(data)

    context = CompileContext()
    
    # 1. Register overridden entity profiles
    context.register_entity("citizen_group", ResolvedEntityProfile(
        legacy_role=int(EntityRole.GUARD),
        legacy_faction=int(Faction.TOWN_COUNCIL),
        hp=250,
        max_hp=250,
        atk=35,
        def_stat=15,
        attack_range=3,
        readiness=85.0
    ))
    context.register_entity("horde", ResolvedEntityProfile(
        legacy_role=int(EntityRole.MONSTER),
        legacy_faction=int(Faction.MONSTER_HORDE),
        hp=500,
        max_hp=500,
        atk=60,
        def_stat=25,
        attack_range=2,
        readiness=95.0
    ))

    # 2. Register overridden building profile
    context.register_building("tavern", ResolvedBuildingProfile(
        hp=1200,
        max_hp=1200
    ))

    # 3. Register overridden resource profile
    context.register_resource("ore_node", ResolvedResourceProfile(
        required_ticks=25,
        resource_type="ore"
    ))

    # 4. Register overridden faction economy
    context.register_faction("villagers", ResolvedFactionEconomyProfile(starting_gold=4500.0))
    context.register_faction("monsters", ResolvedFactionEconomyProfile(starting_gold=120.0))
    context.register_legacy_faction("villagers", Faction.TOWN_COUNCIL)
    context.register_legacy_faction("monsters", Faction.MONSTER_HORDE)

    # 5. Register region ownership
    context.register_region_ownership("town_square", Faction.TOWN_COUNCIL)

    state, report = WorldCompiler.compile(spec, seed=42, context=context)

    # Verify context-aware dynamic overrides
    citizen = state.entities[1]
    assert citizen.combat.hp == 250
    assert citizen.combat.max_hp == 250
    assert citizen.combat.atk == 35
    assert citizen.combat.def_stat == 15
    assert citizen.combat.range == 3
    assert citizen.combat.readiness == 85.0
    assert citizen.identity.role == EntityRole.GUARD
    assert citizen.identity.faction == Faction.TOWN_COUNCIL

    monster = state.entities[3]
    assert monster.combat.hp == 500
    assert monster.combat.max_hp == 500
    assert monster.combat.def_stat == 25
    assert monster.identity.role == EntityRole.MONSTER

    node = state.resource_nodes[10000]
    assert node.required_ticks == 25

    building = state.buildings[20000]
    assert building.hp == 1200
    assert building.max_hp == 1200

    assert state.global_resources.get("faction_town_council_gold") == 4500.0
    assert state.global_resources.get("faction_monster_horde_gold") == 120.0

    assert state.regions["town_square"].owner_faction_id == Faction.TOWN_COUNCIL


def test_compiler_partially_populated_context():
    """Verify that compiling with a partially populated context selectively overrides parameters."""
    data = create_base_spec()
    spec = WorldSpec.model_validate(data)

    context = CompileContext()
    
    # Override only resource and tavern building, leaving entities and factions as legacy fallbacks
    context.register_resource("ore_node", ResolvedResourceProfile(
        required_ticks=8,
        resource_type="ore"
    ))
    context.register_building("tavern", ResolvedBuildingProfile(
        hp=999,
        max_hp=999
    ))

    state, _ = WorldCompiler.compile(spec, seed=42, context=context)

    # Overridden ones use context
    assert state.resource_nodes[10000].required_ticks == 8
    assert state.buildings[20000].hp == 999

    # Unspecified elements fall back to legacy defaults
    citizen = state.entities[1]
    assert citizen.combat.hp == 100
    assert citizen.combat.atk == 10
    assert state.global_resources.get("faction_hero_guild_gold") == 1000.0


def test_compiler_hash_stability():
    """Verify compile state hash stability for identical seeds and inputs."""
    data = create_base_spec()
    spec = WorldSpec.model_validate(data)

    context = CompileContext()
    context.register_resource("ore_node", ResolvedResourceProfile(
        required_ticks=15,
        resource_type="ore"
    ))

    _, report1 = WorldCompiler.compile(spec, seed=99, context=context)
    _, report2 = WorldCompiler.compile(spec, seed=99, context=context)

    assert report1["state_hash"] == report2["state_hash"]
