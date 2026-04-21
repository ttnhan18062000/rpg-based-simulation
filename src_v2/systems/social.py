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
        outcome_quality: float # 1.0 for success, -1.0 for false lead/betrayal
    ) -> SocialUpdate:
        """
        Recalculate trust based on a concrete interaction outcome.
        Legacy test parity: test_source_trust_recalibration.
        """
        current_trust = observer.social.trust_history.get(subject_id, 0.5) # Default 0.5 (Neutral)
        
        # Recalibration logic: 
        # Success adds 0.1 (capped at 1.0)
        # Failure/Betrayal reduces 0.2 (floor at 0.0)
        if outcome_quality > 0:
            new_trust = min(1.0, current_trust + 0.1)
        else:
            new_trust = max(0.0, current_trust - 0.2)
            
        return SocialUpdate(trust_delta={subject_id: new_trust - current_trust})

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
