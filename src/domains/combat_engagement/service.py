"""
src/domains/combat_engagement/service.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatEngagementDecisionService

Coordinates the subjective pre-combat assessment services.
"""

from __future__ import annotations
from typing import Optional

from src.core.state import EntityState
from src.core.state import AuthoritativeState
from src.domains.combat_engagement.schema import CombatEngagementDecisionResult, OpponentModel
from src.domains.combat_engagement.perception import OpponentPerceptionService
from src.domains.combat_engagement.self_estimate import SelfCombatEstimateService
from src.domains.combat_engagement.risk_evaluator import EngagementRiskEvaluator
from src.domains.combat_engagement.selector import CombatPostureSelector


class CombatEngagementDecisionService:
    """
    Coordinates pre-combat assessment.
    """

    @staticmethod
    def evaluate(
        actor: EntityState,
        target: EntityState,
        state: AuthoritativeState,
        memory: Optional[OpponentModel] = None,
        objective_pressure: float = 0.0,
    ) -> CombatEngagementDecisionResult:
        """
        Evaluate target and actor condition to choose the optimal posture.
        """
        # Fear avoidance: entity that has been defeated by this target >= 3 times avoids engagement.
        if actor.social.combat_loss_counts.get(target.id, 0) >= 3:
            opponent_est = OpponentPerceptionService.estimate(actor, target, memory)
            self_est = SelfCombatEstimateService.estimate(actor)
            from src.domains.combat_engagement.schema import CombatPosture, EngagementRiskEvaluation
            risk_eval = EngagementRiskEvaluation(
                win_confidence=0.0, death_risk=1.0, uncertainty_penalty=0.0,
                objective_value=0.0, personality_bias=0.0, emotional_bias=0.0,
                risk_score=1.0, value_score=0.0, acceptable=False,
                reasons=("fear_avoidance",),
            )
            return CombatEngagementDecisionResult(
                actor_id=actor.id,
                target_id=target.id,
                posture=CombatPosture.AVOID,
                risk_evaluation=risk_eval,
                opponent_estimate=opponent_est,
                self_estimate=self_est,
                reason="fear_avoidance: defeated by this opponent 3+ times",
            )

        opponent_est = OpponentPerceptionService.estimate(actor, target, memory)
        self_est = SelfCombatEstimateService.estimate(actor)
        risk_eval = EngagementRiskEvaluator.evaluate(actor, opponent_est, self_est, objective_pressure)

        return CombatPostureSelector.select(
            actor_id=actor.id,
            target_id=target.id,
            opponent_est=opponent_est,
            self_est=self_est,
            risk_eval=risk_eval,
        )
