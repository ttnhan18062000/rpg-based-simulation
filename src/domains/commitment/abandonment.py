"""
src/domains/commitment/abandonment.py
───────────────────────────────────────────────────────────────────────────────
AbandonmentEvaluator for Phase 15.
"""

from __future__ import annotations
from typing import Dict, Any

class AbandonmentEvaluator:
    """Evaluates if abandonment constitutes malicious betrayal or valid survival choice."""

    @staticmethod
    def evaluate_abandonment(
        hp: int,
        max_hp: int,
        is_party_in_combat: bool,
        is_greed_driven: bool
    ) -> Dict[str, Any]:
        hp_ratio = hp / max(1, max_hp)
        
        # Valid survival choice
        if hp_ratio < 0.2:
            return {"is_betrayal": False, "penalty": 0.0, "reason": "survival"}
            
        # Betrayal under combat pressure for greedy gains
        if is_party_in_combat and is_greed_driven:
            return {"is_betrayal": True, "penalty": 0.8, "reason": "greedy_desertion"}
            
        # Standard abandon
        return {"is_betrayal": False, "penalty": 0.2, "reason": "voluntary_quit"}
