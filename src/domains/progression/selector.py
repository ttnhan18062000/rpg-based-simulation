"""
src/domains/progression/selector.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — ConversionDecisionService

Applies personality scores and context weights to choose the final ConversionOption.
"""

from __future__ import annotations
from typing import Dict, Any, List

from src.core.state import EntityState, AuthoritativeState
from src.domains.progression.schema import ConversionKind, ConversionOption, ProgressionDecisionResult


class ConversionDecisionService:
    """
    Applies personality biases (greed, industry, caution) to score options explainably.
    """

    @staticmethod
    def select(
        entity: EntityState,
        options: tuple[ConversionOption, ...],
        state: AuthoritativeState,
    ) -> ProgressionDecisionResult:
        trace: Dict[str, Any] = {}

        # 1. Fetch personality traits
        identity_comp = getattr(entity, "identity", None)
        pers = getattr(identity_comp, "personality", None)
        
        greed = getattr(pers, "greed", 0.0) or 0.0
        industry = getattr(pers, "industry", 0.0) or 0.0
        caution = getattr(pers, "bravery", 0.0) or 0.0  # Cautious is inverse bravery or industry
        
        # Invert bravery to get caution
        caution_val = 1.0 - caution

        scored_options: List[tuple[ConversionOption, float]] = []

        for opt in options:
            base_score = opt.score
            modifier = 0.0

            # Cautious prefers repair/supplies
            if caution_val > 0.6 and opt.kind in (ConversionKind.REPAIR_GEAR, ConversionKind.BUY_SUPPLY):
                modifier += 0.25 * caution_val
                trace[f"{opt.kind}_personality_bonus"] = "Caution trait favors survival and repairs."

            # Greedy prefers selling loot and saving gold
            elif greed > 0.6:
                if opt.kind in (ConversionKind.SELL_LOOT, ConversionKind.SAVE_FOR_LATER):
                    modifier += 0.4 * greed
                    trace[f"{opt.kind}_personality_bonus"] = "Greed trait favors selling and gold accumulation."
                else:
                    modifier -= 0.3 * greed
                    trace[f"{opt.kind}_personality_penalty"] = "Greed trait disfavors expensive crafting/upgrades."

            # Industrious prefers keeping and crafting materials
            elif industry > 0.6 and opt.kind in (ConversionKind.CRAFT_ITEM, ConversionKind.STORE_ITEM):
                modifier += 0.35 * industry
                trace[f"{opt.kind}_personality_bonus"] = "Industry trait favors active crafting/possession."

            final_score = base_score + modifier
            scored_options.append((opt, final_score))

        # Sort based on final score descending; kind.value as tiebreaker for determinism
        sorted_scored = sorted(scored_options, key=lambda pair: (pair[1], pair[0].kind.value), reverse=True)
        
        selected_option = sorted_scored[0][0] if sorted_scored else None
        
        trace["greed"] = greed
        trace["industry"] = industry
        trace["caution"] = caution_val
        trace["scored_options"] = [(pair[0].kind.value, pair[1]) for pair in sorted_scored]

        return ProgressionDecisionResult(
            entity_id=entity.id,
            selected=(selected_option,) if selected_option else (),
            trace=trace,
            reason=selected_option.reason if selected_option else "No feasible option generated."
        )
