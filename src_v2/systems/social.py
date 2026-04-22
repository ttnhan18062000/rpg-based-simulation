from __future__ import annotations
from typing import Dict, List, Optional
from src_v2.core.state import EntityState
from src_v2.core.updates import SocialUpdate

class SocialAppraisalSystem:
    """
    Authoritative logic for trust recalibration and social evaluation.
    Matches legacy 'SocialInterpretation' and 'RelationshipService'.
    """

    @staticmethod
    def recalibrate_trust(
        observer: EntityState,
        subject_id: int,
        outcome_quality: float = 0.0, # -1.0 to 1.0
        harm_ratio: float = 0.0,      # damage / max_hp
        help_ratio: float = 0.0       # help / max_hp
    ) -> SocialUpdate:
        """
        Recalculate trust based on a concrete interaction outcome.
        Legacy Parity: 
        - Harm: -0.1 - (harm_ratio * 0.5)
        - Help: 0.05 + (help_ratio * 0.4)
        - General Success/Failure: 0.1 / -0.2
        """
        current_trust = observer.social.trust_history.get(subject_id, 0.5)
        
        trust_delta = 0.0
        
        if harm_ratio > 0:
            trust_delta = -0.1 - (harm_ratio * 0.5)
        elif help_ratio > 0:
            trust_delta = 0.05 + (help_ratio * 0.4)
        else:
            # Fallback to general quality deltas
            if outcome_quality > 0:
                trust_delta = 0.1
            elif outcome_quality < 0:
                trust_delta = -0.2
                
        # Archetype scaling would go here if IdentityComponent had it.
        # For now, we use the base legacy formulas.
        
        return SocialUpdate(trust_delta={subject_id: trust_delta})

    @staticmethod
    def evaluate_recruitment_offer(
        candidate: EntityState,
        recruiter_id: int,
        payout: int,
        risk: float
    ) -> bool:
        """
        Decision logic for offer acceptance.
        Matches legacy test: test_recruitment_offer_evaluation_acceptance.
        """
        trust = candidate.social.trust_history.get(recruiter_id, 0.5)
        
        # Evaluation heuristic:
        # Score = (Trust * 0.5) + (Payout/200 * 0.4) - (Risk * 0.1)
        # Threshold: 0.5
        score = (trust * 0.5) + (min(1.0, payout / 200) * 0.4) - (risk * 0.1)
        
        return score >= 0.5

    @staticmethod
    def record_betrayal(
        target_id: int
    ) -> SocialUpdate:
        """
        Logs a betrayal event impacting reputation.
        """
        return SocialUpdate(betrayal_increment=1)
