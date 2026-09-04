"""Legality-path wiring test for RelationContext.source_race (Step 7).

TCK-20260831-RACE-RELATIONS-MATRIX: proves LegalityServiceV2.verify_attack_legality()
now populates RelationContext.source_race, so a real authored race_relations entry can
change the Friendly Fire verdict for a faction pair that itself has no clean perspective
label or faction_relationship entry.

`swamp_tribe` (perspective exists -> has_clean=True) has no faction_relationship entry
pointed at `forest_wardens`, and `forest_wardens` is not listed in any of
swamp_tribe_perspective's projected_labels groups -- so before race-hostility escalation,
project_relation() falls through to the legacy alignment-bucket fallback, which resolves
"neutral" (defender vs rival, neither "invader") -> FRIENDLY_FIRE_ILLEGAL. The authored
goblin_to_elf race_relations entry (hostility: "high") flips this to a legal attack.
"""
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction, EntityRole
from src.core.state import AuthoritativeState
from src.core.enums import ReasonCode
from src.engine.legality import LegalityServiceV2
from src.content_semantics.faction import reset_faction_semantics_service
import pytest


@pytest.fixture(autouse=True)
def reset_semantics_cache():
    yield
    reset_faction_semantics_service()


def _build_entity(entity_id: int, faction_id: str, race_id: str, pos=(1.0, 1.0)):
    return (
        V2EntityBuilder(entity_id)
        .kind("actor")
        .location(*pos)
        # "species_id" stored-key hard coupling with TCK-20260904-SPECIES-CORE-SCHEMA-RENAME
        # (get_race_id_str() now reads entity.identity.properties["species_id"]); the race_id
        # param name and race_relations-subsystem naming here are untouched, that belongs to
        # TCK-20260904-SPECIES-RELATIONS-SUBSYSTEM-RENAME.
        .identity(faction=Faction.NEUTRAL, role=EntityRole.MONSTER, properties={"faction_id": faction_id, "species_id": race_id})
        .combat(hp=100, atk=10, def_stat=5, attack_range=1, readiness=100.0)
        .build()
    )


def test_attack_legality_race_hostility_affects_friendly_fire_check():
    attacker = _build_entity(1, "swamp_tribe", "goblin")
    target = _build_entity(2, "forest_wardens", "elf")
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert legal is True, f"Expected legal attack via authored goblin_to_elf race hostility, got {reason}"


def test_attack_legality_no_race_entry_stays_friendly_fire_illegal():
    """Same faction pair, races with no authored race_relations entry (human/spirit) —
    baseline behavior (no escalation) must still resolve to FRIENDLY_FIRE_ILLEGAL, proving
    the race-hostility step is a pure no-op absent an authored entry."""
    attacker = _build_entity(1, "swamp_tribe", "human")
    target = _build_entity(2, "forest_wardens", "spirit")
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert legal is False
    assert reason == ReasonCode.FRIENDLY_FIRE_ILLEGAL
