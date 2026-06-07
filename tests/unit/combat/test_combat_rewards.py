"""
Unit tests for CombatRewardClassificationService.
Logic IDs: COMB-279, COMB-280, PROG-004, PROG-064
"""
import pytest
from dataclasses import FrozenInstanceError
from src.core.enums import EntityRole
from src.engine.combat_rewards import (
    CombatRewardClassificationService,
    RewardCategory,
    RewardClassification,
)


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
