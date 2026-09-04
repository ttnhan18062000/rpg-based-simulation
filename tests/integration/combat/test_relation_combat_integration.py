import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState, EntityRole
from src.core.enums import ReasonCode, Faction
from src.core.builder import V2EntityBuilder
from src.engine.legality import LegalityServiceV2
from src.engine.tactical import TacticalDecisionSystem
from src.content_semantics.faction import get_faction_semantics_service, get_faction_id_str, get_species_id_str, reset_faction_semantics_service
from src.content_semantics.relation import RelationContext


@pytest.fixture(autouse=True)
def reset_semantics_cache():
    """Reset the faction semantics singleton after each test to prevent cross-test state leakage."""
    yield
    reset_faction_semantics_service()

def create_relation_entity(e_id, pos, faction_id, faction_enum=Faction.NEUTRAL, role=EntityRole.HERO, species_id=None):
    properties = {"faction_id": faction_id}
    if species_id:
        properties["species_id"] = species_id
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
    context = RelationContext(distance=1.0, combat_engaged=False, target_species=None, intruding=False)
    
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
    context_far = RelationContext(distance=9.0, combat_engaged=False, target_species=None, intruding=False)
    assert semantics_service.is_hostile_compat("hero_guild", "wild_beast_pack", context_far) is False

    # Beast near: distance 1.0, not engaged -> hostile (contextual threat <= 5.0)
    context_near = RelationContext(distance=1.0, combat_engaged=False, target_species=None, intruding=False)
    assert semantics_service.is_hostile_compat("hero_guild", "wild_beast_pack", context_near) is True

    # Beast far but engaged -> hostile
    context_engaged = RelationContext(distance=9.0, combat_engaged=True, target_species=None, intruding=False)
    assert semantics_service.is_hostile_compat("hero_guild", "wild_beast_pack", context_engaged) is True

def test_integration_legacy_fallback():
    """Verify fallback to legacy faction semantics when dynamic config is missing."""
    # Using dummy/unconfigured faction IDs that contain keywords for legacy mapping
    entity_a = create_relation_entity(1, (1.0, 1.0), "unconfigured_hero_faction", Faction.HERO_GUILD, EntityRole.HERO)
    entity_b = create_relation_entity(2, (2.0, 1.0), "unconfigured_monster_faction", Faction.MONSTER_HORDE, EntityRole.MONSTER)

    state = AuthoritativeState(tick=1, seed=42, entities={1: entity_a, 2: entity_b})

    semantics_service = get_faction_semantics_service()
    context = RelationContext(distance=1.0, combat_engaged=False, target_species=None, intruding=False)

    # Missing dynamic data -> falls back to legacy bucket mapping:
    # "unconfigured_hero_faction" gets HERO_GUILD, "unconfigured_monster_faction" gets MONSTER_HORDE
    # Since MONSTER_HORDE is hostile to HERO_GUILD, it should be hostile
    assert semantics_service.is_hostile_compat("unconfigured_hero_faction", "unconfigured_monster_faction", context) is True


# TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS / COMB-294: every new relationship pair whose
# *source* faction lacks a perspectives.yaml entry deterministically flips that pair's
# `is_hostile_compat()` gate from False to True. The two consumers of that gate have DIFFERENT
# pre-change fallbacks (see plan.md Step 4): `combat_rewards.py`'s `is_hostile()` fallback is
# alignment_bucket-based, while `legality.py`'s own Friendly-Fire fallback is
# legacy_engine_bucket-based (raw `attacker.identity.faction == target.identity.faction`). A pair
# can show no change on one fallback while still flipping the other — each row below is the real,
# already-authored `data/content/social/faction_relationships.yaml` entry, and `expected_illegal`
# is the NEW post-change Friendly-Fire verdict (not the pre-change one; the old fallback is no
# longer reachable for these pairs once the relationship record exists).
NEW_NON_PERSPECTIVE_SOURCE_PAIRS = [
    # MONSTER_HORDE-bucket pairs: legacy Friendly-Fire fallback was ILLEGAL (equal buckets);
    # the new relationship's unconditional "high"/"medium" hostility makes them hostile, so
    # Friendly Fire now correctly allows the attack (illegal -> legal).
    ("bandit_company", Faction.MONSTER_HORDE, "wild_beast_pack", Faction.MONSTER_HORDE,
     True, False, "dungeon_crawl (anchor)"),
    ("orc_clan", Faction.MONSTER_HORDE, "wild_beast_pack", Faction.MONSTER_HORDE,
     True, False, "resource_dense_basin/frontier_extended/frontier_marches (non-anchor only)"),
    ("bandit_company", Faction.MONSTER_HORDE, "goblin_warband", Faction.MONSTER_HORDE,
     True, False, "dungeon_crawl (anchor)"),
    ("bandit_company", Faction.MONSTER_HORDE, "orc_clan", Faction.MONSTER_HORDE,
     True, False, "crowded_frontier/frontier_extended/frontier_marches (non-anchor only)"),
    ("orc_clan", Faction.MONSTER_HORDE, "bandit_company", Faction.MONSTER_HORDE,
     True, False, "crowded_frontier/frontier_extended/frontier_marches (non-anchor only)"),
    ("bandit_company", Faction.MONSTER_HORDE, "undead_remnants", Faction.MONSTER_HORDE,
     True, False, "dungeon_crawl (anchor)"),
    ("bandit_company", Faction.MONSTER_HORDE, "swamp_tribe", Faction.MONSTER_HORDE,
     True, False, "frontier_marches (non-anchor only)"),
    ("orc_clan", Faction.MONSTER_HORDE, "undead_remnants", Faction.MONSTER_HORDE,
     True, False, "frontier_extended/frontier_marches (non-anchor only)"),
    ("orc_clan", Faction.MONSTER_HORDE, "swamp_tribe", Faction.MONSTER_HORDE,
     True, False, "frontier_marches (non-anchor only)"),
    # NEUTRAL-bucket pairs: legacy fallback was already ILLEGAL (equal buckets); the new
    # "none" hostility relationship keeps Friendly Fire ILLEGAL (not hostile) -> no verdict flip.
    ("spirit_court", Faction.NEUTRAL, "merchant_league", Faction.NEUTRAL,
     False, True, "frontier_extended (non-anchor); no anchor world has spirit_court"),
    ("arcane_circle", Faction.NEUTRAL, "merchant_league", Faction.NEUTRAL,
     False, True, "generated_frontier_3_42 (non-anchor); no anchor world has arcane_circle"),
    ("spirit_court", Faction.NEUTRAL, "arcane_circle", Faction.NEUTRAL,
     False, True, "inert: no current world populates both factions together"),
    ("arcane_circle", Faction.NEUTRAL, "spirit_court", Faction.NEUTRAL,
     False, True, "inert: no current world populates both factions together"),
    # HERO_GUILD-bucket pair: legacy fallback already ILLEGAL (equal buckets); no flip.
    ("forest_wardens", Faction.HERO_GUILD, "hero_guild", Faction.HERO_GUILD,
     False, True, "inert: no current world populates both factions together"),
    # Cross-bucket pairs: legacy fallback was LEGAL (different buckets, no friendly-fire block
    # applied at all between them); the new "none"-hostility relationship now protects them as
    # non-hostile allies, so Friendly Fire flips to ILLEGAL (legal -> illegal).
    ("forest_wardens", Faction.HERO_GUILD, "merchant_league", Faction.NEUTRAL,
     False, True, "frontier_extended (non-anchor only)"),
    ("neutral", Faction.NEUTRAL, "town_council", Faction.TOWN_COUNCIL,
     False, True, "universal get_faction_id_str() fallback ID; no world explicitly assigns "
                  "'neutral' as a populated faction"),
]


@pytest.mark.parametrize(
    "source_id,source_enum,target_id,target_enum,expected_hostile,expected_illegal,world_note",
    NEW_NON_PERSPECTIVE_SOURCE_PAIRS,
)
def test_new_catalog_pair_is_hostile_compat_delta(
    source_id, source_enum, target_id, target_enum, expected_hostile, expected_illegal, world_note
):
    """Step 4 item 1: combat_rewards.py's is_hostile_compat() delta for each new non-perspective-
    source pair, using the real authored data/content/social/faction_relationships.yaml entry."""
    semantics_service = get_faction_semantics_service()
    context = RelationContext(distance=1.0, combat_engaged=True, target_species=None, intruding=False)
    assert semantics_service.is_hostile_compat(source_id, target_id, context) is expected_hostile


@pytest.mark.parametrize(
    "source_id,source_enum,target_id,target_enum,expected_hostile,expected_illegal,world_note",
    NEW_NON_PERSPECTIVE_SOURCE_PAIRS,
)
def test_new_catalog_pair_legality_friendly_fire_delta(
    source_id, source_enum, target_id, target_enum, expected_hostile, expected_illegal, world_note
):
    """Step 4 item 2 (+ item 4, per world_note): LegalityServiceV2's own separate Friendly-Fire
    fallback (legacy_engine_bucket-based) diverges from is_hostile_compat()'s alignment_bucket
    fallback, so this must be verified independently via a real verify_attack_legality() call —
    not inferred from the is_hostile_compat() delta above. Entities use each faction's real
    catalog legacy_engine_bucket (source_enum/target_enum) exactly as world-assembly sets them."""
    attacker = create_relation_entity(1, (1.0, 1.0), source_id, source_enum, EntityRole.MONSTER)
    target = create_relation_entity(2, (2.0, 1.0), target_id, target_enum, EntityRole.MONSTER)
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert legal is (not expected_illegal)
    if expected_illegal:
        assert reason == ReasonCode.FRIENDLY_FIRE_ILLEGAL

