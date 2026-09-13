"""
src/domains/combat_engagement/learning.py
───────────────────────────────────────────────────────────────────────────────
Phase 4 — CombatLearning

Updates opponent model memory after combat outcomes.
Capacity-limited to prevent memory explosion.
"""

from __future__ import annotations
from typing import Dict, Any, Optional

from src.domains.combat_engagement.schema import OpponentModel
from src.engine.apply import replace


class CombatLearning:
    """
    Saves and updates memory models for seen target opponent kinds or specific entities.
    """

    @staticmethod
    def learn(
        memory: Optional[OpponentModel],
        subject_key: str,
        outcome: str,  # "WON_EASY", "LOST", "FLED", "NEAR_DEATH"
        observed_damage: float,
        observed_skills: tuple[str, ...],
        tick: int = 0,
    ) -> OpponentModel:
        """
        Produce updated OpponentModel based on recent combat results.
        """
        # 1. Base values from previous memory or defaults
        base_power = 20.0
        uncertainty = 0.4
        confidence = 0.5
        known_skills = list(observed_skills)
        outcomes = [outcome]

        if memory:
            base_power = memory.estimated_power
            uncertainty = memory.uncertainty
            confidence = memory.confidence
            known_skills = list(set(list(memory.known_skill_ids) + list(observed_skills)))
            outcomes = list(memory.outcomes) + [outcome]

        # 2. Adjust estimated power based on outcome
        if outcome == "LOST":
            # Target is stronger than expected
            base_power += min(40.0, observed_damage * 0.5)
            confidence = min(0.95, confidence + 0.1)
            uncertainty = max(0.05, uncertainty - 0.1)
        elif outcome == "WON_EASY":
            # Target is weaker than expected
            base_power = max(10.0, base_power - 15.0)
            confidence = min(0.95, confidence + 0.15)
            uncertainty = max(0.05, uncertainty - 0.15)
        elif outcome == "NEAR_DEATH":
            # Very risky target
            base_power += 25.0
            confidence = min(0.95, confidence + 0.2)
            uncertainty = max(0.05, uncertainty - 0.2)
        elif outcome == "FLED":
            # TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER: this outcome value was named in this
            # method's own docstring/type comment (line 26 above) since before this fix, but had no
            # real branch here -- calling learn(outcome="FLED", ...) silently fell through every
            # if/elif with zero numeric correction, appending "FLED" to `outcomes` but leaving
            # base_power/confidence/uncertainty untouched. A real, disclosed defect, fixed in the
            # same change that gives FLED a real caller (docs/mechanics/04_strategic_cognition.md
            # Sec 13.5a: "a weak signal, a small correction only" -- disengaging tells an observer
            # something, but far less than a resolved outcome does).
            confidence = min(0.95, confidence + 0.03)
            uncertainty = max(0.05, uncertainty - 0.03)

        # Bounded outcomes list capacity (keep last 5)
        if len(outcomes) > 5:
            outcomes = outcomes[-5:]

        # Bounded known skills capacity
        if len(known_skills) > 10:
            known_skills = known_skills[:10]

        return OpponentModel(
            subject_key=subject_key,
            estimated_power=round(base_power, 2),
            uncertainty=round(uncertainty, 2),
            confidence=round(confidence, 2),
            known_skill_ids=tuple(known_skills),
            outcomes=tuple(outcomes),
            last_updated_tick=tick,
        )
