"""
src/domains/combat_engagement/reassessment.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatReassessmentService

Evaluates dynamic mid-combat updates (HP drops, visible skill updates) to
reassess posture.
"""

from __future__ import annotations
from typing import Sequence, Dict, Any, Optional

from src.core.state import EntityState
from src.domains.combat_engagement.schema import CombatEngagementDecisionResult, CombatPosture
from src.domains.combat_engagement.service import CombatEngagementDecisionService


class CombatReassessmentService:
    """
    Evaluates dynamic mid-combat updates.
    """

    @staticmethod
    def reassess(
        actor: EntityState,
        target: EntityState,
        recent_combat_events: Sequence[Dict[str, Any]],
        previous_decision: CombatEngagementDecisionResult,
        state: Any,
    ) -> CombatEngagementDecisionResult:
        """
        Reassess posture if significant events (damage, skill observed) occurred.
        """
        # Cooldown guard: do not reassess if posture changed too recently
        cooldown_ticks = previous_decision.trace.get("last_reassessed_tick", 0)
        current_tick = getattr(state, "tick", 0)
        
        if current_tick - cooldown_ticks < 3:
            # Skip evaluation, return previous decision
            return previous_decision

        hp = getattr(actor.combat, "hp", 100)
        max_hp = getattr(actor.combat, "max_hp", 100)
        hp_ratio = hp / max(1, max_hp)

        # Trigger conditions
        heavy_damage = False
        skill_observed = False
        
        for ev in recent_combat_events:
            # Check if event is damage to actor
            if ev.get("defender_id") == actor.id:
                dmg = ev.get("damage", 0)
                if dmg > max_hp * 0.2:
                    heavy_damage = True
            
            # Check if target used a special skill
            if ev.get("attacker_id") == target.id:
                if ev.get("skill_id"):
                    skill_observed = True

        if hp_ratio < 0.25:
            # HP is dangerously low, force retreat
            opp_est = previous_decision.opponent_estimate
            self_est = previous_decision.self_estimate
            risk_eval = previous_decision.risk_evaluation
            
            # Create low hp retreat decision
            from src.domains.combat_engagement.selector import CombatPostureSelector
            from src.engine.apply import replace
            
            self_est = replace(self_est, constraints=tuple(list(self_est.constraints) + ["near_death"]))
            
            res = CombatPostureSelector.select(actor.id, target.id, opp_est, self_est, risk_eval)
            # Record last reassessed tick
            res.trace["last_reassessed_tick"] = current_tick
            return res

        if heavy_damage or skill_observed:
            # Run a full subjective evaluation again
            res = CombatEngagementDecisionService.evaluate(actor, target, state)
            new_trace = dict(res.trace)
            new_trace["last_reassessed_tick"] = current_tick
            from src.engine.apply import replace
            return replace(res, trace=new_trace)

        return previous_decision

