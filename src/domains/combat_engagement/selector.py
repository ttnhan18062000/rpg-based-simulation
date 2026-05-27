"""
src/domains/combat_engagement/selector.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatPostureSelector

Maps EngagementRiskEvaluation profile to subjective CombatPosture enums.
"""

from __future__ import annotations
from typing import Optional

from src.domains.combat_engagement.schema import (
    CombatPosture,
    PerceivedOpponentEstimate,
    SelfCombatEstimate,
    EngagementRiskEvaluation,
    CombatEngagementDecisionResult,
)


class CombatPostureSelector:
    """
    Selects the tactical posture for combat engagement.
    """

    @staticmethod
    def select(
        actor_id: int,
        target_id: int,
        opponent_est: PerceivedOpponentEstimate,
        self_est: SelfCombatEstimate,
        risk_eval: EngagementRiskEvaluation,
    ) -> CombatEngagementDecisionResult:
        """
        Choose the best posture and return the decision result.
        """
        posture = CombatPosture.IGNORE
        reason = "Target ignored by default."

        # High level checks: near death retreats
        if "near_death" in self_est.constraints:
            posture = CombatPosture.RETREAT
            reason = "HP is critical, initiating retreat."
            
        elif "no_stamina" in self_est.constraints:
            posture = CombatPosture.AVOID
            reason = "Exhausted, routing around opponent."

        elif "grudge_vengeance" in risk_eval.reasons:
            posture = CombatPosture.VENGEANCE_ENGAGE
            reason = "Grudge vengeance override."

        elif risk_eval.acceptable:
            # Risk is acceptable, evaluate posture kind based on confidence
            if risk_eval.win_confidence > 0.6:
                posture = CombatPosture.ENGAGE
                reason = "Acceptable risk with high win confidence, committing to fight."
            elif opponent_est.uncertainty > 0.3:
                posture = CombatPosture.PROBE
                reason = "Risk acceptable but uncertainty is high, probing target."
            else:
                posture = CombatPosture.SKIRMISH
                reason = "Risk acceptable, choosing skirmishing combat posture."

        else:
            # Risk rejected
            if opponent_est.estimated_power > self_est.estimated_power * 1.5:
                posture = CombatPosture.AVOID
                reason = "Target appears significantly stronger, routing around."
            elif risk_eval.death_risk > 0.7:
                posture = CombatPosture.PANIC_FLEE
                reason = "Danger too high, panic fleeing."
            else:
                posture = CombatPosture.WATCH
                reason = "Risk rejected, watching target without commitment."

        return CombatEngagementDecisionResult(
            actor_id=actor_id,
            target_id=target_id,
            posture=posture,
            risk_evaluation=risk_eval,
            opponent_estimate=opponent_est,
            self_estimate=self_est,
            reason=reason,
            trace={
                "posture": posture.value,
                "win_confidence": risk_eval.win_confidence,
                "death_risk": risk_eval.death_risk,
            },
        )
