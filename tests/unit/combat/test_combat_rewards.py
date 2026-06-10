"""
Unit tests for CombatRewardClassificationService.
Logic IDs: COMB-279, COMB-280, PROG-004, PROG-064
"""
import pytest
from dataclasses import FrozenInstanceError, replace
from src.core.enums import EntityRole, Faction
from src.core.state import EntityState, IdentityComponent
from src.engine.combat_rewards import (
    CombatRewardClassificationService,
    RewardCategory,
    RewardClassification,
)


# ── legacy classify(EntityRole) ──────────────────────────────────────────────

def test_monster_role_classify():
    """Monster role maps to MONSTER_KILL with correct XP/gold multipliers and flags."""
    result = CombatRewardClassificationService.classify(EntityRole.MONSTER)
    assert result.category == RewardCategory.MONSTER_KILL
    assert result.xp_multiplier == 10
    assert result.gold_multiplier == 5
    assert result.gold_eligible is True
    assert result.rebirth_eligible is False


def test_hero_role_classify():
    """Hero role maps to HERO_KILL with correct XP/gold multipliers and rebirth flag."""
    result = CombatRewardClassificationService.classify(EntityRole.HERO)
    assert result.category == RewardCategory.HERO_KILL
    assert result.xp_multiplier == 20
    assert result.gold_multiplier == 50
    assert result.gold_eligible is True
    assert result.rebirth_eligible is True


def test_unknown_role_returns_none_category():
    """An EntityRole that is not MONSTER or HERO returns RewardCategory.NONE with zero multipliers."""
    for role in (EntityRole.SHOPKEEPER, EntityRole.CITIZEN, EntityRole.WORKER, EntityRole.GUARD):
        result = CombatRewardClassificationService.classify(role)
        assert result.category == RewardCategory.NONE, f"Expected NONE for {role}, got {result.category}"
        assert result.xp_multiplier == 0
        assert result.gold_multiplier == 0
        assert result.gold_eligible is False
        assert result.rebirth_eligible is False


def test_classification_carries_source_string():
    """Every returned classification must carry a non-empty source string."""
    for role in EntityRole:
        result = CombatRewardClassificationService.classify(role)
        assert isinstance(result.source, str) and len(result.source) > 0, (
            f"Expected non-empty source for {role}, got {result.source!r}"
        )


def test_classification_is_frozen_dataclass():
    """RewardClassification is frozen; assigning to any field must raise FrozenInstanceError."""
    result = CombatRewardClassificationService.classify(EntityRole.MONSTER)
    with pytest.raises(FrozenInstanceError):
        result.xp_multiplier = 999  # type: ignore[misc]


# ── helpers for classify_defeated_target tests ───────────────────────────────

def _make_entity(entity_id: int, role: EntityRole, faction: Faction) -> EntityState:
    base = EntityState(id=entity_id, kind="HERO")
    return replace(base, identity=replace(base.identity, role=role, faction=faction))


class _FakeState:
    """Minimal AuthoritativeState stub — classify_defeated_target only reads entities."""
    pass


_STATE = _FakeState()


# ── classify_defeated_target ─────────────────────────────────────────────────

def test_classify_defeated_target_monster_horde_returns_hostile_creature():
    """Hero (HERO_GUILD) defeating Monster (MONSTER_HORDE) → HOSTILE_CREATURE via relation_projection."""
    attacker = _make_entity(1, EntityRole.HERO, Faction.HERO_GUILD)
    defender = _make_entity(2, EntityRole.MONSTER, Faction.MONSTER_HORDE)
    result = CombatRewardClassificationService.classify_defeated_target(attacker, defender, _STATE)
    assert result.category == RewardCategory.HOSTILE_CREATURE
    assert result.source == "relation_projection"


def test_classify_defeated_target_monster_attacks_hero_gives_hostile_creature():
    """Monster (MONSTER_HORDE) defeating Hero (HERO_GUILD) → HOSTILE_CREATURE via relation_projection.

    MONSTER_HORDE and HERO_GUILD are mutually hostile in the legacy bucket model.
    Relation projection runs first — the HERO_KILL path is only reached for neutral-faction
    attackers that are not in a hostile relation with the defender.
    """
    attacker = _make_entity(1, EntityRole.MONSTER, Faction.MONSTER_HORDE)
    defender = _make_entity(2, EntityRole.HERO, Faction.HERO_GUILD)
    result = CombatRewardClassificationService.classify_defeated_target(attacker, defender, _STATE)
    assert result.category == RewardCategory.HOSTILE_CREATURE
    assert result.source == "relation_projection"


def test_classify_defeated_target_hero_defender_neutral_attacker_returns_hero_kill():
    """Defender with HERO role, attacker with NEUTRAL faction → HERO_KILL via EntityRole fallback.

    NEUTRAL faction has no hostile relation with HERO_GUILD in the legacy bucket model,
    so relation projection returns False and the EntityRole path is reached.
    """
    attacker = _make_entity(1, EntityRole.CITIZEN, Faction.NEUTRAL)
    defender = _make_entity(2, EntityRole.HERO, Faction.HERO_GUILD)
    result = CombatRewardClassificationService.classify_defeated_target(attacker, defender, _STATE)
    assert result.category == RewardCategory.HERO_KILL
    assert result.rebirth_eligible is True


def test_classify_defeated_target_neutral_merchant_returns_none():
    """Neutral merchant (SHOPKEEPER role, HERO_GUILD faction) → NONE."""
    attacker = _make_entity(1, EntityRole.HERO, Faction.HERO_GUILD)
    defender = _make_entity(2, EntityRole.SHOPKEEPER, Faction.HERO_GUILD)
    result = CombatRewardClassificationService.classify_defeated_target(attacker, defender, _STATE)
    assert result.category == RewardCategory.NONE
    assert result.xp_multiplier == 0


def test_classify_defeated_target_hostile_creature_xp_and_gold_multipliers():
    """HOSTILE_CREATURE classification uses xp_multiplier=10, gold_multiplier=5."""
    attacker = _make_entity(1, EntityRole.HERO, Faction.HERO_GUILD)
    defender = _make_entity(2, EntityRole.MONSTER, Faction.MONSTER_HORDE)
    result = CombatRewardClassificationService.classify_defeated_target(attacker, defender, _STATE)
    assert result.xp_multiplier == 10
    assert result.gold_multiplier == 5
    assert result.gold_eligible is True
    assert result.rebirth_eligible is False
    assert result.source == "relation_projection"


def test_classify_is_still_a_valid_compatibility_wrapper():
    """classify(EntityRole) unchanged — legacy callers still get correct results."""
    assert CombatRewardClassificationService.classify(EntityRole.MONSTER).category == RewardCategory.MONSTER_KILL
    assert CombatRewardClassificationService.classify(EntityRole.HERO).category == RewardCategory.HERO_KILL
