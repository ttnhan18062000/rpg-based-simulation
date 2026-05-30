"""
src/domains/emotion/opportunity_cost.py
───────────────────────────────────────────────────────────────────────────────
OpportunityCostEvaluator for Phase 16.
"""

from __future__ import annotations

class OpportunityCostEvaluator:
    """Explicitly computes opportunity cost for competing tactical/strategic routes."""

    @staticmethod
    def evaluate_cost(action_kind: str, is_needed_for_upgrade: bool, has_alternative: bool) -> float:
        cost = 0.0
        
        if action_kind == "sell_material":
            if is_needed_for_upgrade:
                cost += 0.6
                if not has_alternative:
                    cost += 0.3
            else:
                cost += 0.1
                
        elif action_kind == "join_party":
            if is_needed_for_upgrade: # represents conflicting active solo goal
                cost += 0.5
                
        return min(1.0, cost)
