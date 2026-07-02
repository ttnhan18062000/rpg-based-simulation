"""
src/domains/commitment/abandonment.py
───────────────────────────────────────────────────────────────────────────────
AbandonmentEvaluator for Phase 15.
"""

from __future__ import annotations
from enum import Enum
from dataclasses import dataclass


class AbandonmentCategory(str, Enum):
    SURVIVAL = "survival"
    GREEDY_DESERTION = "greedy_desertion"
    VOLUNTARY_QUIT = "voluntary_quit"


@dataclass(frozen=True)
class AbandonmentClassification:
    is_betrayal: bool
    penalty: float
    category: AbandonmentCategory


class AbandonmentEvaluator:
    """Evaluates if abandonment constitutes malicious betrayal or valid survival choice."""

    @staticmethod
    def evaluate_abandonment(
        hp: int,
        max_hp: int,
        is_party_in_combat: bool,
        is_greed_driven: bool
    ) -> AbandonmentClassification:
        hp_ratio = hp / max(1, max_hp)

        # Valid survival choice
        if hp_ratio < 0.2:
            return AbandonmentClassification(
                is_betrayal=False,
                penalty=0.0,
                category=AbandonmentCategory.SURVIVAL,
            )

        # Betrayal under combat pressure for greedy gains
        if is_party_in_combat and is_greed_driven:
            return AbandonmentClassification(
                is_betrayal=True,
                penalty=0.8,
                category=AbandonmentCategory.GREEDY_DESERTION,
            )

        # Standard abandon
        return AbandonmentClassification(
            is_betrayal=False,
            penalty=0.2,
            category=AbandonmentCategory.VOLUNTARY_QUIT,
        )
