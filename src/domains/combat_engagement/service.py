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
