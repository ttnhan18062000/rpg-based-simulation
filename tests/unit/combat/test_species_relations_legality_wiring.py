"""Legality-path wiring test for RelationContext.source_species (Step 7).

TCK-20260831-RACE-RELATIONS-MATRIX: proves LegalityServiceV2.verify_attack_legality()
now populates RelationContext.source_species, so a real authored species_relations entry can
change the Friendly Fire verdict for a faction pair that itself has no clean perspective
label or faction_relationship entry.

`swamp_tribe` (perspective exists -> has_clean=True) has no faction_relationship entry
pointed at `forest_wardens`, and `forest_wardens` is not listed in any of
swamp_tribe_perspective's projected_labels groups -- so before species-hostility escalation,
project_relation() falls through to the legacy alignment-bucket fallback, which resolves
"neutral" (defender vs rival, neither "invader") -> FRIENDLY_FIRE_ILLEGAL. The authored
goblin_to_elf species_relations entry (hostility: "high") flips this to a legal attack.
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


def _build_entity(entity_id: int, faction_id: str, species_id: str, pos=(1.0, 1.0)):
    return (
        V2EntityBuilder(entity_id)
        .kind("actor")
        .location(*pos)
        .identity(faction=Faction.NEUTRAL, role=EntityRole.MONSTER, properties={"faction_id": faction_id, "species_id": species_id})
        .combat(hp=100, atk=10, def_stat=5, attack_range=1, readiness=100.0)
        .build()
    )


def test_attack_legality_species_hostility_affects_friendly_fire_check():
    attacker = _build_entity(1, "swamp_tribe", "goblin")
    target = _build_entity(2, "forest_wardens", "elf")
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert legal is True, f"Expected legal attack via authored goblin_to_elf species hostility, got {reason}"


def test_attack_legality_no_species_entry_stays_friendly_fire_illegal():
    """Same faction pair, species with no authored species_relations entry (human/spirit) —
    baseline behavior (no escalation) must still resolve to FRIENDLY_FIRE_ILLEGAL, proving
    the species-hostility step is a pure no-op absent an authored entry."""
    attacker = _build_entity(1, "swamp_tribe", "human")
    target = _build_entity(2, "forest_wardens", "spirit")
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: target})

    legal, reason = LegalityServiceV2.verify_attack_legality(attacker, target, state)

    assert legal is False
    assert reason == ReasonCode.FRIENDLY_FIRE_ILLEGAL
