"""
src/domains/progression/generator.py
───────────────────────────────────────────────────────────────────────────────
Phase 6 — ConversionOptionGenerator

Spawns feasible choice options from possession interpretations and active gaps.
"""

from __future__ import annotations
from typing import List, Tuple

from src.core.state import EntityState, AuthoritativeState
from src.domains.progression.schema import ConversionKind, ConversionOption, GrowthGapReport
from src.domains.progression.interpretation import RewardInterpretationReport


class ConversionOptionGenerator:
    """
    Generates alternative conversion routes based on interpretations and gaps.
    """

    @staticmethod
    def generate(
        entity: EntityState,
        interpretation: RewardInterpretationReport,
        gaps: GrowthGapReport,
        state: AuthoritativeState,
    ) -> Tuple[ConversionOption, ...]:
        options: List[ConversionOption] = []

        # 1. Spawn better weapon equip options if equipped weapon is weak
        main_hand_gap = gaps.dominant_gap == "weapon_gap"
        
        # Check meanings in interpretation to spawn EQUIP_ITEM
        for meaning in interpretation.meanings:
            if "equip" in meaning.suggested_conversion_tags:
                options.append(ConversionOption(
                    kind=ConversionKind.EQUIP_ITEM,
                    score=0.95,
                    expected_growth_delta=0.8,
                    reason="Equip direct weapon upgrade from recently acquired items."
                ))

            if "craft" in meaning.suggested_conversion_tags:
                options.append(ConversionOption(
                    kind=ConversionKind.CRAFT_ITEM,
                    score=0.8,
                    expected_growth_delta=0.6,
                    reason="Craft iron_sword using recently acquired materials."
                ))

            if "repair" in meaning.suggested_conversion_tags:
                options.append(ConversionOption(
                    kind=ConversionKind.REPAIR_GEAR,
                    score=0.9,
                    expected_growth_delta=0.7,
                    cost_gold=20,
                    reason="Repair critical equipment durability."
                ))

            if "sell" in meaning.suggested_conversion_tags:
                options.append(ConversionOption(
                    kind=ConversionKind.SELL_LOOT,
                    score=0.7,
                    expected_growth_delta=0.2,
                    reason="Sell junk loot to fund spending routes."
                ))

            if "ask" in meaning.suggested_conversion_tags:
                options.append(ConversionOption(
                    kind=ConversionKind.ASK_ITEM_USE,
                    score=0.75,
                    expected_growth_delta=0.5,
                    reason="Rare ancient fragment found. Inquire for strategic information."
                ))

            if "allocate" in meaning.suggested_conversion_tags:
                options.append(ConversionOption(
                    kind=ConversionKind.ALLOCATE_AP,
                    score=0.85,
                    expected_growth_delta=0.5,
                    reason="Allocate unspent Attribute Points to enhance attributes."
                ))

        # Always add fallback options
        options.append(ConversionOption(
            kind=ConversionKind.SAVE_FOR_LATER,
            score=0.3,
            expected_growth_delta=0.0,
            reason="Do nothing, keep gold and resources for later."
        ))

        # Sort options descending by score; kind.value as tiebreaker for determinism
        sorted_options = sorted(options, key=lambda o: (o.score, o.kind.value), reverse=True)
        return tuple(sorted_options[:10])  # Cap results count at 10
