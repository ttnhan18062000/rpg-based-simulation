from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from src.core.enums import EntityRole


class RewardCategory(Enum):
    NONE = "none"
    MONSTER_KILL = "monster_kill"
    HERO_KILL = "hero_kill"


@dataclass(frozen=True)
class RewardClassification:
    category: RewardCategory
    xp_multiplier: int      # Multiplier against evolution_level; MONSTER=10, HERO=20, else=0
    gold_multiplier: int    # Multiplier against evolution_level; MONSTER=5, HERO=50, else=0
    gold_eligible: bool
    rebirth_eligible: bool
    source: str             # e.g. "EntityRole.MONSTER"


class CombatRewardClassificationService:
    """
    Owns all entity-role -> reward-category mapping.
    Reads entity role. Does not mutate any state.
    Logic IDs: COMB-279, COMB-280, PROG-004, PROG-064
    """

    _CLASSIFICATIONS: dict[EntityRole, RewardClassification] = {
        EntityRole.MONSTER: RewardClassification(
            category=RewardCategory.MONSTER_KILL,
            xp_multiplier=10,
            gold_multiplier=5,
            gold_eligible=True,
            rebirth_eligible=False,
            source="EntityRole.MONSTER",
        ),
        EntityRole.HERO: RewardClassification(
            category=RewardCategory.HERO_KILL,
            xp_multiplier=20,
            gold_multiplier=50,
            gold_eligible=True,
            rebirth_eligible=True,
            source="EntityRole.HERO",
        ),
    }

    _NONE_CLASSIFICATION = RewardClassification(
        category=RewardCategory.NONE,
        xp_multiplier=0,
        gold_multiplier=0,
        gold_eligible=False,
        rebirth_eligible=False,
        source="EntityRole.NONE",
    )

    @classmethod
    def classify(cls, entity_role: EntityRole) -> RewardClassification:
        return cls._CLASSIFICATIONS.get(entity_role, cls._NONE_CLASSIFICATION)
