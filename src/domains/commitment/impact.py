"""
src/domains/commitment/impact.py
───────────────────────────────────────────────────────────────────────────────
CommitmentReputationRouteImpact for Phase 15.
"""

from __future__ import annotations
from typing import Iterable
from src.core.state import EntityState

class CommitmentReputationRouteImpact:
    """Applies commitment pressure and reputation biases to scoring."""

    @staticmethod
    def apply_route_bias(entity: EntityState, tags: Iterable[str], base_score: float) -> float:
        score = base_score
        
        # 1. Commitment route boost
        commitments = entity.cognition.commitment.active_commitments
        for entry in commitments.values():
            # If route matches commitment kind/target, boost the score
            if entry.kind in tags or (entry.target_id and str(entry.target_id) in tags):
                score += entry.strength * 0.5

        # 2. Reputation partner fit penalty
        # If the candidate has a known reputation for betrayal, reduce fit score
        # (This will be integrated in cooperation loops)
        return score

    @staticmethod
    def apply_partner_fit_bias(entity: EntityState, candidate_reputation: dict[str, float], base_fit: float) -> float:
        score = base_fit
        if "betrayer" in candidate_reputation:
            score -= candidate_reputation["betrayer"] * 2.0  # Increase penalty weight to reflect deep impact
        if "reliable" in candidate_reputation:
            score += candidate_reputation["reliable"] * 0.2
        return max(0.0, score)
