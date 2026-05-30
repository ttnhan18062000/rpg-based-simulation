"""
src/domains/combat_engagement/risk_evaluator.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — EngagementRiskEvaluator

Balances estimated win chance, death risk, uncertainty, quest objective pressure,
and personality trait biases.
"""

from __future__ import annotations
from typing import Tuple

from src.core.state import EntityState
from src.domains.combat_engagement.schema import (
    PerceivedOpponentEstimate,
    SelfCombatEstimate,
    EngagementRiskEvaluation,
)


class EngagementRiskEvaluator:
    """
    Evaluates pre-combat tactical risks vs objectives value.
    """

    @staticmethod
    def evaluate(
        actor: EntityState,
        opponent_est: PerceivedOpponentEstimate,
        self_est: SelfCombatEstimate,
        objective_pressure: float = 0.0,
    ) -> EngagementRiskEvaluation:
        """
        Produce subjective EngagementRiskEvaluation based on perceived capabilities
        and actor traits.
        """
        reasons: list[str] = []

        # ── 1. Fetch Traits (Biased Normalisation) ───────────────────────────
        def get_trait(trait_name: str) -> float:
            traits = getattr(actor.identity, "personality", None)
            if traits is None:
                return 0.5
            val = getattr(traits, trait_name, 0.5)
            if val is None:
                return 0.5
            if val > 1.0:
                return val / 100.0
            return val

        bravery = get_trait("bravery")
        greed = get_trait("greed")
        sociability = get_trait("sociability")
        
        # Derive caution from bravery
        caution = max(0.0, min(1.0, 1.0 - bravery))

        # ── 2. Victory Confidence & Death Risk ───────────────────────────────
        power_ratio = self_est.estimated_power / max(1.0, opponent_est.estimated_power)
        win_confidence = max(0.05, min(0.95, power_ratio * 0.5))

        # Death risk grows exponentially as power ratio drops
        death_risk = max(0.0, min(1.0, (1.0 / max(0.1, power_ratio)) * 0.4))
        
        # If actor has near_death condition, death risk is extremely high
        if "near_death" in self_est.constraints:
            death_risk = max(0.9, death_risk)
            reasons.append("near_death_alert")

        # ── 3. Bias and Penalties ────────────────────────────────────────────
        # High uncertainty penalizes engagement
        uncertainty_penalty = opponent_est.uncertainty * 0.25
        if uncertainty_penalty > 0.1:
            reasons.append("high_uncertainty_penalty")

        # Objective pressure (quest value multiplier)
        objective_value = objective_pressure * 0.4
        if objective_value > 0.1:
            reasons.append("quest_target_bonus")

        # Personality biases
        personality_bias = (bravery * 0.3) - (caution * 0.3) + (greed * 0.1)

        # Check properties for a grudge modifier
        props = getattr(actor.identity, "properties", {}) or {}
        grudges = props.get("grudges", {}) or {}
        target_str = str(opponent_est.target_id)
        grudge_value = grudges.get(target_str, 0.0)
        
        emotional_bias = 0.0
        if grudge_value > 0.0:
            # Grudge generates high emotional bias overriding caution
            grudge_norm = grudge_value / 100.0 if grudge_value > 1.0 else grudge_value
            emotional_bias += grudge_norm * 0.5
            reasons.append("grudge_vengeance")

        # ── 4. Final Scores ──────────────────────────────────────────────────
        value_score = win_confidence + objective_value + personality_bias + emotional_bias
        risk_score = death_risk + uncertainty_penalty - (bravery * 0.2)

        value_score = round(max(0.0, value_score), 4)
        risk_score = round(max(0.0, risk_score), 4)

        # Acceptability gate
        acceptable = (value_score >= risk_score)
        
        # Severe safety locks: low health cannot accept risks unless massive grudge exists
        if death_risk > 0.8 and emotional_bias < 0.3:
            acceptable = False
            reasons.append("hp_critical_safety_lock")

        if acceptable:
            reasons.append("risk_benefit_acceptable")
        else:
            reasons.append("risk_benefit_rejected")

        return EngagementRiskEvaluation(
            win_confidence=round(win_confidence, 2),
            death_risk=round(death_risk, 2),
            uncertainty_penalty=round(uncertainty_penalty, 2),
            objective_value=round(objective_value, 2),
            personality_bias=round(personality_bias, 2),
            emotional_bias=round(emotional_bias, 2),
            risk_score=risk_score,
            value_score=value_score,
            acceptable=acceptable,
            reasons=tuple(reasons),
        )
