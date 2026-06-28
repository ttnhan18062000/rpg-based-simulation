"""
PartyCompositionScorer — evaluate candidate party composition quality.

Ticket: TCK-20260628-E41F-PARTY-SCORER
Logic IDs: SOC-231 (role diversity), SOC-232 (OCEAN compatibility)

Score combines:
- Role diversity (TANK/HEALER/DPS/SUPPORT coverage): 60% weight
- OCEAN complementarity (bravery + sociability variance): 40% weight

Result (0.0–1.0) feeds into the FORM_PARTY route's expected_benefit so that
sociable entities prefer forming parties when the candidate pool is balanced.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from src.core.state import EntityState


class PartyRole(str, Enum):
    """Functional role within a party, inferred from entity kind and personality."""
    TANK = "tank"
    HEALER = "healer"
    DPS = "dps"
    SUPPORT = "support"


class PartyCompositionScorer:
    """
    Pure-static scorer for party composition quality.

    All methods are deterministic pure functions — no state mutation.
    """

    ROLE_DIVERSITY_WEIGHT: float = 0.6
    OCEAN_COMPAT_WEIGHT: float = 0.4

    @staticmethod
    def infer_party_role(entity: "EntityState") -> PartyRole:
        """Map entity kind + OCEAN bravery/sociability to a party role."""
        kind = (getattr(entity, "kind", "") or "").lower()
        personality = getattr(entity.identity, "personality", None)
        bravery = getattr(personality, "bravery", 0.5) if personality else 0.5
        sociability = getattr(personality, "sociability", 0.5) if personality else 0.5

        # Kind-based mapping takes priority
        if kind in ("guard", "sentinel", "guardian", "brute"):
            return PartyRole.TANK
        if kind in ("healer", "mage", "shaman", "druid"):
            return PartyRole.HEALER
        if kind in ("hero", "ranger", "hunter", "scout"):
            # Heroes lean TANK when brave, DPS otherwise
            return PartyRole.TANK if bravery >= 0.6 else PartyRole.DPS
        if kind in ("worker", "merchant", "citizen", "blacksmith"):
            return PartyRole.SUPPORT

        # Trait-based fallback
        if bravery >= 0.7:
            return PartyRole.TANK
        if sociability >= 0.6:
            return PartyRole.SUPPORT
        return PartyRole.DPS

    @staticmethod
    def score_role_diversity(entities: "List[EntityState]") -> float:
        """
        Fraction of the 4 party roles (TANK/HEALER/DPS/SUPPORT) represented.
        0.0 = all entities have same role; 1.0 = all 4 roles present.
        """
        if not entities:
            return 0.0
        roles = {PartyCompositionScorer.infer_party_role(e) for e in entities}
        return len(roles) / 4.0

    @staticmethod
    def score_ocean_compatibility(entities: "List[EntityState]") -> float:
        """
        Complementary-trait score based on bravery and sociability variance.
        High variance → diverse personalities → better complementarity.
        Returns 0.0–1.0.
        """
        if len(entities) < 2:
            return 0.5  # neutral — no comparison possible

        braveries: List[float] = []
        socials: List[float] = []
        for e in entities:
            p = getattr(e.identity, "personality", None)
            braveries.append(getattr(p, "bravery", 0.5) if p else 0.5)
            socials.append(getattr(p, "sociability", 0.5) if p else 0.5)

        def _variance(vals: List[float]) -> float:
            mean = sum(vals) / len(vals)
            return sum((v - mean) ** 2 for v in vals) / len(vals)

        # Max variance for uniform [0,1] range is 0.25; normalise to 0–1
        bravery_score = min(1.0, _variance(braveries) / 0.25)
        social_score = min(1.0, _variance(socials) / 0.25)
        return round((bravery_score + social_score) / 2.0, 4)

    @classmethod
    def score(cls, entities: "List[EntityState]") -> float:
        """
        Combined composition quality score, 0.0–1.0.
        Weighted sum of role diversity and OCEAN complementarity.
        """
        if not entities:
            return 0.0
        role_div = cls.score_role_diversity(entities)
        ocean_compat = cls.score_ocean_compatibility(entities)
        return round(
            cls.ROLE_DIVERSITY_WEIGHT * role_div
            + cls.OCEAN_COMPAT_WEIGHT * ocean_compat,
            4,
        )
