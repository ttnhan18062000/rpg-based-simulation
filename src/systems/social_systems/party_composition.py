"""
PartyCompositionScorer — evaluate candidate party composition quality.

Ticket: TCK-20260628-E41F-PARTY-SCORER
Logic IDs: SOC-231 (role diversity), SOC-232 (OCEAN compatibility)
Logic ID: SOC-244 (trust/bonds-aware composition + confidence, TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY)
Logic ID: SOC-247 (RelationshipRole affinity term, TCK-20260824-RELATIONSHIP-ROLE-FIELD)

Score combines:
- Role diversity (TANK/HEALER/DPS/SUPPORT coverage): 60% weight
- OCEAN complementarity (bravery + sociability variance): 40% weight
- Trust/bonds directed sentiment (optional, when actor supplied): weight 0.15, additive
- RelationshipRole affinity (optional, when actor supplied): weight 0.10, additive

Result (0.0–1.0) feeds into the FORM_PARTY route's expected_benefit so that
sociable entities prefer forming parties when the candidate pool is balanced.
"""
from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from src.core.models.social import RelationshipRole

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
    TRUST_BONUS_WEIGHT: float = 0.15
    ROLE_AFFINITY_WEIGHT: float = 0.10

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

    @staticmethod
    def _candidate_trust_value(actor: "EntityState", candidate: "EntityState") -> float:
        """
        Directed trust/bond value the acting entity holds toward one specific candidate,
        on trust_history/SocialBond.sentiment's shared native -1.0..1.0 scale. Bond
        sentiment takes priority over trust_history when both exist (established
        precedent: appraisal.py's SocialAppraisalSystem.appraise_contract(), "Private
        sentiment takes priority"; docs/simulation/social_systems_contract.md's
        "Bond sentiment takes priority over trust_history in appraisal"). Neutral
        default 0.0 for a candidate with no prior relationship record.
        """
        bond = actor.social.bonds.get(candidate.id)
        if bond is not None:
            return bond.sentiment
        return actor.social.trust_history.get(candidate.id, 0.0)

    @staticmethod
    def score_trust_bonds(actor: "EntityState", entities: "List[EntityState]") -> float:
        """
        Mean directed trust/bond sentiment the acting entity holds toward each
        candidate in the pool, read from the acting entity's own SocialComponent
        only (never global/omniscient state). Range: -1.0 to 1.0. Empty pool -> 0.0.
        """
        if not entities:
            return 0.0
        values = [
            PartyCompositionScorer._candidate_trust_value(actor, e) for e in entities
        ]
        return round(sum(values) / len(values), 4)

    @staticmethod
    def _candidate_role_value(actor: "EntityState", candidate: "EntityState") -> float:
        """
        Directed RelationshipRole value the acting entity holds toward one specific
        candidate: FRIEND -> +1.0, RIVAL -> -1.0, NEUTRAL or no bond -> 0.0.
        """
        bond = actor.social.bonds.get(candidate.id)
        if bond is None:
            return 0.0
        if bond.role == RelationshipRole.FRIEND:
            return 1.0
        if bond.role == RelationshipRole.RIVAL:
            return -1.0
        return 0.0

    @staticmethod
    def score_role_affinity(actor: "EntityState", entities: "List[EntityState]") -> float:
        """
        Mean directed RelationshipRole affinity the acting entity holds toward each
        candidate in the pool. Range: -1.0 to 1.0. Empty pool -> 0.0.
        """
        if not entities:
            return 0.0
        values = [
            PartyCompositionScorer._candidate_role_value(actor, e) for e in entities
        ]
        return round(sum(values) / len(values), 4)

    @classmethod
    def score(
        cls, entities: "List[EntityState]", *, actor: "Optional[EntityState]" = None
    ) -> float:
        """
        Combined composition quality score, 0.0-1.0.
        Weighted sum of role diversity and OCEAN complementarity, plus an optional
        trust/bonds-aware adjustment when `actor` (the entity forming the party) is
        supplied (TCK-20260811-RELATIONSHIP-AWARE-FORM-PARTY). Omitting `actor`
        reproduces today's exact pre-existing output -- every pre-existing call site
        does this.
        """
        if not entities:
            return 0.0
        role_div = cls.score_role_diversity(entities)
        ocean_compat = cls.score_ocean_compatibility(entities)
        base_score = (
            cls.ROLE_DIVERSITY_WEIGHT * role_div + cls.OCEAN_COMPAT_WEIGHT * ocean_compat
        )
        if actor is None:
            return round(base_score, 4)
        trust_term = cls.score_trust_bonds(actor, entities)
        role_term = cls.score_role_affinity(actor, entities)
        return round(
            max(
                0.0,
                min(
                    1.0,
                    base_score
                    + cls.TRUST_BONUS_WEIGHT * trust_term
                    + cls.ROLE_AFFINITY_WEIGHT * role_term,
                ),
            ),
            4,
        )
