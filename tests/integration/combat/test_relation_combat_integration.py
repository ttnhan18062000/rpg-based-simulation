import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityRole
from src.core.enums import ReasonCode, Faction
from src.core.builder import V2EntityBuilder
from src.engine.legality import LegalityServiceV2
from src.engine.tactical import TacticalDecisionSystem
from src.content_semantics.faction import get_faction_semantics_service, get_faction_id_str, get_race_id_str, reset_faction_semantics_service
from src.content_semantics.relation import RelationContext


@pytest.fixture(autouse=True)
def reset_semantics_cache():
    """Reset the faction semantics singleton after each test to prevent cross-test state leakage."""
    yield
    reset_faction_semantics_service()

def create_relation_entity(e_id, pos, faction_id, faction_enum=Faction.NEUTRAL, role=EntityRole.HERO, race_id=None):
    properties = {"faction_id": faction_id}
    if race_id:
        properties["race_id"] = race_id
    return (V2EntityBuilder(e_id)
            .kind("actor")
            .location(*pos)
            .identity(faction=faction_enum, role=role, properties=properties)
            .combat(hp=100, atk=10, def_stat=5, attack_range=1, readiness=100.0)
            .build())

def test_integration_perspective_hostility():
    """Verify that hero_guild targets goblin_warband dynamically based on perspectives.yaml."""
    hero = create_relation_entity(1, (1.0, 1.0), "hero_guild", Faction.HERO_GUILD, EntityRole.HERO)
    goblin = create_relation_entity(2, (2.0, 1.0), "goblin_warband", Faction.MONSTER_HORDE, EntityRole.MONSTER)

    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})

    # Test hostility classification
    semantics_service = get_faction_semantics_service()
    context = RelationContext(distance=1.0, combat_engaged=False, target_race=None, intruding=False)
    
    # hero_guild perspective maps goblin_warband in hostile_groups
    assert semantics_service.is_hostile_compat("hero_guild", "goblin_warband", context) is True

    # Check that LegalityService accepts attack from hero -> goblin
    legal, reason = LegalityServiceV2.verify_attack_legality(hero, goblin, state)
    assert legal is True

    # Check that LegalityService rejects attack from hero -> hero (friendly fire)
    hero_ally = create_relation_entity(3, (2.0, 1.0), "hero_guild", Faction.HERO_GUILD, EntityRole.HERO)
    legal_ally, reason_ally = LegalityServiceV2.verify_attack_legality(hero, hero_ally, state)
    assert legal_ally is False
    assert reason_ally == ReasonCode.FRIENDLY_FIRE_ILLEGAL

def test_integration_contextual_beast_threat():
    """Verify that wild_beast_pack is only hostile when close or engaged."""
    hero = create_relation_entity(1, (1.0, 1.0), "hero_guild", Faction.HERO_GUILD, EntityRole.HERO)
    beast_far = create_relation_entity(2, (10.0, 1.0), "wild_beast_pack", Faction.MONSTER_HORDE, EntityRole.MONSTER)
    beast_near = create_relation_entity(3, (2.0, 1.0), "wild_beast_pack", Faction.MONSTER_HORDE, EntityRole.MONSTER)

    state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: beast_far, 3: beast_near})

    semantics_service = get_faction_semantics_service()

    # Beast far: distance 9.0, not engaged -> not hostile
    context_far = RelationContext(distance=9.0, combat_engaged=False, target_race=None, intruding=False)
    assert semantics_service.is_hostile_compat("hero_guild", "wild_beast_pack", context_far) is False

    # Beast near: distance 1.0, not engaged -> hostile (contextual threat <= 5.0)
    context_near = RelationContext(distance=1.0, combat_engaged=False, target_race=None, intruding=False)
    assert semantics_service.is_hostile_compat("hero_guild", "wild_beast_pack", context_near) is True

    # Beast far but engaged -> hostile
    context_engaged = RelationContext(distance=9.0, combat_engaged=True, target_race=None, intruding=False)
    assert semantics_service.is_hostile_compat("hero_guild", "wild_beast_pack", context_engaged) is True

def test_integration_legacy_fallback():
    """Verify fallback to legacy faction semantics when dynamic config is missing."""
    # Using dummy/unconfigured faction IDs that contain keywords for legacy mapping
    entity_a = create_relation_entity(1, (1.0, 1.0), "unconfigured_hero_faction", Faction.HERO_GUILD, EntityRole.HERO)
    entity_b = create_relation_entity(2, (2.0, 1.0), "unconfigured_monster_faction", Faction.MONSTER_HORDE, EntityRole.MONSTER)

    state = AuthoritativeState(tick=1, seed=42, entities={1: entity_a, 2: entity_b})

    semantics_service = get_faction_semantics_service()
    context = RelationContext(distance=1.0, combat_engaged=False, target_race=None, intruding=False)

    # Missing dynamic data -> falls back to legacy bucket mapping:
    # "unconfigured_hero_faction" gets HERO_GUILD, "unconfigured_monster_faction" gets MONSTER_HORDE
    # Since MONSTER_HORDE is hostile to HERO_GUILD, it should be hostile
    assert semantics_service.is_hostile_compat("unconfigured_hero_faction", "unconfigured_monster_faction", context) is True

